#!/usr/bin/env python3
"""Collect parameterized mobile suction episodes and merge successful shards."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


def _validate_episode(item: dict[str, Any], seen: set[str]) -> None:
    episode_id = str(item.get("episode_id", ""))
    if not episode_id or episode_id in seen:
        raise ValueError(f"episode_id must be non-empty and unique: {episode_id!r}")
    seen.add(episode_id)
    if len(item.get("size_m", ())) != 3 or any(
        not 0.02 <= float(value) <= 0.60 for value in item["size_m"]
    ):
        raise ValueError(f"invalid size_m for {episode_id}")
    if not 0.05 <= float(item.get("mass_kg", 0.0)) <= 5.0:
        raise ValueError(f"invalid mass_kg for {episode_id}")
    if not 0.1 <= float(item.get("friction", 0.0)) <= 2.0:
        raise ValueError(f"invalid friction for {episode_id}")
    if len(item.get("offset_m", ())) != 2 or any(
        abs(float(value)) > 0.025 for value in item["offset_m"]
    ):
        raise ValueError(f"invalid offset_m for {episode_id}")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(path)


def _cli_float(value: Any) -> str:
    """Format physical parameters without exponent syntax confusing argparse."""

    rendered = f"{float(value):.10f}".rstrip("0").rstrip(".")
    return "0" if rendered in {"", "-0"} else rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backend", choices=("rocm", "cuda"), default="rocm")
    parser.add_argument("--max-episodes", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--smolvla-checkpoint", type=Path)
    parser.add_argument(
        "--policy-mode",
        choices=("shadow", "base_residual", "base_arm_residual"),
        default="shadow",
    )
    parser.add_argument("--policy-hz", type=int, default=3)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Concurrent isolated rollout processes; values above one require --audit-only",
    )
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()) and not args.resume:
        parser.error(f"output directory must be new or empty: {args.output}")
    if args.max_episodes is not None and args.max_episodes < 1:
        parser.error("max-episodes must be positive")
    if args.workers < 1:
        parser.error("workers must be positive")
    if args.workers > 1 and not args.audit_only:
        parser.error("parallel workers are supported only for audit-only campaigns")
    if args.policy_mode != "shadow" and args.smolvla_checkpoint is None:
        parser.error("base_residual mode requires --smolvla-checkpoint")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    episodes = list(config.get("episodes", ()))
    if args.max_episodes is not None:
        episodes = episodes[: args.max_episodes]
    if not episodes:
        parser.error("collection config contains no episodes")
    seen: set[str] = set()
    for item in episodes:
        _validate_episode(item, seen)
    seen_order = {
        str(item["episode_id"]): index for index, item in enumerate(episodes)
    }

    root = Path(__file__).resolve().parent.parent
    args.output.mkdir(parents=True, exist_ok=True)
    existing_results: dict[str, dict[str, Any]] = {}
    existing_summary_path = args.output / "collection-summary.json"
    if args.resume and existing_summary_path.is_file():
        existing = json.loads(existing_summary_path.read_text(encoding="utf-8"))
        existing_results = {
            str(item["episode_id"]): item for item in existing.get("results", ())
        }
    results = []
    successful_roots = []
    pending = []
    for item in episodes:
        episode_id = str(item["episode_id"])
        shard = args.output / "shards" / episode_id
        dataset_root = shard / "lerobot_dataset"
        retained = existing_results.get(episode_id)
        if retained is not None:
            summary_path = Path(str(retained.get("summary", "")))
            retained_complete = bool(
                summary_path.is_file()
                and (
                    args.audit_only
                    or not retained.get("success")
                    or dataset_root.is_dir()
                )
            )
            if retained_complete:
                if retained.get("success") and not args.audit_only:
                    successful_roots.append(dataset_root.resolve())
                results.append(retained)
                continue
        pending.append(item)

    def collect_one(item: dict[str, Any]) -> dict[str, Any]:
        episode_id = str(item["episode_id"])
        shard = args.output / "shards" / episode_id
        dataset_root = shard / "lerobot_dataset"
        command = [
            sys.executable,
            str(root / "scripts/evaluate_mobile_suction_lift_rocm.py"),
            "--backend",
            args.backend,
            "--output",
            str(shard / "run"),
            "--parcel-profile",
            str(item["profile"]),
            "--parcel-size-m",
            *(_cli_float(value) for value in item["size_m"]),
            "--parcel-mass-kg",
            _cli_float(item["mass_kg"]),
            "--parcel-friction",
            _cli_float(item["friction"]),
            "--parcel-offset-m",
            *(_cli_float(value) for value in item["offset_m"]),
        ]
        if not args.audit_only:
            command.extend(("--record-dataset", str(dataset_root)))
        if args.smolvla_checkpoint is not None:
            command.extend(
                (
                    "--smolvla-checkpoint",
                    str(args.smolvla_checkpoint),
                    "--policy-mode",
                    args.policy_mode,
                    "--policy-hz",
                    str(args.policy_hz),
                )
            )
        if item.get("task_text"):
            command.extend(("--task-text", str(item["task_text"])))
        shard.mkdir(parents=True, exist_ok=True)
        log_path = shard / "collector.log"
        with log_path.open("w", encoding="utf-8") as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        summary_path = shard / "run/summary.json"
        summary = (
            json.loads(summary_path.read_text(encoding="utf-8"))
            if summary_path.is_file()
            else {}
        )
        success = bool(completed.returncode == 0 and summary.get("success"))
        return {
            "episode_id": episode_id,
            "profile": item["profile"],
            "parameters": item,
            "return_code": completed.returncode,
            "success": success,
            "failure_stage": next(
                (
                    name
                    for name in (
                        "lift_success",
                        "transport_success",
                        "placed_before_release",
                        "released",
                    )
                    if not summary.get(name, False)
                ),
                None,
            ),
            "placement_error_m": summary.get("placement_error_m"),
            "max_suction_force_n": summary.get("suction", {}).get(
                "max_suction_force_n"
            ),
            "max_contact_force_n": summary.get("suction", {}).get(
                "max_contact_force_n"
            ),
            "frames": summary.get("dataset", {}).get("frames", 0),
            "summary": str(summary_path.resolve()),
            "log": str(log_path.resolve()),
        }

    if args.workers == 1:
        collected = map(collect_one, pending)
    else:
        executor = ThreadPoolExecutor(max_workers=args.workers)
        collected = executor.map(collect_one, pending)
    try:
        for result in collected:
            results.append(result)
            if result["success"] and not args.audit_only:
                successful_roots.append(
                    (args.output / "shards" / result["episode_id"] / "lerobot_dataset").resolve()
                )
            results.sort(key=lambda result: seen_order[str(result["episode_id"])])
            _write_json(
                args.output / "collection-summary.json",
                {
                    "schema_version": 1,
                    "collection_id": config.get("collection_id"),
                    "requested_episodes": len(episodes),
                    "completed_episodes": len(results),
                    "successful_episodes": sum(
                        bool(result.get("success")) for result in results
                    ),
                    "results": results,
                    "status": "collecting",
                },
            )
    finally:
        if args.workers > 1:
            executor.shutdown(wait=True)

    merged_root = args.output / "lerobot_dataset"
    merge_error = None
    if successful_roots and not args.audit_only:
        if merged_root.exists():
            if not args.resume:
                raise RuntimeError(f"merged dataset already exists: {merged_root}")
            # The merged dataset is derived; source shards remain immutable and auditable.
            shutil.rmtree(merged_root)
        editor = shutil.which("lerobot-edit-dataset")
        if editor is None:
            adjacent_editor = Path(sys.executable).parent / "lerobot-edit-dataset"
            editor = str(adjacent_editor) if adjacent_editor.is_file() else None
        if editor is None:
            raise RuntimeError("lerobot-edit-dataset is required to merge episode shards")
        repo_ids = ["local/mobile-bimanual-parcel-expert"] * len(successful_roots)
        merge_command = [
            editor,
            "--operation.type",
            "merge",
            "--operation.repo_ids",
            json.dumps(repo_ids),
            "--operation.roots",
            json.dumps([str(path) for path in successful_roots]),
            "--operation.concatenate_videos",
            "false",
            "--operation.concatenate_data",
            "false",
            "--new_repo_id",
            "local/mobile-bimanual-parcel-multiprofile",
            "--new_root",
            str(merged_root),
            "--push_to_hub",
            "false",
        ]
        merge_log = args.output / "merge.log"
        with merge_log.open("w", encoding="utf-8") as log:
            merged = subprocess.run(merge_command, stdout=log, stderr=subprocess.STDOUT)
        if merged.returncode != 0:
            merge_error = f"dataset merge failed with exit code {merged.returncode}"

    successful_count = sum(bool(result.get("success")) for result in results)
    status = (
        "completed_audit_only"
        if args.audit_only and len(results) == len(episodes)
        else
        "passed"
        if len(successful_roots) >= 2 and merge_error is None and merged_root.is_dir()
        else "insufficient_successes"
        if len(successful_roots) < 2
        else "merge_failed"
    )
    payload = {
        "schema_version": 1,
        "collection_id": config.get("collection_id"),
        "config": str(args.config.resolve()),
        "requested_episodes": len(episodes),
        "completed_episodes": len(results),
        "successful_episodes": successful_count,
        "failed_episodes": len(results) - successful_count,
        "merged_dataset_root": str(merged_root.resolve()) if merged_root.is_dir() else None,
        "merge_error": merge_error,
        "results": results,
        "status": status,
        "claim_boundary": (
            "audit-only campaign; no episode is written to or merged into training data"
            if args.audit_only
            else "successful expert episodes are merged for training; failed runs remain audit-only"
        ),
    }
    _write_json(args.output / "collection-summary.json", payload)
    print(json.dumps(payload))
    return 0 if status in {"passed", "completed_audit_only"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
