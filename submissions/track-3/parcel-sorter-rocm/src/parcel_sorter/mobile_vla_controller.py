"""Online SmolVLA plus Harness-Lite controller for the mobile parcel robot."""

from __future__ import annotations

import math
from pathlib import Path
import time
from typing import Any, Iterable

from .dataset import metric_depth_to_visual_rgb
from .mobile_dataset import MOBILE_DEPTH_RGB_KEY, MOBILE_RGB_KEY
from .mobile_harness import MobileHarnessConfig, select_mobile_harness_action


class MobileSmolVLAHarnessController:
    """Run low-rate VLA inference while a deterministic controller stays in charge."""

    def __init__(
        self,
        checkpoint: str | Path,
        *,
        seed: int = 20260727,
        harness_config: MobileHarnessConfig = MobileHarnessConfig(),
    ) -> None:
        import torch
        from lerobot.configs.policies import PreTrainedConfig
        from lerobot.policies import make_pre_post_processors
        from lerobot.policies.factory import get_policy_class

        checkpoint = Path(checkpoint)
        config = PreTrainedConfig.from_pretrained(checkpoint, local_files_only=True)
        if config.input_features["observation.state"].shape != (43,):
            raise RuntimeError("SmolVLA checkpoint must consume the 43-D mobile state")
        if config.output_features["action"].shape != (19,):
            raise RuntimeError("SmolVLA checkpoint must emit the 19-D mobile action")
        visual_keys = {
            key for key in config.input_features if key.startswith("observation.images.")
        }
        supported_visual_keys = {MOBILE_RGB_KEY, MOBILE_DEPTH_RGB_KEY}
        if MOBILE_RGB_KEY not in visual_keys or not visual_keys <= supported_visual_keys:
            raise RuntimeError(
                f"unsupported mobile SmolVLA visual contract: {sorted(visual_keys)}"
            )
        config.device = "cuda"
        config.n_action_steps = 1
        self._torch = torch
        self._config = config
        self._policy = get_policy_class(config.type).from_pretrained(
            checkpoint, config=config, local_files_only=True
        ).eval()
        self._preprocessor, self._postprocessor = make_pre_post_processors(
            self._policy.config, pretrained_path=str(checkpoint)
        )
        self._harness_config = harness_config
        self._uses_depth_rgb = MOBILE_DEPTH_RGB_KEY in visual_keys
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
    ) -> tuple[tuple[float, ...], dict[str, Any]]:
        import numpy as np

        torch = self._torch
        state_values = tuple(float(value) for value in state)
        expert_values = tuple(float(value) for value in expert_action)
        image = np.asarray(rgb, dtype=np.uint8)[..., :3]
        image_tensor = (
            torch.from_numpy(image.copy()).permute(2, 0, 1).float().div_(255.0)
        )
        batch: dict[str, Any] = {
            "observation.state": torch.tensor(state_values, dtype=torch.float32).unsqueeze(0).cuda(),
            MOBILE_RGB_KEY: image_tensor.unsqueeze(0).cuda(),
            "task": [task],
        }
        if self._uses_depth_rgb:
            if depth is None:
                raise ValueError("RGB-D SmolVLA checkpoint requires metric depth")
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
        predicted = tuple(float(value) for value in action.detach().cpu().reshape(-1))
        decision = select_mobile_harness_action(
            state=state_values,
            expert_action=expert_values,
            vla_action=predicted,
            stage=stage,
            config=self._harness_config,
        )
        self._calls += 1
        telemetry = {
            "call_index": self._calls - 1,
            "seed": call_seed,
            "stage": stage,
            "observation_modality": "rgbd" if self._uses_depth_rgb else "rgb",
            "latency_ms": latency_ms,
            "finite": len(predicted) == 19 and all(math.isfinite(value) for value in predicted),
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

    def _reset(self) -> None:
        for component in (self._policy, self._preprocessor, self._postprocessor):
            reset = getattr(component, "reset", None)
            if callable(reset):
                reset()
