"""Evaluate one representative frame per task stage with a mobile SmolVLA checkpoint."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics
import time
from typing import Any

from parcel_sorter.mobile_dataset import MOBILE_STAGE_NAMES
from parcel_sorter.mobile_task import decode_mobile_bimanual_action, limit_mobile_arm_step
from parcel_sorter.provenance import runtime_report


def _stage_frame_indices(dataset_root: Path) -> dict[str, int]:
    import pyarrow.parquet as pq

    parquet_files = sorted((dataset_root / "data").rglob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"mobile dataset has no parquet files: {dataset_root}")
    stage_ids: list[int] = []
    for path in parquet_files:
        column = pq.read_table(path, columns=["observation.stage_id"])[
            "observation.stage_id"
        ].combine_chunks()
        for item in column:
            value = item.as_py()
            stage_ids.append(int(value[0] if isinstance(value, list) else value))
    selected: dict[str, int] = {}
    for stage_id, stage_name in enumerate(MOBILE_STAGE_NAMES):
        candidates = [index for index, value in enumerate(stage_ids) if value == stage_id]
        if not candidates:
            raise ValueError(f"dataset contains no frame for stage {stage_name}")
        selected[stage_name] = candidates[len(candidates) // 2]
    return selected


def _batch(sample: dict[str, Any], config: Any, torch: Any) -> dict[str, Any]:
    return {
        key: (value.unsqueeze(0).cuda() if torch.is_tensor(value) else [value])
        for key, value in sample.items()
        if key in config.input_features or key == "task"
    }


def _reset(*components: Any) -> None:
    for component in components:
        reset = getattr(component, "reset", None)
        if callable(reset):
            reset()


def _percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _action_metrics(
    predicted: list[float], expert: list[float], state: list[float]
) -> dict[str, Any]:
    errors = [actual - expected for actual, expected in zip(predicted, expert, strict=True)]
    base_speed = math.hypot(predicted[0], predicted[1])
    quaternion_norms = (
        math.sqrt(sum(value * value for value in predicted[6:10])),
        math.sqrt(sum(value * value for value in predicted[14:18])),
    )
    left_step = math.dist(predicted[3:6], state[24:27])
    right_step = math.dist(predicted[11:14], state[31:34])
    decoded = decode_mobile_bimanual_action(
        predicted,
        max_base_linear_speed_m_s=0.05,
    )
    bounded_left = limit_mobile_arm_step(decoded.left, tuple(state[24:27]))
    bounded_right = limit_mobile_arm_step(decoded.right, tuple(state[31:34]))
    decoded_base_speed = math.hypot(*decoded.base_velocity_xy_yaw[:2])
    return {
        "mae": statistics.fmean(abs(value) for value in errors),
        "mse": statistics.fmean(value * value for value in errors),
        "base_mae": statistics.fmean(abs(value) for value in errors[:3]),
        "left_arm_mae": statistics.fmean(abs(value) for value in errors[3:11]),
        "right_arm_mae": statistics.fmean(abs(value) for value in errors[11:19]),
        "raw_base_linear_speed_m_s": base_speed,
        "raw_base_yaw_rate_rad_s": predicted[2],
        "raw_quaternion_norms": list(quaternion_norms),
        "raw_cartesian_step_m": [left_step, right_step],
        "raw_tool_commands": [predicted[10], predicted[18]],
        "expert_tool_commands": [expert[10], expert[18]],
        "tool_command_sign_match": [
            (predicted[10] >= 0) == (expert[10] >= 0),
            (predicted[18] >= 0) == (expert[18] >= 0),
        ],
        "raw_action_within_expert_envelope": bool(
            base_speed <= 0.050001
            and abs(predicted[2]) <= 1.0
            and max(abs(value - 1.0) for value in quaternion_norms) <= 1e-3
            and max(left_step, right_step) <= 0.040001
            and all(abs(value) <= 1.000001 for value in (predicted[10], predicted[18]))
        ),
        "executor": {
            "accepted": True,
            "base_linear_speed_m_s": decoded_base_speed,
            "base_yaw_rate_rad_s": decoded.base_velocity_xy_yaw[2],
            "left_cartesian_step_m": math.dist(
                bounded_left.position_m, tuple(state[24:27])
            ),
            "right_cartesian_step_m": math.dist(
                bounded_right.position_m, tuple(state[31:34])
            ),
            "tool_commands": [decoded.left.gripper, decoded.right.gripper],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()

    import torch
    from lerobot.configs.policies import PreTrainedConfig
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from lerobot.policies import make_pre_post_processors
    from lerobot.policies.factory import get_policy_class

    config = PreTrainedConfig.from_pretrained(args.checkpoint, local_files_only=True)
    if config.input_features["observation.state"].shape != (43,):
        raise RuntimeError("checkpoint does not use the audited 43-D mobile state")
    if config.output_features["action"].shape != (19,):
        raise RuntimeError("checkpoint does not produce the audited 19-D mobile action")
    config.device = "cuda"
    config.n_action_steps = 1
    policy = get_policy_class(config.type).from_pretrained(
        args.checkpoint,
        config=config,
        local_files_only=True,
    ).eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy.config,
        pretrained_path=str(args.checkpoint),
    )
    dataset = LeRobotDataset(
        "local/mobile-bimanual-parcel-expert",
        root=args.dataset_root,
        depth_output_unit="m",
    )
    selected = _stage_frame_indices(args.dataset_root)

    # Warm model kernels once; all reported stage timings are warm inference timings.
    warm_sample = dataset[selected[MOBILE_STAGE_NAMES[0]]]
    torch.manual_seed(args.seed - 1)
    torch.cuda.manual_seed_all(args.seed - 1)
    _reset(policy, preprocessor, postprocessor)
    with torch.inference_mode():
        policy.select_action(preprocessor(_batch(warm_sample, config, torch)))
        torch.cuda.synchronize()

    stage_results = []
    for stage_id, stage_name in enumerate(MOBILE_STAGE_NAMES):
        frame_index = selected[stage_name]
        sample = dataset[frame_index]
        stage_seed = args.seed + stage_id
        torch.manual_seed(stage_seed)
        torch.cuda.manual_seed_all(stage_seed)
        _reset(policy, preprocessor, postprocessor)
        batch = _batch(sample, config, torch)
        with torch.inference_mode():
            torch.cuda.synchronize()
            started = time.perf_counter()
            action = postprocessor(policy.select_action(preprocessor(batch)))
            torch.cuda.synchronize()
            latency_ms = (time.perf_counter() - started) * 1000.0
        predicted = [float(value) for value in action.detach().cpu().reshape(-1)]
        expert = [float(value) for value in sample["action"].reshape(-1)]
        state = [float(value) for value in sample["observation.state"].reshape(-1)]
        finite = len(predicted) == 19 and all(math.isfinite(value) for value in predicted)
        result: dict[str, Any] = {
            "stage": stage_name,
            "seed": stage_seed,
            "frame_index": frame_index,
            "latency_ms": latency_ms,
            "action_shape": list(action.shape),
            "finite": finite,
        }
        if finite:
            try:
                result.update(_action_metrics(predicted, expert, state))
            except ValueError as exc:
                result["executor"] = {"accepted": False, "error": str(exc)}
        stage_results.append(result)

    latencies = [float(item["latency_ms"]) for item in stage_results]
    valid = all(
        item["finite"]
        and item["action_shape"] == [1, 19]
        and item.get("executor", {}).get("accepted", False)
        for item in stage_results
    )
    raw_envelope_pass_count = sum(
        bool(item.get("raw_action_within_expert_envelope")) for item in stage_results
    )
    payload = {
        "schema_version": 2,
        "status": (
            "passed_six_stage_raw_envelope"
            if valid and raw_envelope_pass_count == len(MOBILE_STAGE_NAMES)
            else "passed_six_stage_requires_safety_clipping"
            if valid
            else "failed"
        ),
        "runtime": runtime_report(),
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "policy_type": config.type,
        "state_shape": list(config.input_features["observation.state"].shape),
        "action_shape": list(config.output_features["action"].shape),
        "max_state_dim": int(config.max_state_dim),
        "max_action_dim": int(config.max_action_dim),
        "selection": "middle frame of each audited task stage; policy queue reset per stage",
        "base_seed": args.seed,
        "latency_ms": {
            "mean": statistics.fmean(latencies),
            "p95": _percentile_95(latencies),
            "maximum": max(latencies),
        },
        "offline_action_error": {
            "mean_stage_mae": statistics.fmean(
                float(item["mae"]) for item in stage_results
            ),
            "mean_stage_mse": statistics.fmean(
                float(item["mse"]) for item in stage_results
            ),
        },
        "stages": stage_results,
        "raw_action_envelope_pass_count": raw_envelope_pass_count,
        "claim_boundary": (
            "six-stage offline checkpoint evaluation on one expert episode; "
            "not closed-loop task success or generalization"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
