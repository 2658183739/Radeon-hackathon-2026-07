"""Fail-closed residual harness for the 19-D mobile bimanual policy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable

from .mobile_task import decode_mobile_bimanual_action, limit_mobile_arm_step


@dataclass(frozen=True)
class MobileHarnessConfig:
    candidate_scales: tuple[float, ...] = (0.0, 0.25, 0.5, 0.75, 1.0)
    max_base_residual_m_s: float = 0.02
    max_yaw_residual_rad_s: float = 0.20
    max_position_residual_m: float = 0.01
    max_quaternion_residual_rad: float = math.radians(5.0)
    max_base_linear_speed_m_s: float = 0.05
    max_base_yaw_rate_rad_s: float = 1.0
    max_cartesian_step_m: float = 0.04
    min_progress_ratio: float = 0.50
    force_limit_n: float = 35.0

    def __post_init__(self) -> None:
        positive = (
            self.max_base_residual_m_s,
            self.max_yaw_residual_rad_s,
            self.max_position_residual_m,
            self.max_quaternion_residual_rad,
            self.max_base_linear_speed_m_s,
            self.max_base_yaw_rate_rad_s,
            self.max_cartesian_step_m,
            self.force_limit_n,
        )
        if any(not math.isfinite(value) or value <= 0.0 for value in positive):
            raise ValueError("mobile harness limits must be finite and positive")
        if not 0.0 < self.min_progress_ratio <= 1.0:
            raise ValueError("min_progress_ratio must be in (0, 1]")
        if not self.candidate_scales or any(
            not math.isfinite(value) or not 0.0 <= value <= 1.0
            for value in self.candidate_scales
        ):
            raise ValueError("candidate scales must be finite values in [0, 1]")
        if 0.0 not in self.candidate_scales:
            raise ValueError("candidate scales must include the expert fallback 0.0")


@dataclass(frozen=True)
class MobileHarnessCandidate:
    scale: float
    action: tuple[float, ...]
    safe: bool
    score: float
    min_progress_ratio: float
    max_cartesian_step_m: float
    tool_command_corrections: int
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class MobileHarnessDecision:
    selected: MobileHarnessCandidate
    candidates: tuple[MobileHarnessCandidate, ...]
    fallback_to_expert: bool
    emergency_stop: bool
    rejected_vla: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def select_mobile_harness_action(
    *,
    state: Iterable[float],
    expert_action: Iterable[float],
    vla_action: Iterable[float],
    stage: str,
    config: MobileHarnessConfig = MobileHarnessConfig(),
) -> MobileHarnessDecision:
    """Generate residual candidates and select the largest verified VLA contribution.

    The deterministic expert remains the nominal controller. SmolVLA may only
    contribute bounded continuous residuals. Discrete tool commands are copied
    from the expert because a sign error can release a parcel immediately.
    """

    state_values = _finite_vector(state, 43, "state")
    expert = _finite_vector(expert_action, 19, "expert action")
    raw_vla = tuple(float(value) for value in vla_action)
    rejected_vla = len(raw_vla) != 19 or any(
        not math.isfinite(value) for value in raw_vla
    )
    if not rejected_vla:
        rejected_vla = any(
            math.sqrt(sum(value * value for value in raw_vla[start : start + 4]))
            <= 1e-8
            for start in (6, 14)
        )
    vla = expert if rejected_vla else raw_vla
    force_n = max(abs(state_values[38]), abs(state_values[39]))
    if force_n >= config.force_limit_n:
        stop = _emergency_stop_candidate(
            state_values, expert, f"force_gate_stop:{force_n:.6g}N"
        )
        return MobileHarnessDecision(
            selected=stop,
            candidates=(stop,),
            fallback_to_expert=False,
            emergency_stop=True,
            rejected_vla=rejected_vla,
        )

    candidates = tuple(
        _candidate(
            scale=float(scale),
            state=state_values,
            expert=expert,
            vla=vla,
            stage=stage,
            config=config,
            rejected_vla=rejected_vla,
        )
        for scale in config.candidate_scales
    )
    safe = tuple(candidate for candidate in candidates if candidate.safe)
    if not safe:
        stop = _emergency_stop_candidate(
            state_values, expert, "no_safe_candidate_stop"
        )
        return MobileHarnessDecision(
            selected=stop,
            candidates=(*candidates, stop),
            fallback_to_expert=False,
            emergency_stop=True,
            rejected_vla=rejected_vla,
        )
    selected = max(safe, key=lambda item: (item.score, item.scale))
    return MobileHarnessDecision(
        selected=selected,
        candidates=candidates,
        fallback_to_expert=selected.scale == 0.0,
        emergency_stop=False,
        rejected_vla=rejected_vla,
    )


def build_mobile_failure_replay_manifest(
    collection_summary: dict[str, Any],
    *,
    source_summary: str = "unknown",
    holdout_episode_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Convert mobile collection failures into an auditable curriculum queue."""

    results = collection_summary.get("results")
    if not isinstance(results, list):
        raise ValueError("mobile collection summary must contain a results list")
    holdout = {str(value) for value in holdout_episode_ids}
    items = []
    for result in results:
        if not isinstance(result, dict) or bool(result.get("success")):
            continue
        episode_id = str(result.get("episode_id", "unknown"))
        if episode_id in holdout:
            continue
        parameters = result.get("parameters") or {}
        failure_stage = str(result.get("failure_stage") or "unclassified")
        force_n = float(result.get("max_contact_force_n") or 0.0)
        mass_kg = float(parameters.get("mass_kg") or 0.0)
        stage_priority = {
            "force_safety_abort": 6.0,
            "lift_success": 4.5,
            "placement_success": 3.5,
            "release_success": 3.0,
        }.get(failure_stage, 2.0)
        boundary_bonus = min(1.0, max(0.0, mass_kg - 0.40) / 0.25)
        items.append(
            {
                "episode_id": episode_id,
                "profile": str(result.get("profile", parameters.get("profile", "unknown"))),
                "failure_stage": failure_stage,
                "priority": stage_priority + boundary_bonus,
                "max_contact_force_n": force_n,
                "parameters": parameters,
                "curriculum_bridge": {
                    **parameters,
                    "episode_id": f"{episode_id}-bridge",
                    "mass_kg": round(max(0.05, mass_kg * 0.90), 4),
                },
                "source_summary": source_summary,
            }
        )
    items.sort(key=lambda item: (-float(item["priority"]), str(item["episode_id"])))
    return {
        "schema_version": 1,
        "protocol": "mobile-failure-replay-curriculum-v1",
        "holdout_episode_ids": sorted(holdout),
        "items": items,
        "counts_by_failure_stage": {
            stage: sum(item["failure_stage"] == stage for item in items)
            for stage in sorted({str(item["failure_stage"]) for item in items})
        },
        "claim_boundary": (
            "queue generation only; collection, retraining, and checkpoint promotion "
            "remain separately gated"
        ),
    }


