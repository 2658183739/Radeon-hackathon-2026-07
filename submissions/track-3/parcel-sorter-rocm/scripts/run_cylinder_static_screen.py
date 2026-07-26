#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import time
import tomllib
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcel_sorter.config import load_config
from parcel_sorter.cylinder_static_screen import (
    screen_cylinder_environment,
    screen_episode_keys,
    summarize_static_screen,
)
from parcel_sorter.genesis_env import GenesisParcelEnv
from parcel_sorter.grasp_scoring import sha256_file
from parcel_sorter.randomization import DomainRandomizer


PROTOCOL_ID = "cylinder-static-ik-collision-screen-v1"


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"expected TOML table: {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sample_sha256(sample: Any) -> str:
    canonical = json.dumps(
        asdict(sample),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _validate_protocol(protocol_path: Path, protocol: dict[str, Any]) -> list[str]:
    errors = []
    if str(protocol["metadata"]["protocol_id"]) != PROTOCOL_ID:
        errors.append("protocol_id")
    try:
        screen_episode_keys(protocol)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"population:{error}")
    implementation = protocol["implementation"]
    for name in (
        "planner",
        "screen_module",
        "runner",
        "genesis_env",
        "grasp_planning",
        "catalog",
        "source_audit",
    ):
        path = PROJECT_ROOT / str(implementation[name])
        expected = str(implementation[f"{name}_sha256"])
        if expected == "PENDING_AFTER_FREEZE":
            errors.append(f"{name}_hash_not_frozen")
        elif sha256_file(path) != expected:
            errors.append(f"{name}_hash_mismatch")
    source_path = PROJECT_ROOT / str(implementation["source_audit"])
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if source.get("status") != "candidate_population_valid":
        errors.append("source_audit_invalid")
    source_contract = source.get("selection_contract", {})
    if (
        bool(source_contract.get("physics_stepped"))
        or bool(source_contract.get("scene_constructed"))
        or bool(source_contract.get("robot_action_executed"))
        or source_contract.get("outcome_fields_read") != []
    ):
        errors.append("source_audit_used_physics_or_outcomes")
    source_keys = {
        (str(row["profile_id"]), int(row["episode"]))
        for row in source.get("samples", ())
    }
    if not set(screen_episode_keys(protocol)) <= source_keys:
        errors.append("screen_population_outside_source_audit")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--backend", choices=("rocm", "cpu"), default="rocm")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    protocol = _load_toml(args.protocol)
    protocol_errors = _validate_protocol(args.protocol, protocol)
    if protocol_errors:
        raise ValueError("invalid static-screen protocol: " + ", ".join(protocol_errors))
    protocol_sha256 = sha256_file(args.protocol)
    implementation = protocol["implementation"]
    config = load_config(PROJECT_ROOT / str(implementation["catalog"]))
    randomizer = DomainRandomizer(
        config.randomization,
        config.seed,
        config.parcel_profiles,
    )
    keys = screen_episode_keys(protocol)
    manifest = {
        "schema_version": "1.0",
        "protocol_id": PROTOCOL_ID,
        "protocol_sha256": protocol_sha256,
        "backend": args.backend,
        "runs": [],
    }
    completed = []
    for profile_id, episode in keys:
        sample = randomizer.sample_profile(profile_id, episode)
        sample_sha256 = _sample_sha256(sample)
        output_path = args.output_dir / "samples" / profile_id / f"{episode}.json"
        if args.resume and output_path.exists():
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            if (
                existing.get("protocol_sha256") == protocol_sha256
                and existing.get("status") == "complete"
                and existing.get("profile_id") == profile_id
                and int(existing.get("episode", -1)) == episode
                and existing.get("sample_sha256") == sample_sha256
            ):
                completed.append(existing)
                manifest["runs"].append(
                    {
                        "profile_id": profile_id,
                        "episode": episode,
                        "status": "complete",
                        "output": str(output_path.resolve()),
                        "resumed": True,
                    }
                )
                _write_json(args.output_dir / "manifest.json", manifest)
                continue

        scene_started = time.perf_counter_ns()
        try:
            with GenesisParcelEnv(
                config,
                sample,
                backend=args.backend,
                defer_initialization_settle=True,
            ) as env:
                scene_build_ms = (time.perf_counter_ns() - scene_started) / 1_000_000
                result = screen_cylinder_environment(env, protocol)
            result.update(
                {
                    "protocol_id": PROTOCOL_ID,
                    "protocol_sha256": protocol_sha256,
                    "backend": args.backend,
                    "sample_sha256": sample_sha256,
                    "scene_build_ms": scene_build_ms,
                }
            )
            _write_json(output_path, result)
            completed.append(result)
            status = "complete"
            error = None
        except Exception as exception:
            status = "failed"
            error = f"{type(exception).__name__}: {exception}"
        manifest["runs"].append(
            {
                "profile_id": profile_id,
                "episode": episode,
                "status": status,
                "output": str(output_path.resolve()),
                "resumed": False,
                "error": error,
            }
        )
        _write_json(args.output_dir / "manifest.json", manifest)
        if error is not None:
            raise RuntimeError(error)

    summary = summarize_static_screen(completed, protocol)
    summary.update(
        {
            "protocol_id": PROTOCOL_ID,
            "protocol_sha256": protocol_sha256,
            "backend": args.backend,
            "implementation_sha256": {
                name: str(implementation[f"{name}_sha256"])
                for name in (
                    "planner",
                    "screen_module",
                    "runner",
                    "genesis_env",
                    "grasp_planning",
                    "catalog",
                    "source_audit",
                )
            },
        }
    )
    _write_json(args.output_dir / "result.json", summary)
    print(
        json.dumps(
            {
                "status": summary["status"],
                "observed_samples": summary["observed_samples"],
                "errors": summary["errors"],
            }
        )
    )
    return 0 if summary["status"] == "screen_pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
