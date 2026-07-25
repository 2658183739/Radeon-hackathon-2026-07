from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any, Mapping, Sequence

from .expert import profile_grasp_yaw
from .randomization import ParcelSample


@dataclass(frozen=True)
class GraspPoseCandidate:
    candidate_id: str
    target_position: tuple[float, float, float]
    target_quaternion: tuple[float, float, float, float]
    longitudinal_offset_m: float
    vertical_offset_m: float
    wrist_variant: str


IK_POSITION_TOLERANCE_M = 0.005
IK_ROTATION_TOLERANCE_RAD = 0.05
FK_POSITION_TOLERANCE_M = 0.005
STATE_RESTORE_TOLERANCE = 1e-7
MIN_VERTICAL_SIDE_OVERLAP_M = 0.020


def box_requires_geometry_aware_grasp_planning(
    sample: ParcelSample,
    *,
    hand_clearance_m: float,
    min_vertical_side_overlap_m: float = MIN_VERTICAL_SIDE_OVERLAP_M,
) -> bool:
    """Scope planning to boxes whose height reaches the palm-risk envelope."""
    if sample.shape != "box" or sample.dimensions_m is None:
        return False
    if hand_clearance_m <= 0 or min_vertical_side_overlap_m <= 0:
        raise ValueError("grasp-planning geometry thresholds must be positive")
    return sample.dimensions_m[2] >= (
        hand_clearance_m + min_vertical_side_overlap_m
    )


def interpolate_joint_segment(
    start_qpos: Sequence[float],
    goal_qpos: Sequence[float],
    *,
    max_joint_delta_rad: float,
    arm_dofs: int = 7,
) -> tuple[tuple[float, ...], ...]:
    """Return endpoint-inclusive linear joint samples for swept collision checks."""
    if len(start_qpos) != len(goal_qpos) or len(start_qpos) < arm_dofs:
        raise ValueError("joint segments require equally sized arm configurations")
    if arm_dofs < 1 or max_joint_delta_rad <= 0:
        raise ValueError("joint interpolation limits must be positive")
    maximum_delta = max(
        abs(float(goal_qpos[index]) - float(start_qpos[index]))
        for index in range(arm_dofs)
    )
    steps = max(1, int(math.ceil(maximum_delta / max_joint_delta_rad)))
    return tuple(
        tuple(
            float(start + (goal - start) * step / steps)
            for start, goal in zip(start_qpos, goal_qpos, strict=True)
        )
        for step in range(1, steps + 1)
    )


def generate_box_grasp_pose_candidates(
    sample: ParcelSample,
    parcel_pose: tuple[float, ...],
    *,
    hand_clearance_m: float,
    max_longitudinal_offset_m: float = 0.050,
    min_longitudinal_edge_margin_m: float = 0.060,
    max_vertical_offset_m: float = 0.055,
    min_vertical_side_overlap_m: float = MIN_VERTICAL_SIDE_OVERLAP_M,
    include_symmetric_wrist: bool = True,
) -> tuple[GraspPoseCandidate, ...]:
    """Generate auditable side-grasp poses for a yaw-oriented rigid box."""
    if sample.shape != "box" or sample.dimensions_m is None:
        raise ValueError("box grasp-pose generation requires box dimensions")
    if min(
        hand_clearance_m,
        min_longitudinal_edge_margin_m,
        min_vertical_side_overlap_m,
    ) <= 0:
        raise ValueError("grasp clearances and overlap must be positive")
    if max_longitudinal_offset_m < 0 or max_vertical_offset_m < 0:
        raise ValueError("grasp-pose offset limits cannot be negative")

    length_m, _, height_m = sample.dimensions_m
    available_longitudinal_offset = max(
        0.0,
        length_m / 2 - min_longitudinal_edge_margin_m,
    )
    longitudinal_extent = min(
        max_longitudinal_offset_m,
        available_longitudinal_offset,
    )
    longitudinal_offsets = _unique_values(
        (-longitudinal_extent, 0.0, longitudinal_extent)
    )

    available_vertical_offset = max(
        0.0,
        height_m / 2 - min_vertical_side_overlap_m,
    )
    vertical_extent = min(max_vertical_offset_m, available_vertical_offset)
    vertical_offsets = _unique_values(
        (
            0.0,
            min(0.020, vertical_extent),
            min(0.040, vertical_extent),
            vertical_extent,
        )
    )

    parcel_yaw = _yaw_from_pose(parcel_pose)
    base_yaw = profile_grasp_yaw(replace(sample, yaw_rad=parcel_yaw))
    variants = [("canonical", base_yaw)]
    if include_symmetric_wrist:
        variants.append(("symmetric_pi", base_yaw + math.pi))
    cos_yaw = math.cos(parcel_yaw)
    sin_yaw = math.sin(parcel_yaw)
    candidates = []
    for wrist_variant, grasp_yaw in variants:
        half_yaw = grasp_yaw / 2
        quaternion = (0.0, math.cos(half_yaw), math.sin(half_yaw), 0.0)
        for longitudinal_offset in longitudinal_offsets:
            x = parcel_pose[0] + longitudinal_offset * cos_yaw
            y = parcel_pose[1] + longitudinal_offset * sin_yaw
            for vertical_offset in vertical_offsets:
                candidate_id = (
                    f"{wrist_variant}-long-{longitudinal_offset:+.3f}"
                    f"-up-{vertical_offset:.3f}"
                )
                candidates.append(
                    GraspPoseCandidate(
                        candidate_id=candidate_id,
                        target_position=(
                            float(x),
                            float(y),
                            float(parcel_pose[2] + hand_clearance_m + vertical_offset),
                        ),
                        target_quaternion=quaternion,
                        longitudinal_offset_m=longitudinal_offset,
                        vertical_offset_m=vertical_offset,
                        wrist_variant=wrist_variant,
                    )
                )
    return tuple(candidates)


