from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from parcel_sorter.config import load_config
from parcel_sorter.dataset import JsonlTrajectoryWriter
from parcel_sorter.episode_plan import build_episode_plan
from parcel_sorter.genesis_env import GenesisParcelEnv
from parcel_sorter.metrics import MetricsAccumulator
from parcel_sorter.policy import LeRobotPolicyAdapter
from parcel_sorter.provenance import runtime_report
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.runner import run_policy_episode, save_episode_writers


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate an ACT, Diffusion, or SmolVLA LeRobot checkpoint in Genesis"
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="configs/baseline.toml")
    parser.add_argument("--backend", choices=("rocm", "cuda"), default="rocm")
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--start-episode", type=int, default=0)
    parser.add_argument(
        "--profile",
        action="append",
        dest="selected_profiles",
        help="evaluate this profile; repeat for matched per-profile evaluation",
    )
    parser.add_argument("--output", default="outputs/eval-act")
    parser.add_argument("--nominal", action="store_true")
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument(
        "--n-action-steps",
        type=int,
        help="override how many predicted actions are executed before replanning",
    )
    parser.add_argument(
        "--action-position-mode",
        choices=("absolute", "delta"),
        default="absolute",
        help="interpret the first three policy outputs as absolute XYZ or XYZ deltas",
    )
    parser.add_argument("--fail-on-unsuccessful", action="store_true")
    args = parser.parse_args()
    if args.episodes < 1 or args.start_episode < 0:
        parser.error("episodes must be positive and start-episode cannot be negative")

    config = load_config(args.config)
    if args.nominal:
        config = replace(config, randomization=replace(config.randomization, enabled=False))
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    writer = JsonlTrajectoryWriter(output / "audit_dataset")
    policy = LeRobotPolicyAdapter(
        args.checkpoint,
        config,
        action_steps_override=args.n_action_steps,
        action_position_mode=args.action_position_mode,
    )
    randomizer = DomainRandomizer(config.randomization, config.seed, config.parcel_profiles)
    try:
        plan = build_episode_plan(
            config.parcel_profiles,
            args.episodes,
            args.start_episode,
            tuple(args.selected_profiles or ()),
        )
    except ValueError as exc:
        parser.error(str(exc))
    metrics = MetricsAccumulator()
    profile_metrics: dict[str, MetricsAccumulator] = {}
    reports = []

    for offset, spec in enumerate(plan):
        episode_index = spec.episode_index
        sample = (
            randomizer.sample(episode_index)
            if spec.profile_id is None
            else randomizer.sample_profile(spec.profile_id, episode_index)
        )
        writer.assert_episode_available(episode_index)
        video_path = None
        if args.record_video or (config.output.record_first_episode and offset == 0):
            video_path = output / "videos" / f"episode_{episode_index:06d}.mp4"
        policy.reset()
        with GenesisParcelEnv(
            config,
            sample,
            backend=args.backend,
            video_path=video_path,
            capture_sensors=True,
        ) as env:
            report = run_policy_episode(
                env,
                config,
                sample,
                episode_index,
                policy,
                (writer,),
            )
        save_episode_writers(report, writer, None)
        reports.append(report.to_dict())
        metrics.add(report.result)
        profile_metrics.setdefault(sample.profile_id, MetricsAccumulator()).add(report.result)
        print(
            json.dumps(
                {
                    "episode": episode_index,
                    "profile": sample.profile_id,
                    "success": report.result.success,
                }
            )
        )

    payload = {
        "runtime": runtime_report(),
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "policy_type": policy.policy_type,
        "n_action_steps_override": args.n_action_steps,
        "action_position_mode": args.action_position_mode,
        "evaluation_range": {
            "start_episode": min(spec.episode_index for spec in plan),
            "end_episode": max(spec.episode_index for spec in plan),
            "num_episodes": len(plan),
            "profile_filter": list(args.selected_profiles or ()),
            "episodes_per_profile": args.episodes if args.selected_profiles else None,
        },
        "config": asdict(config),
        "summary": metrics.summary(),
        "profile_summaries": {
            profile_id: accumulator.summary()
            for profile_id, accumulator in sorted(profile_metrics.items())
        },
        "episodes": reports,
    }
    with (output / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    all_successful = all(report["result"]["success"] for report in reports)
    return 2 if args.fail_on_unsuccessful and not all_successful else 0


if __name__ == "__main__":
    raise SystemExit(main())