def _candidate(
    *,
    scale: float,
    state: tuple[float, ...],
    expert: tuple[float, ...],
    vla: tuple[float, ...],
    stage: str,
    config: MobileHarnessConfig,
    rejected_vla: bool,
) -> MobileHarnessCandidate:
    base_residual = _clip_norm(
        tuple(vla[index] - expert[index] for index in (0, 1)),
        config.max_base_residual_m_s,
    )
    yaw_residual = _clip(
        vla[2] - expert[2], config.max_yaw_residual_rad_s
    )
    action = [
        expert[0] + scale * base_residual[0],
        expert[1] + scale * base_residual[1],
        expert[2] + scale * yaw_residual,
    ]
    tool_corrections = 0
    for action_start, state_start in ((3, 24), (11, 31)):
        expert_position = expert[action_start : action_start + 3]
        residual = _clip_norm(
            tuple(
                vla[action_start + index] - expert[action_start + index]
                for index in range(3)
            ),
            config.max_position_residual_m,
        )
        candidate_position = tuple(
            nominal + scale * offset
            for nominal, offset in zip(expert_position, residual, strict=True)
        )
        action.extend(candidate_position)
        action.extend(
            _bounded_slerp(
                expert[action_start + 3 : action_start + 7],
                vla[action_start + 3 : action_start + 7],
                scale=scale,
                max_angle_rad=config.max_quaternion_residual_rad,
            )
        )
        expert_tool = 1.0 if expert[action_start + 7] >= 0.0 else -1.0
        vla_tool = 1.0 if vla[action_start + 7] >= 0.0 else -1.0
        tool_corrections += int(expert_tool != vla_tool)
        action.append(expert_tool)

    reasons = []
    try:
        expert_decoded = decode_mobile_bimanual_action(
            expert,
            max_base_linear_speed_m_s=config.max_base_linear_speed_m_s,
            max_base_yaw_rate_rad_s=config.max_base_yaw_rate_rad_s,
        )
        expert_left = limit_mobile_arm_step(
            expert_decoded.left, state[24:27], max_step_m=config.max_cartesian_step_m
        )
        expert_right = limit_mobile_arm_step(
            expert_decoded.right, state[31:34], max_step_m=config.max_cartesian_step_m
        )
        decoded = decode_mobile_bimanual_action(
            action,
            max_base_linear_speed_m_s=config.max_base_linear_speed_m_s,
            max_base_yaw_rate_rad_s=config.max_base_yaw_rate_rad_s,
        )
        left = limit_mobile_arm_step(
            decoded.left, state[24:27], max_step_m=config.max_cartesian_step_m
        )
        right = limit_mobile_arm_step(
            decoded.right, state[31:34], max_step_m=config.max_cartesian_step_m
        )
        left_step = math.dist(left.position_m, state[24:27])
        right_step = math.dist(right.position_m, state[31:34])
        if left.position_m != decoded.left.position_m or right.position_m != decoded.right.position_m:
            reasons.append("cartesian_step_clipped")
        if math.hypot(*action[:2]) > config.max_base_linear_speed_m_s + 1e-9:
            reasons.append("base_speed_clipped")
        progress_values = [
            _progress_ratio(state[24:27], expert_left.position_m, left.position_m),
            _progress_ratio(state[31:34], expert_right.position_m, right.position_m),
        ]
        if min(progress_values) + 1e-9 < config.min_progress_ratio:
            reasons.append("expert_progress_gate")
        executable_action = (
            *decoded.base_velocity_xy_yaw,
            *left.position_m,
            *left.quaternion_wxyz,
            left.gripper,
            *right.position_m,
            *right.quaternion_wxyz,
            right.gripper,
        )
    except ValueError as exc:
        left_step = right_step = math.inf
        progress_values = [-math.inf]
        executable_action = tuple(float(value) for value in action)
        reasons.append(f"decode_error:{exc}")
    if rejected_vla and scale > 0.0:
        reasons.append("invalid_vla_action")
    if stage == "release" and tool_corrections:
        reasons.append("stage_tool_interlock")
    safe = not any(
        reason in {
            "expert_progress_gate",
            "invalid_vla_action",
        }
        or reason.startswith("decode_error:")
        for reason in reasons
    )
    score = scale - 0.02 * tool_corrections - (10.0 if not safe else 0.0)
    return MobileHarnessCandidate(
        scale=scale,
        action=tuple(float(value) for value in executable_action),
        safe=safe,
        score=score,
        min_progress_ratio=min(progress_values),
        max_cartesian_step_m=max(left_step, right_step),
        tool_command_corrections=tool_corrections,
        reasons=tuple(reasons or ("verified",)),
    )


