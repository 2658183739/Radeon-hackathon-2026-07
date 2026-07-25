#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcel_sorter.grasp_scoring import load_grasp_split_protocol, sha256_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a frozen grasp-candidate collection split in isolated processes."
    )
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/catalog_v2.toml")
    parser.add_argument("--backend", choices=("cpu", "rocm"), default="rocm")
    parser.add_argument("--max-candidates", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--unlock-holdout",
        action="store_true",
        help="required to execute the frozen holdout split",
    )
    return parser.parse_args()


def planned_runs(
    protocol: Path,
    split: str,
    output_dir: Path,
) -> list[dict[str, Any]]:
    assignments = load_grasp_split_protocol(protocol)
    rows = [
        {
            "profile": profile,
            "episode": episode,
            "split": assigned_split,
            "output": str(output_dir / split / profile / f"{episode}.json"),
        }
        for (profile, episode), assigned_split in assignments.items()
        if assigned_split == split
    ]
    if not rows:
        raise ValueError(f"protocol contains no assignments for split {split}")
    return sorted(rows, key=lambda row: (str(row["profile"]), int(row["episode"])))


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run(args: argparse.Namespace) -> dict[str, Any]:
    if min(args.max_candidates, args.repeats) < 1:
        raise ValueError("candidate and repeat budgets must be positive")
    if args.split == "holdout" and not args.unlock_holdout:
        raise PermissionError(
            "holdout collection is locked; pass --unlock-holdout only after model selection"
        )
    protocol = args.protocol.resolve()
    output_dir = args.output_dir.resolve()
    rows = planned_runs(protocol, args.split, output_dir)
    manifest_path = output_dir / args.split / "manifest.json"
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "protocol": str(protocol),
        "protocol_sha256": sha256_file(protocol),
        "split": args.split,
        "backend": args.backend,
        "max_candidates": args.max_candidates,
        "repeats": args.repeats,
        "dry_run": args.dry_run,
        "planned_episode_count": len(rows),
        "planned_max_rollouts": len(rows) * args.max_candidates * args.repeats,
        "runs": [],
    }
    labeler = PROJECT_ROOT / "scripts/diagnose_counterfactual_grasp_candidates.py"
    for row in rows:
        output = Path(str(row["output"]))
        command = [
            sys.executable,
            str(labeler),
            "--config",
            str(args.config.resolve()),
            "--profile",
            str(row["profile"]),
            "--episode",
            str(row["episode"]),
            "--backend",
            args.backend,
            "--all-candidates",
            "--max-candidates",
            str(args.max_candidates),
            "--repeats",
            str(args.repeats),
            "--output",
            str(output),
        ]
        record = {**row, "command": command, "status": "planned"}
        manifest["runs"].append(record)
        if args.dry_run:
            continue
        if output.exists():
            if not args.resume:
                raise FileExistsError(
                    f"collection output already exists: {output}; pass --resume to audit and skip"
                )
            payload = json.loads(output.read_text(encoding="utf-8"))
            if (
                str(payload["profile"]) != str(row["profile"])
                or int(payload["episode"]) != int(row["episode"])
            ):
                raise ValueError(f"existing output does not match frozen run: {output}")
            record.update({"status": "reused", "sha256": sha256_file(output)})
            _write_manifest(manifest_path, manifest)
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        record["status"] = "running"
        _write_manifest(manifest_path, manifest)
        try:
            subprocess.run(command, cwd=PROJECT_ROOT, check=True)
        except BaseException:
            record["status"] = "failed"
            _write_manifest(manifest_path, manifest)
            raise
        record.update({"status": "complete", "sha256": sha256_file(output)})
        _write_manifest(manifest_path, manifest)
    if args.dry_run:
        return manifest
    manifest["complete_episode_count"] = sum(
        row["status"] in {"complete", "reused"} for row in manifest["runs"]
    )
    _write_manifest(manifest_path, manifest)
    return manifest


def main() -> int:
    args = parse_args()
    payload = run(args)
    print(
        json.dumps(
            {
                "split": payload["split"],
                "dry_run": payload["dry_run"],
                "planned_episode_count": payload["planned_episode_count"],
                "planned_max_rollouts": payload["planned_max_rollouts"],
                "manifest": str(args.output_dir.resolve() / args.split / "manifest.json"),
                "runs": payload["runs"] if args.dry_run else None,
            },
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
