from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DynamicGraspThresholds:
    """Frozen pass/fail limits for a short loaded-grasp physics probe."""

    min_parcel_lift_m: float = 0.020
    max_relative_step_m: float = 0.008
    max_downward_step_m: float = 0.006
    max_contact_force_n: float = 35.0
    min_dual_contact_fraction: float = 0.80

    def validate(self) -> None:
        positive = (
            self.min_parcel_lift_m,
            self.max_relative_step_m,
            self.max_downward_step_m,
            self.max_contact_force_n,
        )
        if any(not math.isfinite(value) or value <= 0 for value in positive):
            raise ValueError("dynamic grasp thresholds must be finite and positive")
        if (
            not math.isfinite(self.min_dual_contact_fraction)
            or not 0.0 <= self.min_dual_contact_fraction <= 1.0
        ):
            raise ValueError("min_dual_contact_fraction must be in [0, 1]")


def dynamic_grasp_is_stable(
    evaluation: Mapping[str, Any],
    thresholds: DynamicGraspThresholds,
) -> bool:
    """Apply the preregistered safety and retention gates to one rollout."""
    thresholds.validate()
    return (
        bool(evaluation.get("captured", False))
        and bool(evaluation.get("final_dual_contact", False))
        and not bool(evaluation.get("safety_aborted", False))
        and bool(evaluation.get("finite", False))
        and float(evaluation["parcel_lift_m"]) >= thresholds.min_parcel_lift_m
        and float(evaluation["max_relative_step_m"])
        <= thresholds.max_relative_step_m
        and float(evaluation["max_downward_step_m"])
        <= thresholds.max_downward_step_m
        and float(evaluation["peak_contact_force_n"])
        <= thresholds.max_contact_force_n
        and float(evaluation["dual_contact_fraction"])
        >= thresholds.min_dual_contact_fraction
    )


def dynamic_grasp_rank_key(
    evaluation: Mapping[str, Any],
    thresholds: DynamicGraspThresholds,
) -> tuple[Any, ...]:
    """Rank safe retained grasps before smoothness and the static prior."""
    stable = dynamic_grasp_is_stable(evaluation, thresholds)
    return (
        not stable,
        bool(evaluation.get("safety_aborted", False)),
        not bool(evaluation.get("final_dual_contact", False)),
        not bool(evaluation.get("captured", False)),
        -float(evaluation.get("dual_contact_fraction", 0.0)),
        float(evaluation.get("max_downward_step_m", math.inf)),
        float(evaluation.get("max_relative_step_m", math.inf)),
        float(evaluation.get("final_relative_drift_m", math.inf)),
        -float(evaluation.get("parcel_lift_m", 0.0)),
        float(evaluation.get("peak_contact_force_n", math.inf)),
        int(evaluation.get("static_rank", 2**31 - 1)),
        str(evaluation.get("candidate_id", "")),
        str(evaluation.get("seed_name", "")),
    )


def rank_dynamic_grasp_evaluations(
    evaluations: Sequence[Mapping[str, Any]],
    thresholds: DynamicGraspThresholds,
) -> list[Mapping[str, Any]]:
    return sorted(
        evaluations,
        key=lambda evaluation: dynamic_grasp_rank_key(evaluation, thresholds),
    )
