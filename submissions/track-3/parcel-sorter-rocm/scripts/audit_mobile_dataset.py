#!/usr/bin/env python3
"""Audit a mobile bimanual LeRobotDataset before policy training."""

from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path

from parcel_sorter.dataset import metric_depth_to_visual_rgb
from parcel_sorter.mobile_dataset import (
    MOBILE_DEPTH_KEY,
    MOBILE_DEPTH_RGB_KEY,
    mobile_policy_visual_keys,
)


def _fixed_list_array(table: object, name: str, width: int, np: object) -> object:
    column = table[name].combine_chunks()
    values = column.values.to_numpy(zero_copy_only=False)
    return np.asarray(values, dtype=np.float32).reshape(-1, width)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-episodes", type=int, default=1)
    parser.add_argument("--policy-modality", choices=("rgb", "rgbd"), default="rgb")
    args = parser.parse_args()
    if args.min_episodes < 1:
        parser.error("min-episodes must be positive")

    import numpy as np
    import pyarrow.parquet as pq
    from PIL import Image

    root = args.dataset_root.resolve()
    info_path = root / "meta/info.json"
    parquet_files = sorted((root / "data").rglob("*.parquet"))
    if not info_path.is_file() or not parquet_files:
        raise FileNotFoundError(f"incomplete mobile dataset: {root}")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    action_feature = info["features"]["action"]
    action_width = int(action_feature["shape"][0])
    action_names = tuple(str(name) for name in action_feature.get("names", ()))
    if action_width not in (19, 20):
        raise ValueError(f"unsupported mobile action width: {action_width}")
    table = pq.read_table(parquet_files)
    policy_input_features = (
        "observation.state",
        *mobile_policy_visual_keys(args.policy_modality),
    )
    states = _fixed_list_array(table, "observation.state", 43, np)
    actions = _fixed_list_array(table, "action", action_width, np)
    stage_ids = np.asarray(
        table["observation.stage_id"].combine_chunks().to_numpy(), dtype=np.int64
    )
    timestamps = np.asarray(
        table["timestamp"].combine_chunks().to_numpy(), dtype=np.float64
    )
    episode_indices = np.asarray(
        table["episode_index"].combine_chunks().to_numpy(), dtype=np.int64
    )
    stage_names = tuple(
        info["features"]["observation.stage_id"]["info"]["stages"]
    )
    stage_counts = {
        name: int(np.count_nonzero(stage_ids == index))
        for index, name in enumerate(stage_names)
    }
    episode_stage_counts = {
        str(episode_index): {
            name: int(
                np.count_nonzero(
                    (episode_indices == episode_index) & (stage_ids == stage_id)
                )
            )
            for stage_id, name in enumerate(stage_names)
        }
        for episode_index in sorted(set(int(value) for value in episode_indices))
    }

    quaternion_slices = (slice(6, 10), slice(14, 18))
    quaternion_norm_error = max(
        float(np.abs(np.linalg.norm(actions[:, indices], axis=1) - 1.0).max())
        for indices in quaternion_slices
    )
    base_speed = np.linalg.norm(actions[:, :2], axis=1)
    tool_values = sorted(
        set(float(value) for value in np.concatenate((actions[:, 10], actions[:, 18])))
    )

    depth_min = math.inf
    depth_max = -math.inf
    depth_values = []
    depth_column = table[MOBILE_DEPTH_KEY].combine_chunks()
    depth_rgb_column = table[MOBILE_DEPTH_RGB_KEY].combine_chunks()
    depth_rgb_check_stride = max(1, len(depth_column) // 64)
    depth_rgb_checked_frames = 0
    depth_rgb_mismatch_count = 0
    for frame_index, item in enumerate(depth_column):
        encoded = item.as_py()["bytes"]
        depth = np.asarray(Image.open(io.BytesIO(encoded)), dtype=np.float32)
        if depth.shape != (224, 224) or not np.isfinite(depth).all():
            raise ValueError("invalid mobile metric depth frame")
        depth_min = min(depth_min, float(depth.min()))
        depth_max = max(depth_max, float(depth.max()))
        depth_values.append(depth.reshape(-1)[::64])
        if frame_index % depth_rgb_check_stride == 0:
            encoded_rgb = depth_rgb_column[frame_index].as_py()["bytes"]
            stored_rgb = np.asarray(Image.open(io.BytesIO(encoded_rgb)), dtype=np.uint8)[..., :3]
            expected_rgb = metric_depth_to_visual_rgb(depth, np)
            depth_rgb_checked_frames += 1
            depth_rgb_mismatch_count += int(
                stored_rgb.shape != expected_rgb.shape
                or not np.array_equal(stored_rgb, expected_rgb)
            )
    depth_sample = np.concatenate(depth_values)
    depth_percentiles = np.percentile(depth_sample, (1, 50, 99)).tolist()

    expected_frames = int(info["total_frames"])
    errors = []
    if int(info["total_episodes"]) < args.min_episodes or len(table) != expected_frames:
        errors.append("episode_or_frame_count")
    if states.shape != (expected_frames, 43) or actions.shape != (
        expected_frames,
        action_width,
    ):
        errors.append("state_action_shape")
    if not np.isfinite(states).all() or not np.isfinite(actions).all():
        errors.append("non_finite_state_or_action")
    if any(count <= 0 for count in stage_counts.values()):
        errors.append("missing_task_stage")
    if any(
        count <= 0
        for counts in episode_stage_counts.values()
        for count in counts.values()
    ):
        errors.append("missing_episode_task_stage")
    for episode_index in sorted(set(int(value) for value in episode_indices)):
        episode_timestamps = timestamps[episode_indices == episode_index]
        if (
            len(episode_timestamps) > 1
            and float(np.abs(np.diff(episode_timestamps) - 1.0 / 30.0).max()) > 1e-4
        ):
            errors.append("timestamp_cadence")
            break
    if float(base_speed.max()) > 0.050001:
        errors.append("base_speed_limit")
    if quaternion_norm_error > 1e-4:
        errors.append("action_quaternion_norm")
    if not set(tool_values).issubset({-1.0, 1.0}):
        errors.append("tool_command_domain")
    if not 0.05 < depth_min < depth_max <= 20.001:
        errors.append("metric_depth_range")
    if depth_rgb_mismatch_count:
        errors.append("derived_depth_rgb_mismatch")
    if any(key not in info["features"] for key in policy_input_features):
        errors.append("missing_policy_input_feature")
    if "observation.privileged_state" in policy_input_features:
        errors.append("privileged_policy_leakage")
    progress_enabled = action_width == 20
    progress = actions[:, 19] if progress_enabled else None
    if progress_enabled and (
        len(action_names) != 20
        or action_names[-1] != "primitive_progress"
        or float(progress.min()) < 0.0
        or float(progress.max()) > 1.0
    ):
        errors.append("primitive_progress_contract")

    payload = {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "dataset_root": str(root),
        "episodes": int(info["total_episodes"]),
        "frames": expected_frames,
        "fps": int(info["fps"]),
        "stage_counts": stage_counts,
        "episode_stage_counts": episode_stage_counts,
        "state_shape": list(states.shape),
        "action_shape": list(actions.shape),
        "primitive_progress_enabled": progress_enabled,
        "primitive_progress_min": float(progress.min()) if progress_enabled else None,
        "primitive_progress_max": float(progress.max()) if progress_enabled else None,
        "base_action_speed_max_m_s": float(base_speed.max()),
        "action_quaternion_norm_error_max": quaternion_norm_error,
        "tool_command_values": tool_values,
        "depth_tiff_unit": "m",
        "depth_min_m": depth_min,
        "depth_max_m": depth_max,
        "depth_percentiles_m": depth_percentiles,
        "depth_rgb_checked_frames": depth_rgb_checked_frames,
        "depth_rgb_mismatch_count": depth_rgb_mismatch_count,
        "policy_modality": args.policy_modality,
        "policy_input_features": list(policy_input_features),
        "privileged_state_in_policy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
