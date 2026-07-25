#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from parcel_sorter.config import load_config
from parcel_sorter.genesis_env import GenesisParcelEnv
from parcel_sorter.grasp_planning import (
    generate_box_grasp_pose_candidates,
    grasp_evaluation_is_feasible,
    rank_grasp_pose_evaluations,
)
from parcel_sorter.grasp_stability import full_episode_grasp_rank_key
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.runner import run_expert_episode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run controller-faithful closed-loop counterfactuals while forcing "
            "one statically feasible grasp candidate. This is diagnostic only."
        )
    )
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/catalog_v2.toml")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--episode", type=int, required=True)
    parser.add_argument("--backend", choices=("cpu", "rocm"), default="rocm")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--all-candidates", action="store_true")
    parser.add_argument("--max-candidates", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument(
        "--inactive-gate",
        choices=("error", "skip"),
        default="error",
        help="fail or emit a structured skip when the formal reset gate is inactive",
    )
    return parser.parse_args()


def _static_candidate_rows(
    env: GenesisParcelEnv,
) -> tuple[list[dict[str, Any]], set[str]]:
    state = env.state()
    candidates = generate_box_grasp_pose_candidates(
        env.sample,
        state.parcel_pose,
        hand_clearance_m=env.expert.grasp_hand_clearance_m(),
    )
    evaluations = [
        env._evaluate_grasp_pose_candidate(candidate, seed_name, seed_qpos)
        for candidate in candidates
        for seed_name, seed_qpos in env._grasp_planning_seeds()
    ]
    ranked = rank_grasp_pose_evaluations(evaluations)
    unique_feasible: list[dict[str, Any]] = []
    seen: set[str] = set()
    for static_rank, evaluation in enumerate(ranked):
        candidate_id = str(evaluation["candidate_id"])
        if candidate_id in seen or not grasp_evaluation_is_feasible(evaluation):
            continue
        row = dict(evaluation)
        row["static_rank"] = static_rank
        unique_feasible.append(row)
        seen.add(candidate_id)
    return unique_feasible, {candidate.candidate_id for candidate in candidates}


def _compact_static_row(evaluation: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "candidate_id",
        "seed_name",
        "static_rank",
        "target_position",
        "target_quaternion",
        "longitudinal_offset_m",
        "vertical_offset_m",
        "wrist_variant",
        "minimum_singular_value",
        "joint_distance_rad",
        "nonfinger_clearance_m",
        "disallowed_collision_count",
    )
    return {key: evaluation[key] for key in keys}


def _selected_candidate_id(safety_summary: Mapping[str, Any]) -> str | None:
    for event in safety_summary.get("grasp_plan_events", ()):
        selected = event.get("selected")
        if selected is not None:
            return str(selected["candidate_id"])
    return None


def _first_force_abort_frame(
    trace: tuple[dict[str, Any], ...],
    threshold_n: float,
) -> int | None:
    return next(
        (
            int(row["frame"])
            for row in trace
            if float(row["contact_force_n"]) > threshold_n
        ),
        None,
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.episode < 0 or min(args.max_candidates, args.repeats) < 1:
        raise ValueError("episode must be non-negative and budgets must be positive")
    if args.all_candidates == bool(args.candidate_id):
        raise ValueError("choose exactly one of --all-candidates or --candidate-id")

    config = load_config(args.config)
    config = replace(
        config,
        task=replace(
            config.task,
            max_grasp_retries=0,
            geometry_aware_grasp_planning_enabled=True,
            grasp_planning_reset_fallback_gate_enabled=True,
            grasp_planning_transport_contract_enabled=True,
            grasp_planning_transport_lookahead_enabled=False,
        ),
        control=replace(
            config.control,
            collision_checked_reset_enabled=True,
            transport_slip_recovery_enabled=False,
            transport_slip_setdown_regrasp_enabled=False,
        ),
    )
    config.validate()
    randomizer = DomainRandomizer(config.randomization, config.seed, config.parcel_profiles)
    sample = randomizer.sample_profile(args.profile, args.episode)
    started = time.perf_counter_ns()

    with GenesisParcelEnv(config, sample, backend=args.backend) as discovery_env:
        feasible, all_candidate_ids = _static_candidate_rows(discovery_env)
        planner_active = discovery_env.geometry_grasp_planning_active
    feasible_by_id = {str(row["candidate_id"]): row for row in feasible}
    if args.all_candidates:
        selected_ids = list(feasible_by_id)[: args.max_candidates]
    else:
        selected_ids = [str(candidate_id) for candidate_id in args.candidate_id]
    missing = sorted(set(selected_ids) - set(feasible_by_id))
    if missing:
        raise ValueError("requested candidates are not statically feasible: " + ", ".join(missing))
    if not planner_active:
        if args.inactive_gate == "error":
            raise RuntimeError("reset-fallback gate did not activate geometry planning")
        return {
            "schema_version": 1,
            "status": "skipped_inactive_reset_gate",
            "backend": args.backend,
            "config": str(args.config.resolve()),
            "episode": args.episode,
            "profile": args.profile,
            "sample": asdict(sample),
            "contract": {
                "controller_faithful": True,
                "fresh_scene_per_rollout": True,
                "collision_checked_reset_enabled": True,
                "reset_fallback_gate_enabled": True,
                "reset_fallback_gate_satisfied": False,
                "labels_generated": False,
                "reason": "geometry planning is not active in the formal controller",
            },
            "static_feasible_candidates": [
                _compact_static_row(row) for row in feasible
            ],
            "tested_candidate_ids": [],
            "repeat_count": args.repeats,
            "ranked_rollouts": [],
            "rollouts": [],
            "compute_ms": (time.perf_counter_ns() - started) / 1_000_000,
        }

    rollouts: list[dict[str, Any]] = []
    for candidate_id in selected_ids:
        static_row = feasible_by_id[candidate_id]
        for repeat in range(args.repeats):
            with GenesisParcelEnv(config, sample, backend=args.backend) as env:
                env.set_diagnostic_grasp_candidate_allowlist(
                    frozenset({candidate_id})
                )
                report = run_expert_episode(
                    env,
                    config,
                    sample,
                    args.episode,
                )
            selected = _selected_candidate_id(report.safety_summary)
            if selected != candidate_id:
                raise RuntimeError(
                    f"forced candidate mismatch: requested {candidate_id}, selected {selected}"
                )
            result = report.result
            force_abort_frame = _first_force_abort_frame(
                report.trace,
                config.task.max_contact_force_n,
            )
            rollouts.append(
                {
                    "candidate_id": candidate_id,
                    "repeat": repeat,
                    "static_rank": int(static_row["static_rank"]),
                    "success": result.success,
                    "safety_aborted": force_abort_frame is not None,
                    "force_abort_frame": force_abort_frame,
                    "dropped": result.dropped,
                    "max_contact_force_n": result.max_contact_force_n,
                    "duration_seconds": result.duration_seconds,
                    "terminal_stage": report.terminal_stage,
                    "selected_candidate_id": selected,
                    "planner_attempts": report.safety_summary["grasp_plan_attempts"],
                    "transport_final_phase": report.safety_summary[
                        "grasp_planning_transport_final_phase"
                    ],
                    "report": report.to_dict(),
                }
            )

    ranked = sorted(rollouts, key=full_episode_grasp_rank_key)
    return {
        "schema_version": 1,
        "status": "complete",
        "backend": args.backend,
        "config": str(args.config.resolve()),
        "episode": args.episode,
        "profile": args.profile,
        "sample": asdict(sample),
        "contract": {
            "controller_faithful": True,
            "fresh_scene_per_rollout": True,
            "collision_checked_reset_enabled": True,
            "reset_fallback_gate_enabled": True,
            "transport_contract_enabled": True,
            "transport_lookahead_enabled": False,
            "max_grasp_retries": 0,
            "force_abort_n": config.task.max_contact_force_n,
            "only_intervention": "reject every generated candidate ID except the target",
        },
        "static_feasible_candidates": [
            _compact_static_row(row) for row in feasible
        ],
        "tested_candidate_ids": selected_ids,
        "repeat_count": args.repeats,
        "ranked_rollouts": [
            {key: value for key, value in row.items() if key != "report"}
            for row in ranked
        ],
        "rollouts": rollouts,
        "compute_ms": (time.perf_counter_ns() - started) / 1_000_000,
    }


def main() -> int:
    args = parse_args()
    payload = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": payload["status"],
                "episode": payload["episode"],
                "tested_candidate_ids": payload["tested_candidate_ids"],
                "ranked_rollouts": payload["ranked_rollouts"],
                "compute_ms": payload["compute_ms"],
            },
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
