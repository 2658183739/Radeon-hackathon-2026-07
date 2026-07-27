"""Online LeRobot VLA plus Harness-Lite controller for the mobile parcel robot."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
import time
from typing import Any, Iterable

from .dataset import metric_depth_to_visual_rgb
from .mobile_depth_sidecar import depth_risk_scale_cap
from .mobile_dataset import MOBILE_DEPTH_RGB_KEY, MOBILE_RGB_KEY
from .mobile_harness import (
    MobileHarnessConfig,
    force_memory_scale_cap,
    select_mobile_harness_action,
)
from .mobile_primitive_learning import primitive_task_text


@dataclass(frozen=True)
class VLAGoalJudgement:
    distance_m: float
    direction_alignment: float
    direction_consistent: bool
    arrival_claimed: bool
    arrival_verified: bool
    scale_cap: float


def update_primitive_progress_peak(
    previous_peak: float,
    progress: float | None,
    *,
    stage_changed: bool,
) -> float:
    """Latch the strongest progress evidence within one primitive only."""

    if not math.isfinite(previous_peak) or not 0.0 <= previous_peak <= 1.0:
        raise ValueError("previous progress peak must be finite and in [0, 1]")
    if progress is not None and (
        not math.isfinite(progress) or not 0.0 <= progress <= 1.0
    ):
        raise ValueError("progress must be None or a finite value in [0, 1]")
    base = 0.0 if stage_changed else previous_peak
    return max(base, 0.0 if progress is None else progress)


def evaluate_vla_goal_judgement(
    state: Iterable[float],
    vla_action: Iterable[float],
    *,
    stage: str,
    primitive_complete: bool,
    goal_xy: Iterable[float] | None = None,
    arrival_tolerance_m: float = 0.015,
) -> VLAGoalJudgement:
    """Check the VLA route proposal and arrival claim against the encoded goal."""

    state_values = tuple(float(value) for value in state)
    action_values = tuple(float(value) for value in vla_action)
    if len(state_values) != 43 or len(action_values) < 2:
        raise ValueError("goal judgement requires 43-D state and a base action")
    if any(not math.isfinite(value) for value in (*state_values, *action_values[:2])):
        raise ValueError("goal judgement inputs must be finite")
    if arrival_tolerance_m <= 0.0 or not math.isfinite(arrival_tolerance_m):
        raise ValueError("arrival tolerance must be finite and positive")
    goal_values = (
        tuple(float(value) for value in goal_xy)
        if goal_xy is not None
        else state_values[40:42]
    )
    if len(goal_values) != 2 or any(not math.isfinite(value) for value in goal_values):
        raise ValueError("goal_xy must contain two finite values")
    goal = (
        goal_values[0] - state_values[0],
        goal_values[1] - state_values[1],
    )
    distance_m = math.hypot(*goal)
    proposed = action_values[:2]
    proposed_speed = math.hypot(*proposed)
    if distance_m <= 1e-9:
        alignment = 1.0
    elif proposed_speed <= 1e-9:
        alignment = 0.0
    else:
        alignment = max(
            -1.0,
            min(
                1.0,
                (goal[0] * proposed[0] + goal[1] * proposed[1])
                / (distance_m * proposed_speed),
            ),
        )
    direction_consistent = stage != "transport" or alignment >= -0.05
    arrival_claimed = bool(primitive_complete and stage == "transport")
    arrival_verified = bool(arrival_claimed and distance_m <= arrival_tolerance_m)
    return VLAGoalJudgement(
        distance_m=distance_m,
        direction_alignment=alignment,
        direction_consistent=direction_consistent,
        arrival_claimed=arrival_claimed,
        arrival_verified=arrival_verified,
        scale_cap=1.0 if direction_consistent else 0.0,
    )


class MobileVLAHarnessController:
    """Run low-rate SmolVLA or PI0.5 inference behind the same safety harness."""

    def __init__(
        self,
        checkpoint: str | Path,
        *,
        seed: int = 20260727,
        harness_config: MobileHarnessConfig = MobileHarnessConfig(),
        force_memory_enabled: bool = False,
        depth_sidecar_enabled: bool = False,
        primitive_progress_threshold: float = 0.90,
    ) -> None:
        import torch
        from lerobot.configs.policies import PreTrainedConfig
        from lerobot.policies import make_pre_post_processors
        from lerobot.policies.factory import get_policy_class

        checkpoint = Path(checkpoint)
        config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
        if config.type not in {"smolvla", "pi05"}:
            raise RuntimeError(
                f"mobile VLA checkpoint must be SmolVLA or PI0.5, got {config.type!r}"
            )
        if config.input_features["observation.state"].shape != (43,):
            raise RuntimeError("VLA checkpoint must consume the 43-D mobile state")
        output_shape = config.output_features["action"].shape
        if output_shape not in {(19,), (20,)}:
            raise RuntimeError(
                "VLA checkpoint must emit 19-D mobile actions or 19-D actions "
                "plus one primitive-progress channel"
            )
        visual_keys = {
            key for key in config.input_features if key.startswith("observation.images.")
        }
        supported_visual_keys = {MOBILE_RGB_KEY, MOBILE_DEPTH_RGB_KEY}
        if MOBILE_RGB_KEY not in visual_keys or not visual_keys <= supported_visual_keys:
            raise RuntimeError(
                f"unsupported mobile VLA visual contract: {sorted(visual_keys)}"
            )
        config.device = "cuda"
        config.n_action_steps = 1
        self._torch = torch
        self._config = config
        self.policy_type = str(config.type)
        policy_class = get_policy_class(config.type)
        if config.use_peft:
            from peft import PeftConfig, PeftModel

            peft_config = PeftConfig.from_pretrained(checkpoint)
            base_checkpoint = peft_config.base_model_name_or_path
            if not base_checkpoint:
                raise RuntimeError("PEFT VLA checkpoint does not identify its base model")
            base_policy = policy_class.from_pretrained(
                base_checkpoint,
                config=config,
                local_files_only=True,
            )
            self._policy = PeftModel.from_pretrained(
                base_policy,
                checkpoint,
                config=peft_config,
                is_trainable=False,
            ).eval()
        else:
            self._policy = policy_class.from_pretrained(
                checkpoint, config=config, local_files_only=True
            ).eval()
        self._preprocessor, self._postprocessor = make_pre_post_processors(
            config, pretrained_path=str(checkpoint)
        )
        self._harness_config = harness_config
        self._force_memory_enabled = bool(force_memory_enabled)
        self._depth_sidecar_enabled = bool(depth_sidecar_enabled)
        self._force_history_n: deque[float] = deque(
            maxlen=harness_config.force_memory_window
        )
        self._uses_depth_rgb = MOBILE_DEPTH_RGB_KEY in visual_keys
        if not 0.0 < primitive_progress_threshold <= 1.0:
            raise ValueError("primitive_progress_threshold must be in (0, 1]")
        self._uses_progress_channel = output_shape == (20,)
        self._primitive_progress_threshold = float(primitive_progress_threshold)
        self._primitive_progress_peak = 0.0
        self._progress_stage: str | None = None
        self._seed = int(seed)
        self._calls = 0
        self._reset()

    def select(
        self,
        *,
        rgb: Any,
        depth: Any | None = None,
        state: Iterable[float],
        task: str,
        expert_action: Iterable[float],
        stage: str,
        goal_xy: Iterable[float] | None = None,
    ) -> tuple[tuple[float, ...], dict[str, Any]]:
        import numpy as np

        torch = self._torch
        state_values = tuple(float(value) for value in state)
        expert_values = tuple(float(value) for value in expert_action)
        image = np.asarray(rgb, dtype=np.uint8)[..., :3]
        image_tensor = (
            torch.from_numpy(image.copy()).permute(2, 0, 1).float().div_(255.0)
        )
        policy_task = primitive_task_text(task, stage) if self._uses_progress_channel else task
        batch: dict[str, Any] = {
            "observation.state": torch.tensor(state_values, dtype=torch.float32).unsqueeze(0).cuda(),
            MOBILE_RGB_KEY: image_tensor.unsqueeze(0).cuda(),
            "task": [policy_task],
        }
        if self._uses_depth_rgb:
            if depth is None:
                raise ValueError("RGB-D VLA checkpoint requires metric depth")
            depth_rgb = metric_depth_to_visual_rgb(depth, np)
            depth_tensor = (
                torch.from_numpy(depth_rgb.copy()).permute(2, 0, 1).float().div_(255.0)
            )
            batch[MOBILE_DEPTH_RGB_KEY] = depth_tensor.unsqueeze(0).cuda()
        call_seed = self._seed + self._calls
        torch.manual_seed(call_seed)
        torch.cuda.manual_seed_all(call_seed)
        self._reset()
        with torch.inference_mode():
            torch.cuda.synchronize()
            started = time.perf_counter()
            action = self._postprocessor(
                self._policy.select_action(self._preprocessor(batch))
            )
            torch.cuda.synchronize()
            latency_ms = (time.perf_counter() - started) * 1000.0
        policy_output = tuple(float(value) for value in action.detach().cpu().reshape(-1))
        predicted = policy_output[:19]
        progress_raw = policy_output[19] if self._uses_progress_channel else None
        progress = (
            min(1.0, max(0.0, progress_raw)) if progress_raw is not None and math.isfinite(progress_raw) else None
        )
        instantaneous_complete = bool(
            progress is not None and progress >= self._primitive_progress_threshold
        )
        self._primitive_progress_peak = update_primitive_progress_peak(
            self._primitive_progress_peak,
            progress,
            stage_changed=self._progress_stage != stage,
        )
        self._progress_stage = stage
        primitive_complete = bool(
            self._primitive_progress_peak >= self._primitive_progress_threshold
        )
        goal_judgement = evaluate_vla_goal_judgement(
            state_values,
            predicted,
            stage=stage,
            primitive_complete=primitive_complete,
            goal_xy=goal_xy,
        )
        self._force_history_n.append(max(abs(state_values[38]), abs(state_values[39])))
        force_memory = force_memory_scale_cap(
            self._force_history_n,
            config=self._harness_config,
        )
        depth_risk = depth_risk_scale_cap(depth) if self._depth_sidecar_enabled else None
        force_scale_cap = force_memory.scale_cap if self._force_memory_enabled else 1.0
        depth_scale_cap = depth_risk.scale_cap if depth_risk is not None else 1.0
        maximum_vla_scale = min(
            force_scale_cap, depth_scale_cap, goal_judgement.scale_cap
        )
        if goal_judgement.scale_cap < min(force_scale_cap, depth_scale_cap):
            maximum_vla_scale_reason = "goal_direction_mismatch"
        elif depth_scale_cap < force_scale_cap:
            maximum_vla_scale_reason = "depth_geometry_scale_gate"
        else:
            maximum_vla_scale_reason = "force_memory_scale_gate"
        decision = select_mobile_harness_action(
            state=state_values,
            expert_action=expert_values,
            vla_action=predicted,
            stage=stage,
            config=self._harness_config,
            maximum_vla_scale=maximum_vla_scale,
            maximum_vla_scale_reason=maximum_vla_scale_reason,
        )
        self._calls += 1
        telemetry = {
            "policy_type": self.policy_type,
            "call_index": self._calls - 1,
            "seed": call_seed,
            "stage": stage,
            "observation_modality": "rgbd" if self._uses_depth_rgb else "rgb",
            "latency_ms": latency_ms,
            "finite": len(policy_output) in (19, 20)
            and all(math.isfinite(value) for value in policy_output),
            "policy_task": policy_task,
            "primitive_progress_enabled": self._uses_progress_channel,
            "primitive_progress_raw": progress_raw,
            "primitive_progress": progress,
            "primitive_progress_peak": self._primitive_progress_peak,
            "primitive_complete_instantaneous": instantaneous_complete,
            "primitive_complete": primitive_complete,
            "goal_judgement": asdict(goal_judgement),
            "selected_scale": decision.selected.scale,
            "fallback_to_expert": decision.fallback_to_expert,
            "emergency_stop": decision.emergency_stop,
            "rejected_vla": decision.rejected_vla,
            "tool_command_corrections": decision.selected.tool_command_corrections,
            "candidate_count": len(decision.candidates),
            "selected_reasons": list(decision.selected.reasons),
            "raw_base_action": list(predicted[:3]),
            "expert_base_action": list(expert_values[:3]),
            "selected_base_action": list(decision.selected.action[:3]),
            "force_memory_enabled": self._force_memory_enabled,
            "force_memory": force_memory.to_dict(),
            "depth_sidecar_enabled": self._depth_sidecar_enabled,
            "depth_risk": depth_risk.to_dict() if depth_risk is not None else None,
            "combined_scale_cap": maximum_vla_scale,
            "combined_scale_cap_reason": maximum_vla_scale_reason,
        }
        return decision.selected.action, telemetry
    def warmup(
        self,
        *,
        rgb: Any,
        depth: Any | None = None,
        state: Iterable[float],
        task: str,
        expert_action: Iterable[float],
    ) -> None:
        self.select(
            rgb=rgb,
            depth=depth,
            state=state,
            task=task,
            expert_action=expert_action,
            stage="pregrasp",
        )
        self._calls = 0
        self._force_history_n.clear()

    def _reset(self) -> None:
        for component in (self._policy, self._preprocessor, self._postprocessor):
            reset = getattr(component, "reset", None)
            if callable(reset):
                reset()


# Compatibility for existing experiment scripts and stored ablation commands.
MobileSmolVLAHarnessController = MobileVLAHarnessController
