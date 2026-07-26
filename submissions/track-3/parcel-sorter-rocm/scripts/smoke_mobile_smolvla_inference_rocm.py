"""Reload a mobile SmolVLA checkpoint and verify its 19-D action on ROCm."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from parcel_sorter.provenance import runtime_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
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
    )
    sample = dataset[0]
    batch = {
        key: (value.unsqueeze(0).cuda() if torch.is_tensor(value) else [value])
        for key, value in sample.items()
        if key in config.input_features or key == "task"
    }
    with torch.inference_mode():
        torch.cuda.synchronize()
        started = time.perf_counter()
        action = postprocessor(policy.select_action(preprocessor(batch)))
        torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - started) * 1000.0

    payload = {
        "runtime": runtime_report(),
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "policy_type": config.type,
        "state_shape": list(config.input_features["observation.state"].shape),
        "action_shape": list(action.shape),
        "max_state_dim": int(config.max_state_dim),
        "max_action_dim": int(config.max_action_dim),
        "finite": bool(torch.isfinite(action).all()),
        "cold_inference_latency_ms": latency_ms,
        "claim_boundary": "one-frame checkpoint reload smoke; not a task success rate",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if payload["finite"] and payload["action_shape"] == [1, 19] else 2


if __name__ == "__main__":
    raise SystemExit(main())
