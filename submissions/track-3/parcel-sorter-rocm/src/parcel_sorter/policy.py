from __future__ import annotations

import math
from pathlib import Path
from typing import Any
from typing import Protocol

from .config import ExperimentConfig
from .contracts import CartesianAction, PolicyContext
from .dataset import DEPTH_RGB_KEY, metric_depth_to_visual_rgb
from .expert import ScriptedPickPlaceExpert
from .state_machine import Command


class ActionPolicy(Protocol):
    """Stable boundary for scripted, ACT, BC, or VLA policies."""

    def predict(self, context: PolicyContext) -> CartesianAction: ...


class ScriptedExpertPolicy:
    def __init__(self, expert: ScriptedPickPlaceExpert) -> None:
        self.expert = expert

    def predict(self, context: PolicyContext) -> CartesianAction:
        return self.expert.action(context.decision, context.state)


class LeRobotPolicyAdapter:
    """Any supported LeRobot checkpoint behind the safe Cartesian action boundary."""

    def __init__(self, checkpoint: str | Path, config: ExperimentConfig) -> None:
        try:
            import torch
            from lerobot.configs.policies import PreTrainedConfig
            from lerobot.policies import make_pre_post_processors
            from lerobot.policies.factory import get_policy_class
        except ImportError as exc:
            raise RuntimeError(
                "policy evaluation requires LeRobot; run the Radeon bootstrap with "
                "INSTALL_LEROBOT=1"
            ) from exc

        self.torch = torch
        self.config = config
        self.checkpoint = Path(checkpoint).resolve()
        if not (self.checkpoint / "config.json").is_file():
            raise FileNotFoundError(f"LeRobot checkpoint not found: {self.checkpoint}")
        policy_config = PreTrainedConfig.from_pretrained(
            self.checkpoint,
            local_files_only=True,
        )
        policy_config.device = "cuda"
        policy_class = get_policy_class(policy_config.type)
        self.policy_type = policy_config.type
        visual_keys = tuple(
            key
            for key in policy_config.input_features
            if key.startswith("observation.images.")
        )
        supported_visual_keys = {
            "observation.images.overhead_rgb",
            DEPTH_RGB_KEY,
        }
        unknown_visual_keys = sorted(set(visual_keys) - supported_visual_keys)
        if unknown_visual_keys:
            raise ValueError(
                "checkpoint requests unsupported visual input(s): "
                + ", ".join(unknown_visual_keys)
            )
        if "observation.images.overhead_rgb" not in visual_keys:
            raise ValueError("checkpoint must include observation.images.overhead_rgb")
        self.visual_input_keys = visual_keys
        self.policy = policy_class.from_pretrained(
            self.checkpoint,
            config=policy_config,
            local_files_only=True,
        ).eval()
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            self.policy.config,
            pretrained_path=str(self.checkpoint),
        )
        self._last_stage: str | None = None

    def reset(self) -> None:
        self.policy.reset()
        self._last_stage = None

    def predict(self, context: PolicyContext) -> CartesianAction:
        command = Command(context.decision.command)
        if command == Command.STOP:
            return _safe_cartesian_action(
                (),
                context,
                self.config.control.max_ee_step_m,
            )
        if context.rgb is None:
            raise RuntimeError("the learned policy requires an RGB sensor frame")
        if context.decision.stage != self._last_stage:
            self.policy.reset()
            self._last_stage = context.decision.stage

        state = self.torch.tensor(
            context.state.policy_vector(),
            dtype=self.torch.float32,
            device="cuda",
        ).unsqueeze(0)
        batch_inputs: dict[str, Any] = {
            "observation.state": state,
            "task": [context.task],
        }
        for key in self.visual_input_keys:
            if key == "observation.images.overhead_rgb":
                source = context.rgb
            else:
                if context.depth is None:
                    raise RuntimeError("RGB-D checkpoint requires a metric depth frame")
                import numpy as np

                source = metric_depth_to_visual_rgb(context.depth, np)
            batch_inputs[key] = self._visual_tensor(source, key)
        batch = self.preprocessor(batch_inputs)
        with self.torch.inference_mode():
            action = self.postprocessor(self.policy.select_action(batch))
            self.torch.cuda.synchronize()
        values = action[0].detach().to("cpu").tolist()
        return _safe_cartesian_action(
            values,
            context,
            self.config.control.max_ee_step_m,
        )

    def _visual_tensor(self, source: Any, key: str) -> Any:
        image_source = source.copy() if hasattr(source, "copy") else source
        image = self.torch.as_tensor(image_source, device="cuda")
        if image.ndim != 3 or image.shape[-1] < 3:
            raise ValueError(
                f"expected HWC three-channel image for {key}, received {tuple(image.shape)}"
            )
        return (
            image[..., :3]
            .permute(2, 0, 1)
            .to(self.torch.float32)
            .div_(255.0)
            .unsqueeze(0)
        )


def _safe_cartesian_action(
    values: Any,
    context: PolicyContext,
    max_step_m: float,
) -> CartesianAction:
    """Validate a learned action and enforce motion and gripper safety limits."""
    current = tuple(float(value) for value in context.state.end_effector_pose[:3])
    command = Command(context.decision.command)
    if command == Command.STOP:
        return CartesianAction(current, (0.0, 1.0, 0.0, 0.0), 1.0, command.value)

    values = tuple(float(value) for value in values)
    if len(values) != 8 or not all(math.isfinite(value) for value in values):
        raise ValueError("policy must return eight finite Cartesian action values")

    target = _bounded_target(current, values[:3], max_step_m)
    quaternion = values[3:7]
    norm = math.sqrt(sum(value * value for value in quaternion))
    if norm < 1e-6:
        quaternion = (0.0, 1.0, 0.0, 0.0)
    else:
        quaternion = tuple(value / norm for value in quaternion)

    gripper = 1.0 if command in {
        Command.SEARCH,
        Command.MOVE_PREGRASP,
        Command.OPEN_GRIPPER,
    } else -1.0
    return CartesianAction(target, quaternion, gripper, command.value)


def _bounded_target(
    current: tuple[float, ...],
    target: tuple[float, ...],
    max_step_m: float,
) -> tuple[float, float, float]:
    delta = tuple(target_value - current_value for current_value, target_value in zip(current, target))
    distance = math.sqrt(sum(value * value for value in delta))
    if distance <= max_step_m or distance == 0:
        return tuple(target)  # type: ignore[return-value]
    scale = max_step_m / distance
    return tuple(
        current_value + offset * scale
        for current_value, offset in zip(current, delta)
    )  # type: ignore[return-value]


# Backwards-compatible name for existing evaluation scripts and external imports.
ACTPolicyAdapter = LeRobotPolicyAdapter
