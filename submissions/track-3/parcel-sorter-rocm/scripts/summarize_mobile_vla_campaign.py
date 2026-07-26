#!/usr/bin/env python3
"""Create a compact, hash-linked audit of a mobile VLA campaign."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

from parcel_sorter.metrics import wilson_interval


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    collection = json.loads(args.collection_summary.read_text(encoding="utf-8"))
    compact_runs: list[dict[str, Any]] = []
    errors = []
    for result in collection.get("results", ()):
        summary_path = Path(str(result.get("summary", "")))
        if not summary_path.is_file():
            errors.append(f"missing_summary:{result.get('episode_id')}")
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        runtime = summary.get("runtime") or {}
        policy = summary.get("policy") or {}
        compact_runs.append(
            {
                "episode_id": result.get("episode_id"),
                "profile": result.get("profile"),
                "parameters": result.get("parameters"),
                "success": bool(summary.get("success")),
                "failure_stage": result.get("failure_stage"),
                "placement_error_m": summary.get("placement_error_m"),
                "lift_delta_m": summary.get("lift_delta_m"),
                "suction": summary.get("suction"),
                "policy": {key: value for key, value in policy.items() if key != "trace"},
                "runtime": {
                    "torch": runtime.get("torch"),
                    "rocm": runtime.get("rocm"),
                    "cuda": runtime.get("cuda"),
                    "gpu_count": runtime.get("gpu_count"),
                    "gpu_name": runtime.get("gpu_name"),
                },
                "source_summary": str(summary_path.resolve()),
                "source_summary_sha256": _sha256(summary_path),
            }
        )

    successes = sum(bool(run["success"]) for run in compact_runs)
    trials = len(compact_runs)
    wilson_low, wilson_high = wilson_interval(successes, trials)
    successful_errors = [
        float(run["placement_error_m"])
        for run in compact_runs
        if run["success"] and run["placement_error_m"] is not None
    ]
    payload = {
        "schema_version": 1,
        "protocol": "mobile-vla-campaign-audit-v1",
        "status": "passed" if not errors and trials == int(collection["requested_episodes"]) else "failed",
        "errors": errors,
        "collection_summary": str(args.collection_summary.resolve()),
        "collection_summary_sha256": _sha256(args.collection_summary),
        "audit_only": collection.get("merged_dataset_root") is None,
        "successes": successes,
        "trials": trials,
        "success_rate": successes / trials if trials else 0.0,
        "wilson_95": [wilson_low, wilson_high],
        "mean_success_placement_error_m": (
            statistics.fmean(successful_errors) if successful_errors else None
        ),
        "force_violation_count": sum(
            float((run.get("suction") or {}).get("max_contact_force_n") or 0.0) >= 35.0
            for run in compact_runs
        ),
        "vla_actuated_run_count": sum(
            int((run.get("policy") or {}).get("applied_physics_steps") or 0) > 0
            for run in compact_runs
        ),
        "single_radeon_rocm_run_count": sum(
            (run.get("runtime") or {}).get("gpu_count") == 1
            and (run.get("runtime") or {}).get("cuda") is None
            and bool((run.get("runtime") or {}).get("rocm"))
            for run in compact_runs
        ),
        "runs": compact_runs,
        "claim_boundary": (
            "frozen small-sample holdout gate; not the planned 100-episode final campaign"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if payload["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
