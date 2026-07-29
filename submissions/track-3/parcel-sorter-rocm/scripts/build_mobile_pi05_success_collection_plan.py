#!/usr/bin/env python3
"""Build a deterministic, diversity-balanced parcel demonstration plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
from typing import Any, Callable


GRASP_MODES = ("top_suction", "side_suction", "cooperative_cradle")


def _stratified(count: int, rng: random.Random) -> list[float]:
    values = [(index + rng.random()) / count for index in range(count)]
    rng.shuffle(values)
    return values


def _lerp(low: float, high: float, fraction: float) -> float:
    return round(low + (high - low) * fraction, 10)


def _dimensions(count: int, rng: random.Random, dimensions: int) -> list[list[float]]:
    return [_stratified(count, rng) for _ in range(dimensions)]


def _top_suction(
    index: int, count: int, fractions: list[list[float]]
) -> dict[str, Any]:
    use_mailer = index % 2 == 1
    if use_mailer:
        profile = "flat_mailer"
        size_ranges = ((0.125, 0.145), (0.040, 0.047), (0.015, 0.021))
        mass_range = (0.07, 0.14)
        recovery_x_range = (0.002, 0.004)
        recovery_y_range = (-0.004, -0.002)
    else:
        profile = "micro_box"
        size_ranges = ((0.060, 0.070), (0.035, 0.040), (0.026, 0.032))
        mass_range = (0.06, 0.10)
        recovery_x_range = (-0.001, 0.001)
        recovery_y_range = (0.005, 0.007)
    return {
        "profile": profile,
        "shape": "box",
        "orientation_mode": "yaw",
        "yaw_rad": _lerp(-0.12, 0.12, fractions[0][index]),
        "handling_class": "parallel_jaw",
        "grasp_mode": "top_suction",
        "minimum_sealed_cups": 1,
        "cooperative_cradle": False,
        "size_m": [
            _lerp(low, high, fractions[offset + 1][index])
            for offset, (low, high) in enumerate(size_ranges)
        ],
        "mass_kg": _lerp(*mass_range, fractions[4][index]),
        "friction": _lerp(0.32, 0.42, fractions[5][index]),
        "offset_m": [
            _lerp(-0.004, 0.004, fractions[6][index]),
            _lerp(-0.004, 0.004, fractions[7][index]),
        ],
        "recovery_contact_offset_m": [
            _lerp(*recovery_x_range, fractions[8][index]),
            _lerp(*recovery_y_range, fractions[9][index]),
        ],
        "recovery_contact_penetration_delta_m": _lerp(
            0.0, 0.0005, fractions[10][index]
        ),
        "recovery_vertical_speed_scale": _lerp(0.60, 0.68, fractions[11][index]),
        "retry_index": 1 + (index % 2),
        "task_text": (
            f"Pick up the {profile.replace('_', ' ')} with top suction and place it "
            "at the marked parcel destination."
        ),
    }


def _side_suction(
    index: int, count: int, fractions: list[list[float]]
) -> dict[str, Any]:
    diameter = _lerp(0.040, 0.046, fractions[0][index])
    return {
        "profile": "upright_canister",
        "shape": "cylinder",
        "orientation_mode": "upright",
        "yaw_rad": 0.0,
        "handling_class": "parallel_jaw",
        "grasp_mode": "side_suction",
        "minimum_sealed_cups": 1,
        "cooperative_cradle": False,
        "size_m": [
            diameter,
            diameter,
            _lerp(0.065, 0.075, fractions[1][index]),
        ],
        "mass_kg": _lerp(0.13, 0.21, fractions[2][index]),
        "friction": _lerp(0.28, 0.34, fractions[3][index]),
        "offset_m": [
            _lerp(-0.004, 0.004, fractions[4][index]),
            _lerp(-0.004, 0.004, fractions[5][index]),
        ],
        "recovery_contact_offset_m": [
            _lerp(-0.001, 0.001, fractions[6][index]),
            _lerp(0.0053, 0.0067, fractions[7][index]),
        ],
        "recovery_contact_penetration_delta_m": _lerp(
            0.0002, 0.0008, fractions[8][index]
        ),
        "recovery_vertical_speed_scale": _lerp(0.60, 0.68, fractions[9][index]),
        "recovery_approach_speed_scale": _lerp(0.75, 1.0, fractions[10][index]),
        "retry_index": 1 + (index % 2),
        "task_text": (
            "Pick up the upright canister with side suction and place it at the "
            "marked parcel destination."
        ),
    }


def _cooperative_cradle(
    index: int, count: int, fractions: list[list[float]]
) -> dict[str, Any]:
    return {
        "profile": "large_rectangular_carton_boundary",
        "shape": "box",
        "orientation_mode": "yaw",
        "yaw_rad": _lerp(-0.04, 0.04, fractions[0][index]),
        "handling_class": "cradle_required",
        "grasp_mode": "cooperative_cradle",
        "minimum_sealed_cups": 1,
        "cooperative_cradle": True,
        "cradle_contact_memory": True,
        "size_m": [
            _lerp(1.40, 1.48, fractions[1][index]),
            _lerp(0.115, 0.125, fractions[2][index]),
            _lerp(0.175, 0.185, fractions[3][index]),
        ],
        "mass_kg": _lerp(0.35, 0.45, fractions[4][index]),
        "friction": _lerp(0.85, 0.95, fractions[5][index]),
        "offset_m": [
            _lerp(-0.002, 0.002, fractions[6][index]),
            _lerp(-0.002, 0.002, fractions[7][index]),
        ],
        "recovery_contact_offset_m": [
            _lerp(-0.0005, 0.0005, fractions[8][index]),
            _lerp(0.0025, 0.0035, fractions[9][index]),
        ],
        "recovery_contact_penetration_delta_m": 0.0,
        "recovery_cradle_engagement_delta_m": 0.0,
        "recovery_left_lift_offset_m": [
            0.0,
            0.0,
            _lerp(0.001, 0.002, fractions[10][index]),
        ],
        "recovery_right_lift_offset_m": [
            _lerp(-0.0005, 0.0005, fractions[11][index]),
            _lerp(0.0015, 0.0025, fractions[12][index]),
            _lerp(-0.0025, -0.0015, fractions[13][index]),
        ],
        "recovery_vertical_speed_scale": _lerp(0.90, 1.0, fractions[14][index]),
        "retry_index": 2,
        "task_text": (
            "Pick up the large rectangular carton with cooperative cradle control "
            "and place it at the marked parcel destination."
        ),
    }


BUILDERS: dict[
    str, Callable[[int, int, list[list[float]]], dict[str, Any]]
] = {
    "top_suction": _top_suction,
    "side_suction": _side_suction,
    "cooperative_cradle": _cooperative_cradle,
}


def build_plan(episodes_per_mode: int, seed: int, phase: str) -> dict[str, Any]:
    if episodes_per_mode < 8:
        raise ValueError("episodes_per_mode must be at least 8")
    if phase not in {"pilot", "bulk"}:
        raise ValueError("phase must be pilot or bulk")
    episodes: list[dict[str, Any]] = []
    for mode_index, mode in enumerate(GRASP_MODES):
        rng = random.Random(seed + 1009 * mode_index)
        fractions = _dimensions(episodes_per_mode, rng, 15)
        builder = BUILDERS[mode]
        for index in range(episodes_per_mode):
            item = builder(index, episodes_per_mode, fractions)
            item.update(
                {
                    "episode_id": f"parcel-success-{phase}-v1-{mode}-{index:04d}",
                    "design_cell": f"{mode}-cell-{index % 8:02d}",
                    "split": "collection_candidate",
                    "source_identity": (
                        f"parcel-success-{phase}-v1/{mode}/{index:04d}"
                    ),
                }
            )
            episodes.append(item)
    return {
        "schema_version": 1,
        "collection_id": f"parcel-success-{phase}-v1",
        "protocol": "pi05-diversity-balanced-success-collection-v1",
        "seed": seed,
        "phase": phase,
        "episodes_per_mode": episodes_per_mode,
        "planned_attempts": len(episodes),
        "target_success_dataset": {
            "total_successes": 1500,
            "successes_per_mode": 500,
            "train": 1200,
            "development": 150,
            "confirmation": 150,
            "independent_unit": "unique_simulated_physical_episode_parameters",
        },
        "admission_policy": (
            "Only complete successful episodes with no force violation, emergency stop, "
            "expert fallback, or missing wrist RGB-D enter behavior cloning. Failed "
            "attempts remain failure telemetry."
        ),
        "literature_alignment": {
            "target_domain_examples_per_cell": 50,
            "design_cells": 24,
            "long_trajectory_sampling_cap_per_stage": 100,
            "sampling_policy": "equal grasp-mode and design-cell probability",
        },
        "episodes": episodes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episodes-per-mode", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--phase", choices=("pilot", "bulk"), default="pilot")
    args = parser.parse_args()
    plan = build_plan(args.episodes_per_mode, args.seed, args.phase)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "output": str(args.output),
        "planned_attempts": plan["planned_attempts"],
        "episodes_per_mode": plan["episodes_per_mode"],
        "seed": plan["seed"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
