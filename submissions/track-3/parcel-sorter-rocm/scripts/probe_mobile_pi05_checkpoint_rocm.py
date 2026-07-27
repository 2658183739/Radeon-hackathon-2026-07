#!/usr/bin/env python3
"""Load a PI0.5 LoRA checkpoint and run one mobile Harness inference."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lerobot.datasets.lerobot_dataset import LeRobotDataset

from parcel_sorter.mobile_vla_controller import MobileVLAHarnessController


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    import torch

    dataset = LeRobotDataset(
        "local/mobile-bimanual-parcel-expert",
        root=args.dataset,
    )
    frame = dataset[0]
    rgb = (
        frame["observation.images.overhead_rgb"]
        .permute(1, 2, 0)
        .mul(255.0)
        .clamp(0.0, 255.0)
        .byte()
        .numpy()
    )
    state = frame["observation.state"].tolist()
    expert_action = frame["action"][:19].tolist()

    torch.cuda.reset_peak_memory_stats()
    controller = MobileVLAHarnessController(args.checkpoint)
    selected, telemetry = controller.select(
        rgb=rgb,
        state=state,
        task=str(frame["task"]),
        expert_action=expert_action,
        stage="pregrasp",
    )
    summary = {
        "policy_type": controller.policy_type,
        "checkpoint": str(args.checkpoint.resolve()),
        "dataset": str(args.dataset.resolve()),
        "output_dim": len(selected),
        "finite": all(math.isfinite(value) for value in selected),
        "latency_ms": telemetry["latency_ms"],
        "selected_scale": telemetry["selected_scale"],
        "fallback_to_expert": telemetry["fallback_to_expert"],
        "peak_vram_bytes": torch.cuda.max_memory_allocated(),
    }
    if summary["policy_type"] != "pi05" or summary["output_dim"] != 19 or not summary["finite"]:
        raise RuntimeError(f"PI0.5 checkpoint probe failed: {summary}")
    payload = json.dumps(summary, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