def grasp_evaluation_is_feasible(
    evaluation: Mapping[str, Any],
    *,
    collision_filter_enabled: bool = True,
) -> bool:
    """Apply the preregistered IK, state-restoration, and collision gates."""
    kinematically_feasible = (
        bool(evaluation["finite"])
        and float(evaluation["ik_position_error_m"]) <= IK_POSITION_TOLERANCE_M
        and float(evaluation["ik_rotation_error_rad"]) <= IK_ROTATION_TOLERANCE_RAD
        and float(evaluation["fk_position_error_m"]) <= FK_POSITION_TOLERANCE_M
        and float(evaluation["restore_max_abs_error"]) <= STATE_RESTORE_TOLERANCE
    )
    return kinematically_feasible and (
        not collision_filter_enabled
        or int(evaluation["disallowed_collision_count"]) == 0
    )


def grasp_evaluation_rank_key(
    evaluation: Mapping[str, Any],
    *,
    collision_filter_enabled: bool = True,
    manipulability_ranking_enabled: bool = True,
) -> tuple[Any, ...]:
    """Rank feasible poses without letting sub-threshold IK noise dominate.

    Errors are converted to pass/fail buckets. Once a solution is inside every
    kinematic tolerance, a centered low side-contact prior, joint travel,
    manipulability, and clearance determine the order rather than meaningless
    1e-6-scale solver differences.
    """
    feasible = grasp_evaluation_is_feasible(
        evaluation,
        collision_filter_enabled=collision_filter_enabled,
    )
    position_bucket = _error_bucket(
        float(evaluation["ik_position_error_m"]),
        IK_POSITION_TOLERANCE_M,
    )
    rotation_bucket = _error_bucket(
        float(evaluation["ik_rotation_error_rad"]),
        IK_ROTATION_TOLERANCE_RAD,
    )
    fk_bucket = _error_bucket(
        float(evaluation["fk_position_error_m"]),
        FK_POSITION_TOLERANCE_M,
    )
    collision_count = (
        int(evaluation["disallowed_collision_count"])
        if collision_filter_enabled
        else 0
    )
    clearance_m = (
        float(evaluation.get("nonfinger_clearance_m", 0.0))
        if collision_filter_enabled
        else 0.0
    )
    minimum_singular_value = (
        float(evaluation["minimum_singular_value"])
        if manipulability_ranking_enabled
        else 0.0
    )
    symmetric_wrist_fallback = (
        str(evaluation.get("wrist_variant", "canonical")) != "canonical"
    )
    longitudinal_offset_m = abs(
        float(evaluation.get("longitudinal_offset_m", 0.0))
    )
    vertical_offset_m = float(evaluation.get("vertical_offset_m", 0.0))
    return (
        not feasible,
        collision_count,
        position_bucket,
        rotation_bucket,
        fk_bucket,
        symmetric_wrist_fallback,
        longitudinal_offset_m,
        vertical_offset_m,
        float(evaluation["joint_distance_rad"]),
        -minimum_singular_value,
        -clearance_m,
        str(evaluation["candidate_id"]),
        str(evaluation["seed_name"]),
    )


def rank_grasp_pose_evaluations(
    evaluations: Sequence[Mapping[str, Any]],
    *,
    collision_filter_enabled: bool = True,
    manipulability_ranking_enabled: bool = True,
) -> list[Mapping[str, Any]]:
    return sorted(
        evaluations,
        key=lambda evaluation: grasp_evaluation_rank_key(
            evaluation,
            collision_filter_enabled=collision_filter_enabled,
            manipulability_ranking_enabled=manipulability_ranking_enabled,
        ),
    )


def select_grasp_pose_evaluation(
    evaluations: Sequence[Mapping[str, Any]],
    *,
    rejected_candidate_ids: frozenset[str] = frozenset(),
    collision_filter_enabled: bool = True,
    manipulability_ranking_enabled: bool = True,
) -> Mapping[str, Any] | None:
    ranked = rank_grasp_pose_evaluations(
        evaluations,
        collision_filter_enabled=collision_filter_enabled,
        manipulability_ranking_enabled=manipulability_ranking_enabled,
    )
    return next(
        (
            evaluation
            for evaluation in ranked
            if str(evaluation["candidate_id"]) not in rejected_candidate_ids
            and grasp_evaluation_is_feasible(
                evaluation,
                collision_filter_enabled=collision_filter_enabled,
            )
        ),
        None,
    )


def _error_bucket(error: float, tolerance: float) -> int:
    if not math.isfinite(error):
        return 2**31 - 1
    if error <= tolerance:
        return 0
    return int(math.ceil(error / tolerance))


def _unique_values(values: tuple[float, ...]) -> tuple[float, ...]:
    unique = []
    for value in values:
        if not any(math.isclose(value, other, abs_tol=1e-12) for other in unique):
            unique.append(float(value))
    return tuple(unique)


def _yaw_from_pose(pose: tuple[float, ...]) -> float:
    if len(pose) < 7:
        raise ValueError("parcel pose must contain xyz and a wxyz quaternion")
    w, x, y, z = pose[3:7]
    return math.atan2(
        2.0 * (w * z + x * y),
        1.0 - 2.0 * (y * y + z * z),
    )
