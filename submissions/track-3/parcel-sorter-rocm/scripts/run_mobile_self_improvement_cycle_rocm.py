#!/usr/bin/env python3
"""Run one resumable, fail-closed mobile SmolVLA improvement cycle on Radeon."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcel_sorter.mobile_self_improvement_cycle import (
    build_curriculum_config,
    build_frozen_holdout_config,
    build_replay_from_campaign_audit,
    promotion_gate,
    sha256_file,
    validate_split_isolation,
    write_json,
)


STEP_ORDER = (
    "preflight",
    "collect_curriculum",
    "audit_curriculum",
    "train_candidate",
    "offline_ablation",
    "evaluate_baseline",
    "summarize_baseline",
    "evaluate_candidate",
    "summarize_candidate",
    "promotion_gate",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle-id", default="v3")
    parser.add_argument("--cycle-dir", type=Path, required=True)
    parser.add_argument("--source-campaign-audit", type=Path, required=True)
    parser.add_argument("--base-training-config", type=Path, required=True)
    parser.add_argument("--baseline-checkpoint", type=Path, required=True)
    parser.add_argument("--holdout-trials", type=int, default=100)
    parser.add_argument("--holdout-seed", type=int, default=20260728)
    parser.add_argument("--training-steps", type=int, default=2800)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--policy-hz", type=int, default=3)
    parser.add_argument("--evaluation-workers", type=int, default=4)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stop-after", choices=STEP_ORDER)
    args = parser.parse_args()
    if args.training_steps < 1 or min(
        args.batch_size, args.policy_hz, args.evaluation_workers
    ) < 1:
        parser.error(
            "training steps, batch size, policy Hz, and evaluation workers must be positive"
        )
    if args.num_workers < 0:
        parser.error("num-workers cannot be negative")

    root = PROJECT_ROOT
    cycle_dir = args.cycle_dir.resolve()
    state_path = cycle_dir / "cycle-state.json"
    if cycle_dir.exists() and any(cycle_dir.iterdir()) and not args.resume:
        parser.error(f"cycle directory must be new or --resume must be used: {cycle_dir}")
    cycle_dir.mkdir(parents=True, exist_ok=True)

    source_audit = _read_json(args.source_campaign_audit)
    base_training = _read_json(args.base_training_config)
    replay = build_replay_from_campaign_audit(source_audit)
    curriculum = build_curriculum_config(base_training, replay, cycle_id=args.cycle_id)
    holdout = build_frozen_holdout_config(
        cycle_id=args.cycle_id, trials=args.holdout_trials, seed=args.holdout_seed
    )
    isolation = validate_split_isolation(curriculum, holdout)
    replay_path = cycle_dir / "failure-replay.json"
    curriculum_path = cycle_dir / "curriculum-config.json"
    holdout_path = cycle_dir / "frozen-holdout.json"
    isolation_path = cycle_dir / "split-isolation-audit.json"
    for path, payload in (
        (replay_path, replay),
        (curriculum_path, curriculum),
        (holdout_path, holdout),
        (isolation_path, isolation),
    ):
        _freeze_prepared_artifact(path, payload, resume=args.resume)

    training_dir = cycle_dir / "curriculum-collection"
    candidate_dir = cycle_dir / "candidate-training"
    candidate_checkpoint = (
        candidate_dir / "checkpoints" / f"{args.training_steps:06d}" / "pretrained_model"
    )
    baseline_rollouts = cycle_dir / "baseline-holdout"
    candidate_rollouts = cycle_dir / "candidate-holdout"
    commands = {
        "preflight": ["bash", str(root / "scripts/preflight_radeon.sh")],
        "collect_curriculum": [
            sys.executable,
            str(root / "scripts/collect_mobile_suction_dataset_rocm.py"),
            "--config", str(curriculum_path), "--output", str(training_dir),
            "--backend", "rocm", "--resume",
        ],
        "audit_curriculum": [
            sys.executable,
            str(root / "scripts/audit_mobile_dataset.py"),
            "--dataset-root", str(training_dir / "lerobot_dataset"),
            "--output", str(cycle_dir / "curriculum-dataset-audit.json"),
            "--min-episodes", str(len(curriculum["episodes"])),
        ],
        "train_candidate": [
            "bash", str(root / "scripts/train_mobile_smolvla_rocm.sh"),
            str(training_dir / "lerobot_dataset"), str(candidate_dir),
        ],
        "offline_ablation": [
            sys.executable,
            str(root / "scripts/smoke_mobile_smolvla_inference_rocm.py"),
            "--checkpoint", str(candidate_checkpoint),
            "--dataset-root", str(training_dir / "lerobot_dataset"),
            "--output", str(cycle_dir / "candidate-offline-ablation.json"),
        ],
        "evaluate_baseline": _campaign_command(
            root,
            holdout_path,
            baseline_rollouts,
            args.baseline_checkpoint.resolve(),
            args.policy_hz,
            args.evaluation_workers,
        ),
        "summarize_baseline": _summary_command(
            root, baseline_rollouts, cycle_dir / "baseline-holdout-audit.json"
        ),
        "evaluate_candidate": _campaign_command(
            root,
            holdout_path,
            candidate_rollouts,
            candidate_checkpoint,
            args.policy_hz,
            args.evaluation_workers,
        ),
        "summarize_candidate": _summary_command(
            root, candidate_rollouts, cycle_dir / "candidate-holdout-audit.json"
        ),
    }
    state = _load_state(state_path, args, replay_path, curriculum_path, holdout_path, commands)
    if args.dry_run:
        state["status"] = "dry_run"
        write_json(state_path, state)
        print(json.dumps(state, indent=2))
        return 0

    env = os.environ.copy()
    env.update(
        {
            "HIP_VISIBLE_DEVICES": env.get("HIP_VISIBLE_DEVICES", "0"),
            "MOBILE_SMOLVLA_STEPS": str(args.training_steps),
            "MOBILE_SMOLVLA_BATCH_SIZE": str(args.batch_size),
            "MOBILE_SMOLVLA_NUM_WORKERS": str(args.num_workers),
            "PARCEL_SORTER_VENV": sys.prefix,
        }
    )
    env["PATH"] = f"{Path(sys.prefix) / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    env["PYTHONPATH"] = (
        f"{root / 'src'}{os.pathsep}{env['PYTHONPATH']}"
        if env.get("PYTHONPATH")
        else str(root / "src")
    )
    for step in STEP_ORDER:
        if step == "promotion_gate":
            _run_promotion_gate(cycle_dir, candidate_checkpoint, state, state_path)
        elif state["steps"].get(step, {}).get("status") == "passed":
            continue
        else:
            _run_command(step, commands[step], cycle_dir, state, state_path, env)
        if args.stop_after == step:
            state["status"] = "stopped_after_requested_step"
            write_json(state_path, state)
            return 0
    state["status"] = (
        "completed_promoted"
        if state["steps"]["promotion_gate"]["status"] == "passed"
        else "completed_not_promoted"
    )
    write_json(state_path, state)
    return 0


def _campaign_command(
    root: Path,
    holdout: Path,
    output: Path,
    checkpoint: Path,
    policy_hz: int,
    workers: int,
) -> list[str]:
    return [
        sys.executable,
        str(root / "scripts/collect_mobile_suction_dataset_rocm.py"),
        "--config", str(holdout), "--output", str(output), "--backend", "rocm",
        "--resume", "--audit-only", "--smolvla-checkpoint", str(checkpoint),
        "--policy-mode", "base_residual", "--policy-hz", str(policy_hz),
        "--workers", str(workers),
    ]


def _summary_command(root: Path, rollouts: Path, output: Path) -> list[str]:
    return [
        sys.executable,
        str(root / "scripts/summarize_mobile_vla_campaign.py"),
        "--collection-summary", str(rollouts / "collection-summary.json"),
        "--output", str(output),
    ]


def _load_state(
    path: Path,
    args: argparse.Namespace,
    replay: Path,
    curriculum: Path,
    holdout: Path,
    commands: dict[str, list[str]],
) -> dict[str, Any]:
    if args.resume and path.is_file():
        state = _read_json(path)
        if state.get("inputs", {}).get("holdout_sha256") != sha256_file(holdout):
            raise RuntimeError("resume rejected: frozen holdout hash changed")
        state["commands"] = commands
        state.setdefault("settings", {})["evaluation_workers"] = args.evaluation_workers
        return state
    return {
        "schema_version": 1,
        "protocol": "mobile-smolvla-self-improvement-cycle-v1",
        "cycle_id": args.cycle_id,
        "status": "prepared",
        "inputs": {
            "source_campaign_audit": str(args.source_campaign_audit.resolve()),
            "source_campaign_audit_sha256": sha256_file(args.source_campaign_audit),
            "base_training_config": str(args.base_training_config.resolve()),
            "base_training_config_sha256": sha256_file(args.base_training_config),
            "baseline_checkpoint": str(args.baseline_checkpoint.resolve()),
            "replay_sha256": sha256_file(replay),
            "curriculum_sha256": sha256_file(curriculum),
            "holdout_sha256": sha256_file(holdout),
        },
        "settings": {
            "holdout_trials": args.holdout_trials,
            "holdout_seed": args.holdout_seed,
            "training_steps": args.training_steps,
            "batch_size": args.batch_size,
            "num_workers": args.num_workers,
            "policy_hz": args.policy_hz,
            "evaluation_workers": args.evaluation_workers,
        },
        "commands": commands,
        "steps": {},
        "claim_boundary": (
            "nearline improvement between episodes; no active rollout mutates model weights"
        ),
    }


def _run_command(
    name: str,
    command: list[str],
    cycle_dir: Path,
    state: dict[str, Any],
    state_path: Path,
    env: dict[str, str],
) -> None:
    log_path = cycle_dir / "logs" / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    state["status"] = "running"
    state["steps"][name] = {"status": "running", "log": str(log_path), "command": command}
    write_json(state_path, state)
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
    state["steps"][name]["return_code"] = completed.returncode
    state["steps"][name]["status"] = "passed" if completed.returncode == 0 else "failed"
    write_json(state_path, state)
    if completed.returncode != 0:
        raise RuntimeError(f"cycle step failed: {name}; inspect {log_path}")


def _run_promotion_gate(
    cycle_dir: Path, checkpoint: Path, state: dict[str, Any], state_path: Path
) -> None:
    baseline = _read_json(cycle_dir / "baseline-holdout-audit.json")
    candidate = _read_json(cycle_dir / "candidate-holdout-audit.json")
    result = promotion_gate(baseline, candidate)
    result["candidate_checkpoint"] = str(checkpoint)
    result_path = cycle_dir / "promotion-gate.json"
    write_json(result_path, result)
    if result["promoted"]:
        write_json(
            cycle_dir / "promoted-checkpoint.json",
            {
                "checkpoint": str(checkpoint),
                "promotion_gate": str(result_path),
                "promotion_gate_sha256": sha256_file(result_path),
            },
        )
    state["steps"]["promotion_gate"] = {
        "status": "passed" if result["promoted"] else "rejected",
        "result": str(result_path),
    }
    write_json(state_path, state)


def _freeze_prepared_artifact(
    path: Path, payload: dict[str, Any], *, resume: bool
) -> None:
    if resume and path.is_file():
        if _read_json(path) != payload:
            raise RuntimeError(f"resume rejected: prepared artifact changed: {path}")
        return
    write_json(path, payload)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
