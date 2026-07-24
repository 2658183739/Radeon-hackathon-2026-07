from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from parcel_sorter.config import load_config
from parcel_sorter.dataset import JsonlTrajectoryWriter, LeRobotTrajectoryWriter
from parcel_sorter.genesis_env import GenesisParcelEnv
from parcel_sorter.metrics import MetricsAccumulator
from parcel_sorter.provenance import runtime_report
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.runner import run_expert_episode, save_episode_writers


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic Genesis parcel-sorting expert")
    parser.add_argument("--config", default="configs/baseline.toml")
    parser.add_argument("--backend", choices=("rocm", "cuda", "cpu"), default="rocm")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--start-episode", type=int, default=0)
    parser.add_argument("--output", default=None)
    parser.add_argument("--viewer", action="store_true")
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--lerobot", action="store_true")
    parser.add_argument("--record-sensors", action="store_true")
    parser.add_argument(
        "--nominal",
        action="store_true",
        help="disable domain randomization for deterministic hardware calibration",
    )
    parser.add_argument("--fail-on-unsuccessful", action="store_true")
    args = parser.parse_args()
    if args.episodes < 1 or args.start_episode < 0:
        parser.error("episodes must be positive and start-episode cannot be negative")
    if args.lerobot and not args.record_sensors:
        parser.error("--lerobot requires --record-sensors so RGB-D frames are available")

    config = load_config(args.config)
    if args.nominal:
        config = replace(
            config,
            randomization=replace(config.randomization, enabled=False),
        )
    output = Path(args.output or config.output.root_dir) / "expert"
    output.mkdir(parents=True, exist_ok=True)
    jsonl_writer = JsonlTrajectoryWriter(output / "audit_dataset")
    lerobot_writer = None
    if args.lerobot:
        lerobot_writer = LeRobotTrajectoryWriter(
            root=output / "lerobot_dataset",
            fps=config.simulation.control_hz,
            image_size=(config.sensors.image_width, config.sensors.image_height),
            include_rgb=config.sensors.rgb,
            include_depth=config.sensors.depth,
        )

    metrics = MetricsAccumulator()
    randomizer = DomainRandomizer(config.randomization, config.seed, config.parcel_profiles)
    reports = []
    try:
        for offset in range(args.episodes):
            episode_index = args.start_episode + offset
            sample = randomizer.sample(episode_index)
            should_record_video = args.record_video or (
                config.output.record_first_episode and offset == 0
            )
            capture_sensors = args.record_sensors or config.output.save_sensor_frames
            video_path = (
                output / "videos" / f"episode_{episode_index:06d}.mp4"
                if should_record_video
                else None
            )
            with GenesisParcelEnv(
                config,
                sample,
                backend=args.backend,
                show_viewer=args.viewer,
                video_path=video_path,
                capture_sensors=capture_sensors,
            ) as env:
                writers = tuple(writer for writer in (jsonl_writer, lerobot_writer) if writer is not None)
                report = run_expert_episode(env, config, sample, episode_index, writers)
            save_episode_writers(report, jsonl_writer, lerobot_writer)
            reports.append(report.to_dict())
            metrics.add(report.result)
            print(
                json.dumps(
                    {
                        "episode": episode_index,
                        "success": report.result.success,
                        "stage": report.terminal_stage,
                        "retries": report.result.retries,
                    },
                    ensure_ascii=False,
                )
            )
    finally:
        if lerobot_writer is not None:
            lerobot_writer.finalize()

    result = {
        "runtime": runtime_report(),
        "evaluation_range": {
            "start_episode": args.start_episode,
            "end_episode": args.start_episode + args.episodes - 1,
            "num_episodes": args.episodes,
        },
        "config": asdict(config),
        "summary": metrics.summary(),
        "episodes": reports,
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    all_successful = all(report["result"]["success"] for report in reports)
    return 2 if args.fail_on_unsuccessful and not all_successful else 0


if __name__ == "__main__":
    raise SystemExit(main())