def _emergency_stop_candidate(
    state: tuple[float, ...], expert: tuple[float, ...], reason: str
) -> MobileHarnessCandidate:
    action = (
        0.0,
        0.0,
        0.0,
        *state[24:31],
        -1.0,
        *state[31:38],
        1.0,
    )
    return MobileHarnessCandidate(
        scale=-1.0,
        action=tuple(float(value) for value in action),
        safe=True,
        score=-1.0,
        min_progress_ratio=0.0,
        max_cartesian_step_m=0.0,
        tool_command_corrections=sum(
            (action[index] >= 0.0) != (expert[index] >= 0.0)
            for index in (10, 18)
        ),
        reasons=(reason,),
    )


def _finite_vector(values: Iterable[float], length: int, name: str) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if len(result) != length:
        raise ValueError(f"{name} must contain {length} values")
    if any(not math.isfinite(value) for value in result):
        raise ValueError(f"{name} contains non-finite values")
    return result


def _clip(value: float, limit: float) -> float:
    return max(-limit, min(limit, value))


def _clip_norm(values: tuple[float, ...], limit: float) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= limit or norm <= 1e-12:
        return values
    return tuple(value * limit / norm for value in values)


def _normalize_quaternion(values: tuple[float, ...]) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= 1e-8:
        raise ValueError("quaternion norm is zero")
    return tuple(value / norm for value in values)


def _bounded_slerp(
    start: tuple[float, ...],
    end: tuple[float, ...],
    *,
    scale: float,
    max_angle_rad: float,
) -> tuple[float, ...]:
    left = _normalize_quaternion(start)
    right = _normalize_quaternion(end)
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    if dot < 0.0:
        right = tuple(-value for value in right)
        dot = -dot
    dot = max(-1.0, min(1.0, dot))
    angle = 2.0 * math.acos(dot)
    bounded_scale = scale * min(1.0, max_angle_rad / max(angle, 1e-12))
    mixed = tuple(
        (1.0 - bounded_scale) * a + bounded_scale * b
        for a, b in zip(left, right, strict=True)
    )
    return _normalize_quaternion(mixed)


def _progress_ratio(
    current: tuple[float, ...],
    expert: tuple[float, ...],
    candidate: tuple[float, ...],
) -> float:
    motion = tuple(target - value for target, value in zip(expert, current, strict=True))
    denominator = sum(value * value for value in motion)
    if denominator <= 1e-12:
        return 1.0
    candidate_motion = tuple(
        target - value for target, value in zip(candidate, current, strict=True)
    )
    return sum(
        value * direction
        for value, direction in zip(candidate_motion, motion, strict=True)
    ) / denominator
