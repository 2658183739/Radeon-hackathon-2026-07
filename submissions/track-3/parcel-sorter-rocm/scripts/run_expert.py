from __future__ import annotations

import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from parcel_sorter.collection_plan import load_collection_requests
from parcel_sorter.config import load_config
from parcel_sorter.dataset import JsonlTrajectoryWriter, LeRobotTrajectoryWriter
from parcel_sorter.episode_plan import build_episode_plan, build_profile_episode_plan
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
    parser.add_argument(
        "--profile",
        action="append",
        dest="selected_profiles",
        help="collect this training profile; repeat for balanced per-profile collection",
    )
    parser.add_argument(
        "--collection-plan",
        help="frozen JSON from plan_balanced_collection.py; supports per-profile episode counts",
    )
    parser.add_argument(
        "--allow-unready-collection",
        action="store_true",
        help="acknowledge that a plan contains profiles requiring expert diagnostics",
    )
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
    parser.add_argument(
        "--reset-qpos",
        type=float,
        nargs=9,
        metavar=("J1", "J2", "J3", "J4", "J5", "J6", "J7", "F1", "F2"),
        help="override the nine-joint reset pose for a controlled diagnostic",
    )
    parser.add_argument(
        "--size-aware-approach",
        action="store_true",
        help="enable geometry-aware horizontal-transit clearance for a controlled diagnostic",
    )
    parser.add_argument(
        "--approach-clearance-margin",
        type=float,
        default=None,
        help="add a fixed metres margin to size-aware transit clearance",
    )
    parser.add_argument(
        "--retry-retreat-distance",
        type=float,
        default=None,
        help="retreat this many metres laterally before a post-failure retry approach",
    )
    parser.add_argument(
        "--approach-step",
        type=float,
        default=None,
        help="limit every MOVE_PREGRASP Cartesian step for a controlled diagnostic",
    )
    parser.add_argument(
        "--approach-contact-brake-force",
        type=float,
        default=None,
        help="enable approach contact braking at this measured force threshold",
    )
    parser.add_argument(
        "--approach-contact-brake-step",
        type=float,
        default=None,
        help="maximum Cartesian retreat step used by approach contact braking",
    )
    parser.add_argument(
        "--approach-barrier-recovery-step",
        type=float,
        default=None,
        help="allow a larger vertical-only recovery step below the approach barrier",
    )
    parser.add_argument(
        "--precontact-aabb-guard-distance",
        type=float,
        default=None,
        help="enable the Genesis finger/parcel AABB pre-contact guard at this distance",
    )
    parser.add_argument(
        "--approach-stiffness-scale",
        type=float,
        default=None,
        help="scale approach arm Kp and preserve damping ratio by scaling Kv by sqrt(scale)",
    )
    args = parser.parse_args()
    if args.episodes < 1 or args.start_episode < 0:
        parser.error("episodes must be positive and start-episode cannot be negative")
    if args.lerobot and not args.record_sensors:
        parser.error("--lerobot requires --record-sensors so RGB-D frames are available")
    if args.collection_plan and args.selected_profiles:
        parser.error("--collection-plan cannot be combined with repeated --profile")

    config = load_config(args.config)
    if args.nominal:
        config = replace(
            config,
            randomization=replace(config.randomization, enabled=False),
        )
    if args.reset_qpos is not None:
        config = replace(
            config,
            control=replace(config.control, reset_qpos=tuple(args.reset_qpos)),
        )
    if (
        args.size_aware_approach
        or args.approach_clearance_margin is not None
        or args.retry_retreat_distance is not None
        or args.approach_step is not None
        or args.approach_contact_brake_force is not None
        or args.approach_contact_brake_step is not None
        or args.approach_barrier_recovery_step is not None
        or args.precontact_aabb_guard_distance is not None
        or args.approach_stiffness_scale is not None
    ):
        config = replace(
            config,
            task=replace(
                config.task,
                size_aware_approach_enabled=(
                    config.task.size_aware_approach_enabled or args.size_aware_approach
                ),
                approach_clearance_margin_m=(
                    config.task.approach_clearance_margin_m
                    if args.approach_clearance_margin is None
                    else args.approach_clearance_margin
                ),
                retry_retreat_distance_m=(
                    config.task.retry_retreat_distance_m
                    if args.retry_retreat_distance is None
                    else args.retry_retreat_distance
                ),
            ),
            control=replace(
                config.control,
                approach_contact_brake_force_n=(
                    config.control.approach_contact_brake_force_n
                    if args.approach_contact_brake_force is None
                    else args.approach_contact_brake_force
                ),
                approach_contact_brake_step_m=(
                    config.control.approach_contact_brake_step_m
                    if args.approach_contact_brake_step is None
                    else args.approach_contact_brake_step
                ),
                approach_barrier_recovery_step_m=(
                    config.control.approach_barrier_recovery_step_m
                    if args.approach_barrier_recovery_step is None
                    else args.approach_barrier_recovery_step
                ),
                precontact_aabb_guard_distance_m=(
                    config.control.precontact_aabb_guard_distance_m
                    if args.precontact_aabb_guard_distance is None
                    else args.precontact_aabb_guard_distance
                ),
                approach_stiffness_scale=(
                    config.control.approach_stiffness_scale
                    if args.approach_stiffness_scale is None
                    else args.approach_stiffness_scale
                ),
            ),
        )
    if args.approach_step is not None:
        config = replace(
            config,
            control=replace(config.control, approach_step_m=args.approach_step),
        )
    try:
        config.validate()
    except ValueError as exc:
        parser.error(str(exc))
    try:
        if args.collection_plan:
            requests = load_collection_requests(
                args.collection_plan,
                allow_unready=args.allow_unready_collection,
                expected_training_profile_ids=tuple(
                    profile.profile_id
                    for profile in config.parcel_profiles
                    if not profile.evaluation_only
                ),
                expected_config_path=args.config,
            )
            plan = build_profile_episode_plan(
                config.parcel_profiles,
                requests,
                allow_evaluation_only=False,
            )
        else:
            plan = build_episode_plan(
                config.parcel_profiles,
                args.episodes,
                args.start_episode,
                tuple(args.selected_profiles or ()),
                allow_evaluation_only=False,
            )
    except ValueError as exc:
        parser.error(str(exc))

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
    profile_metrics: dict[str, MetricsAccumulator] = {}
    try:
        for offset, spec in enumerate(plan):
            episode_index = spec.episode_index
            sample = (
                randomizer.sample(episode_index)
                if spec.profile_id is None
                else randomizer.sample_profile(spec.profile_id, episode_index)
            )
            jsonl_writer.assert_episode_available(episode_index)
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
            profile_metrics.setdefault(sample.profile_id, MetricsAccumulator()).add(report.result)
            print(
                json.dumps(
                    {
                        "episode": episode_index,
                        "profile": sample.profile_id,
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
            "start_episode": min(spec.episode_index for spec in plan),
            "end_episode": max(spec.episode_index for spec in plan),
            "num_episodes": len(plan),
            "profile_filter": list(args.selected_profiles or ()),
            "episodes_per_profile": args.episodes if args.selected_profiles else None,
            "collection_plan": args.collection_plan,
            "profile_episode_counts": {
                profile_id: sum(spec.profile_id == profile_id for spec in plan)
                for profile_id in sorted({spec.profile_id for spec in plan if spec.profile_id})
            },
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
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    all_successful = all(report["result"]["success"] for report in reports)
    return 2 if args.fail_on_unsuccessful and not all_successful else 0


if __name__ == "__main__":
    raise SystemExit(main())
