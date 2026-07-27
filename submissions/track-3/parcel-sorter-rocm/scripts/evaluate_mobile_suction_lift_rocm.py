"""Verify physical tri-cup contact, compliant attachment, and parcel lift."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics

from parcel_sorter.genesis_env import initialize_genesis
from parcel_sorter.mobile_dataset import MobileBimanualFrame, MobileBimanualLeRobotWriter
from parcel_sorter.mobile_dual_arm_projection import (
    project_dual_arm_residuals,
    transport_arm_authority,
)
from parcel_sorter.mobile_harness import (
    MobileHarnessConfig,
    transport_deadline_requires_expert,
)
from parcel_sorter.mobile_cradle import MobileVCradleMonitor
from parcel_sorter.mobile_bimanual import (
    ARM_JOINT_NAMES,
    BASE_JOINT_NAMES,
    END_EFFECTOR_LINK_NAMES,
    FINGER_JOINT_NAMES,
    build_mobile_bimanual_mjcf,
    joint_dof_indices,
)
from parcel_sorter.mobile_suction import MobileTriSuctionController
from parcel_sorter.mobile_task import (
    clamp_position_residual_to_anchor,
    placement_within_release_gate,
)
from parcel_sorter.mobile_vla_controller import MobileSmolVLAHarnessController
from parcel_sorter.provenance import runtime_report
from parcel_sorter.suction import rotate_vector


def _flat(values: object) -> list[float]:
    if hasattr(values, "detach"):
        values = values.detach().cpu()  # type: ignore[union-attr]
    if hasattr(values, "reshape"):
        values = values.reshape(-1)  # type: ignore[union-attr]
    return [float(value) for value in values]  # type: ignore[union-attr]


def _normalized(values: object, np: object) -> object:
    vector = np.asarray(values, dtype=np.float64)
    norm = float(np.linalg.norm(vector))
    if norm <= 1e-8:
        raise RuntimeError("tool axis has zero length")
    return vector / norm


def _box_ray_extent(axis: object, box_size: object) -> float:
    """Distance from an axis-aligned box centre to the face hit by a ray."""

    intersections = [
        float(size) / (2.0 * abs(float(component)))
        for component, size in zip(axis, box_size, strict=True)  # type: ignore[arg-type]
        if abs(float(component)) > 1e-9
    ]
    if not intersections:
        raise ValueError("box approach axis has no finite component")
    return min(intersections)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=("rocm", "cuda"), default="rocm")
    parser.add_argument("--output", type=Path, default=Path("outputs/mobile-suction-lift"))
    parser.add_argument(
        "--record-dataset",
        type=Path,
        help="record the successful full task as a 30 Hz RGB-D LeRobot episode",
    )
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--parcel-profile", default="carton")
    parser.add_argument(
        "--parcel-size-m", type=float, nargs=3, default=(0.20, 0.12, 0.20)
    )
    parser.add_argument("--parcel-mass-kg", type=float, default=0.40)
    parser.add_argument("--parcel-friction", type=float, default=0.80)
    parser.add_argument("--parcel-offset-m", type=float, nargs=2, default=(0.0, 0.0))
    parser.add_argument(
        "--cooperative-cradle",
        action="store_true",
        help="synchronize the right V cradle for wide-parcel lift, transport, and place",
    )
    parser.add_argument("--task-text")
    parser.add_argument("--smolvla-checkpoint", type=Path)
    parser.add_argument(
        "--force-memory-harness",
        action="store_true",
        help="cap SmolVLA residual scale using short contact-force history",
    )
    parser.add_argument(
        "--policy-mode",
        choices=(
            "shadow",
            "base_residual",
            "base_arm_residual",
            "base_dual_arm_residual",
        ),
        default="shadow",
    )
    parser.add_argument(
        "--depth-risk-sidecar",
        action="store_true",
        help="use metric depth as a deterministic Harness scale gate for the RGB policy",
    )
    parser.add_argument("--policy-hz", type=int, default=5)
    args = parser.parse_args()
    if args.image_size < 32:
        parser.error("image-size must be at least 32")
    max_parcel_dimension_m = 1.70 if args.cooperative_cradle else 0.60
    if any(not 0.02 <= value <= max_parcel_dimension_m for value in args.parcel_size_m):
        parser.error(
            f"parcel dimensions must be in [0.02, {max_parcel_dimension_m:.2f}] m"
        )
    if not 0.05 <= args.parcel_mass_kg <= 5.0:
        parser.error("parcel mass must be in [0.05, 5.0] kg")
    if not 0.1 <= args.parcel_friction <= 2.0:
        parser.error("parcel friction must be in [0.1, 2.0]")
    if any(abs(value) > 0.025 for value in args.parcel_offset_m):
        parser.error("parcel XY offsets must be within 0.025 m")
    if args.policy_hz <= 0 or 30 % args.policy_hz != 0:
        parser.error("policy-hz must be a positive divisor of 30")
    if args.policy_mode != "shadow" and args.smolvla_checkpoint is None:
        parser.error("residual policy modes require --smolvla-checkpoint")
    if args.cooperative_cradle and args.parcel_size_m[0] < 0.28:
        parser.error("cooperative cradle requires parcel X dimension >= 0.28 m")
    if args.cooperative_cradle and args.policy_mode == "base_arm_residual":
        parser.error("cooperative cradle is not compatible with left-arm residual ablation")

    gs, torch, np = initialize_genesis(args.backend)
    source = Path(gs.__file__).resolve().parent / "assets/xml/franka_sim/bi-franka_panda.xml"
    asset = build_mobile_bimanual_mjcf(
        source,
        args.output / "mobile_bi_franka.xml",
        left_tri_suction=True,
        right_v_cradle=True,
    )
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1.0 / 240.0, substeps=1),
        rigid_options=gs.options.RigidOptions(enable_collision=True),
        show_viewer=False,
    )
    scene.add_entity(gs.morphs.Plane())
    pedestal_position = np.asarray(
        (0.0, 0.7500, 1.3000)
        if args.cooperative_cradle
        else (-0.6800, 0.7500, 1.3000)
    )
    transport_delta = np.asarray((0.3000, 0.0, 0.0))
    destination_pedestal_position = pedestal_position + transport_delta
    parcel_size = np.asarray(args.parcel_size_m, dtype=np.float64)
    parcel_support_z = pedestal_position[2] + 0.05 + parcel_size[2] / 2.0
    initial_parcel_position = np.asarray(
        (
            pedestal_position[0] + args.parcel_offset_m[0],
            pedestal_position[1] + args.parcel_offset_m[1],
            parcel_support_z + 0.002,
        )
    )
    pedestal_size_x = (
        max(0.16, float(parcel_size[0]) + 0.04)
        if args.cooperative_cradle
        else 0.16
    )
    scene.add_entity(
        gs.morphs.Box(
            size=(pedestal_size_x, 0.08, 0.10),
            pos=tuple(pedestal_position.tolist()),
            fixed=True,
        )
    )
    scene.add_entity(
        gs.morphs.Box(
            size=(pedestal_size_x, 0.08, 0.10),
            pos=tuple(destination_pedestal_position.tolist()),
            fixed=True,
        )
    )
    parcel = scene.add_entity(
        gs.morphs.Box(
            size=tuple(parcel_size.tolist()),
            pos=tuple(initial_parcel_position.tolist()),
        ),
        material=gs.materials.Rigid(friction=args.parcel_friction),
    )
    robot = scene.add_entity(gs.morphs.MJCF(file=str(asset)))
    camera = None
    if args.record_dataset is not None or args.smolvla_checkpoint is not None:
        camera = scene.add_camera(
            res=(args.image_size, args.image_size),
            pos=(0.0, -2.4, 3.1),
            lookat=(-0.45, 0.65, 1.25),
            fov=52,
            GUI=False,
        )
    scene.build()
    parcel.set_mass(args.parcel_mass_kg)

    base_dofs = np.asarray(joint_dof_indices(robot, BASE_JOINT_NAMES))
    left_arm_dofs = np.asarray(joint_dof_indices(robot, ARM_JOINT_NAMES["left"]))
    right_arm_dofs = np.asarray(joint_dof_indices(robot, ARM_JOINT_NAMES["right"]))
    arm_dofs = np.asarray((*left_arm_dofs.tolist(), *right_arm_dofs.tolist()))
    left_finger_dofs = np.asarray(joint_dof_indices(robot, FINGER_JOINT_NAMES["left"]))
    right_finger_dofs = np.asarray(joint_dof_indices(robot, FINGER_JOINT_NAMES["right"]))
    finger_dofs = np.asarray((*left_finger_dofs.tolist(), *right_finger_dofs.tolist()))
    hand = robot.get_link(END_EFFECTOR_LINK_NAMES["left"])
    robot.set_dofs_kp(np.zeros(3), base_dofs)
    robot.set_dofs_kv(np.asarray((600.0, 600.0, 300.0)), base_dofs)
    robot.set_dofs_force_range(
        np.asarray((-2500.0, -2500.0, -1200.0)),
        np.asarray((2500.0, 2500.0, 1200.0)),
        base_dofs,
    )
    robot.set_dofs_kp(
        np.asarray((4500.0, 4500.0, 3500.0, 3500.0, 2000.0, 2000.0, 2000.0) * 2),
        arm_dofs,
    )
    robot.set_dofs_kv(
        np.asarray((450.0, 450.0, 350.0, 350.0, 200.0, 200.0, 200.0) * 2),
        arm_dofs,
    )
    robot.set_dofs_force_range(-np.ones(14) * 90.0, np.ones(14) * 90.0, arm_dofs)
    robot.set_dofs_kp(np.ones(4) * 100.0, finger_dofs)
    robot.set_dofs_kv(np.ones(4) * 10.0, finger_dofs)
    neutral = np.asarray((0.0, -0.35, 0.0, -2.10, 0.0, 1.75, 0.785))
    qpos = np.asarray(_flat(robot.get_qpos()))
    qpos[arm_dofs] = np.tile(neutral, 2)
    qpos[finger_dofs] = 0.04
    robot.set_qpos(qpos)
    robot.control_dofs_position(np.tile(neutral, 2), arm_dofs)
    robot.control_dofs_position(np.ones(4) * 0.04, finger_dofs)
    for _ in range(120):
        scene.step()

    hand_position = np.asarray(_flat(hand.get_pos()))
    hand_quaternion = tuple(_flat(hand.get_quat()))
    tool_axis = _normalized(rotate_vector(hand_quaternion, (0.0, 0.0, 1.0)), np)
    parcel_half_extent_on_axis = _box_ray_extent(tool_axis, parcel_size)
    cup_tip_offset_m = 0.112
    cradle_tip_offset_m = 0.270
    cooperative_contact_penetration_m = 0.006
    planned_parcel_position = hand_position + tool_axis * (
        cup_tip_offset_m + parcel_half_extent_on_axis
    )
    parcel_spawn = initial_parcel_position
    settle_trace = []
    settled_parcel_position = parcel_spawn.copy()
    settled_velocity = np.zeros(6)
    for window in range(12):
        for _ in range(120):
            scene.step()
        settled_parcel_position = np.asarray(_flat(parcel.get_pos()))
        settled_velocity = np.asarray(_flat(parcel.get_dofs_velocity()))
        linear_speed = float(np.linalg.norm(settled_velocity[:3]))
        supported = bool(settled_parcel_position[2] >= parcel_support_z - 0.025)
        settle_trace.append(
            {
                "window": window + 1,
                "position_m": settled_parcel_position.tolist(),
                "linear_speed_m_s": linear_speed,
                "supported": supported,
            }
        )
        if supported and linear_speed <= 0.01:
            break
    settle_position_error_m = float(np.linalg.norm(settled_parcel_position - parcel_spawn))
    settle_linear_speed_m_s = float(np.linalg.norm(settled_velocity[:3]))
    scene_stable = bool(
        math.isfinite(settle_position_error_m)
        and math.isfinite(settle_linear_speed_m_s)
        and settled_parcel_position[2] >= parcel_support_z - 0.025
        and settle_linear_speed_m_s <= 0.01
    )

    left_hand = hand
    right_hand = robot.get_link(END_EFFECTOR_LINK_NAMES["right"])
    pregrasp_start_positions = (
        np.asarray(_flat(left_hand.get_pos())),
        np.asarray(_flat(right_hand.get_pos())),
    )
    pregrasp_quaternions = (
        np.asarray(_flat(left_hand.get_quat())),
        np.asarray(_flat(right_hand.get_quat())),
    )
    left_contact_lateral_offset = np.zeros(3)
    right_cradle_contact_target = None
    left_pregrasp_tcp_target = None
    right_pregrasp_tcp_target = None
    if args.cooperative_cradle:
        cooperative_span_m = float(parcel_size[0]) * 0.5 - 0.04
        left_contact_lateral_offset = np.asarray((-cooperative_span_m, 0.0, 0.0))
        right_contact_lateral_offset = np.asarray((cooperative_span_m, 0.0, 0.0))
        right_tool_axis = _normalized(
            rotate_vector(tuple(pregrasp_quaternions[1].tolist()), (0.0, 0.0, 1.0)),
            np,
        )
        right_half_extent_on_axis = _box_ray_extent(right_tool_axis, parcel_size)
        left_contact_surface = (
            settled_parcel_position
            + left_contact_lateral_offset
            - tool_axis
            * (parcel_half_extent_on_axis - cooperative_contact_penetration_m)
        )
        right_contact_surface = (
            settled_parcel_position
            + right_contact_lateral_offset
            - right_tool_axis
            * (right_half_extent_on_axis - cooperative_contact_penetration_m)
        )
        left_pregrasp_tcp_target = left_contact_surface - tool_axis * 0.040
        right_pregrasp_tcp_target = right_contact_surface - right_tool_axis * 0.040
        right_cradle_contact_target = (
            right_contact_surface - right_tool_axis * cradle_tip_offset_m
        )
        pregrasp_targets = (
            left_pregrasp_tcp_target - tool_axis * cup_tip_offset_m,
            right_pregrasp_tcp_target - right_tool_axis * cradle_tip_offset_m,
        )
    else:
        center_y = 0.5 * (
            pregrasp_start_positions[0][1] + pregrasp_start_positions[1][1]
        )
        left_pregrasp_target = pregrasp_start_positions[0] + np.asarray(
            (0.08, 0.20 * (center_y - pregrasp_start_positions[0][1]), -0.08)
        )
        # The base supplies the final horizontal approach; align the suction array
        # with the settled parcel centre once so the arm can hold a fixed IK branch.
        left_pregrasp_target[2] = settled_parcel_position[2] - tool_axis[2] * (
            cup_tip_offset_m + parcel_half_extent_on_axis + 0.040
        )
        pregrasp_targets = (
            left_pregrasp_target,
            pregrasp_start_positions[1]
            + np.asarray(
                (-0.08, 0.20 * (center_y - pregrasp_start_positions[1][1]), -0.08)
            ),
        )
    pregrasp_init_qpos = np.asarray(_flat(robot.get_qpos()))
    if args.cooperative_cradle:
        pregrasp_solution = robot.inverse_kinematics_multilink(
            links=(left_hand, right_hand),
            poss=(left_pregrasp_tcp_target, right_pregrasp_tcp_target),
            quats=pregrasp_quaternions,
            local_points=(
                np.asarray((0.0, 0.0, cup_tip_offset_m)),
                np.asarray((0.0, 0.0, cradle_tip_offset_m)),
            ),
            init_qpos=pregrasp_init_qpos,
            respect_joint_limit=True,
            max_samples=12,
            max_solver_iters=80,
            damping=0.02,
            max_step_size=0.15,
            dofs_idx_local=arm_dofs,
        )
        pregrasp_values = np.asarray(_flat(pregrasp_solution))
    else:
        pregrasp_solution = robot.inverse_kinematics_multilink(
            links=(left_hand, right_hand),
            poss=pregrasp_targets,
            quats=pregrasp_quaternions,
            init_qpos=pregrasp_init_qpos,
            respect_joint_limit=True,
            max_samples=12,
            max_solver_iters=50,
            damping=0.02,
            max_step_size=0.25,
            dofs_idx_local=arm_dofs,
        )
        pregrasp_values = np.asarray(_flat(pregrasp_solution))
    cradle_monitor = (
        MobileVCradleMonitor(robot=robot, parcel=parcel, torch=torch)
        if args.cooperative_cradle
        else None
    )
    cradle_lift_contact_steps = 0
    cradle_transport_contact_steps = 0
    cradle_place_contact_steps = 0
    cradle_lift_steps = 0
    cradle_transport_steps = 0
    cradle_place_steps = 0
    cooperative_lift_ik_attempts = 0
    cooperative_lift_ik_accepts = 0
    cooperative_lift_ik_rejections = 0
    cooperative_place_ik_attempts = 0
    cooperative_place_ik_accepts = 0
    cooperative_place_ik_rejections = 0
    cradle_engage_steps = 0
    cradle_engage_contact_steps = 0
    cradle_engaged_before_lift = False
    writer = None
    if args.record_dataset is not None:
        writer = MobileBimanualLeRobotWriter(
            args.record_dataset,
            fps=30,
            image_size=(args.image_size, args.image_size),
            include_depth=True,
        )
    recorded_frames = 0
    recorded_physics_steps = 0
    task_text = args.task_text or (
        f"Classify the {args.parcel_profile} parcel, pick it with tri-suction, "
        f"transport it to the {args.parcel_profile} sorting station, and place it safely."
    )
    harness_config = MobileHarnessConfig(
        min_progress_ratio=0.75 if args.cooperative_cradle else 0.50
    )
    transport_capacity_ratio = 0.60 if args.cooperative_cradle else 0.75
    policy_controller = (
        MobileSmolVLAHarnessController(
            args.smolvla_checkpoint,
            harness_config=harness_config,
            force_memory_enabled=args.force_memory_harness,
            depth_sidecar_enabled=args.depth_risk_sidecar,
        )
        if args.smolvla_checkpoint is not None
        else None
    )
    policy_stride_frames = 30 // args.policy_hz
    policy_trace: list[dict[str, object]] = []
    latest_policy_action: tuple[float, ...] | None = None
    latest_policy_stage: str | None = None
    policy_applied_physics_steps = 0
    latest_policy_left_arm_qpos = None
    latest_policy_dual_arm_qpos = None
    latest_policy_arm_stage: str | None = None
    transport_arm_anchor_position = None
    transport_arm_anchor_quaternion = None
    transport_right_arm_anchor_position = None
    transport_right_arm_anchor_quaternion = None
    transport_arm_anchor_base = None
    arm_policy_update_attempts = 0
    arm_policy_update_accepts = 0
    arm_policy_update_rejections = 0
    arm_policy_applied_physics_steps = 0

    def record_control_frame(
        *,
        stage: str,
        base_action: object,
        left_position: object,
        left_quaternion: object,
        left_tool_command: float,
        right_position: object,
        right_quaternion: object,
        right_tool_command: float,
        suction_controller: object | None = None,
        policy_expert_base_action: object | None = None,
        policy_remaining_distance_m: float | None = None,
    ) -> None:
        nonlocal recorded_frames, recorded_physics_steps
        nonlocal latest_policy_action, latest_policy_stage
        nonlocal latest_policy_left_arm_qpos, latest_policy_dual_arm_qpos
        nonlocal latest_policy_arm_stage
        nonlocal arm_policy_update_attempts, arm_policy_update_accepts
        nonlocal arm_policy_update_rejections
        if writer is None and policy_controller is None:
            return
        recorded_physics_steps += 1
        if recorded_physics_steps % 8 != 0:
            return
        if camera is None:
            raise RuntimeError("mobile observation requires an RGB-D camera")
        left_contact_force_n = 0.0
        right_contact_force_n = 0.0
        if suction_controller is not None:
            _, left_contact_force_n = suction_controller.contact_snapshot()
        if cradle_monitor is not None:
            _, right_contact_force_n = cradle_monitor.snapshot()
        rgb, depth, _, _ = camera.render(rgb=True, depth=True)
        current_qpos = np.asarray(_flat(robot.get_qpos()))
        base_velocity = _flat(robot.get_dofs_velocity(base_dofs))
        left_pose = (*_flat(left_hand.get_pos()), *_flat(left_hand.get_quat()))
        right_pose = (*_flat(right_hand.get_pos()), *_flat(right_hand.get_quat()))
        parcel_pose = (*_flat(parcel.get_pos()), *_flat(parcel.get_quat()))
        state_vector = (
            *current_qpos[base_dofs].tolist(),
            *base_velocity,
            *current_qpos[left_arm_dofs].tolist(),
            *current_qpos[left_finger_dofs].tolist(),
            *current_qpos[right_arm_dofs].tolist(),
            *current_qpos[right_finger_dofs].tolist(),
            *left_pose,
            *right_pose,
            left_contact_force_n,
            right_contact_force_n,
            float(destination_pedestal_position[0]),
            float(destination_pedestal_position[1]),
            0.0,
        )
        expert_base_action = (
            base_action
            if policy_expert_base_action is None
            else policy_expert_base_action
        )
        action_vector = (
            *_flat(expert_base_action),
            *_flat(left_position),
            *_flat(left_quaternion),
            float(left_tool_command),
            *_flat(right_position),
            *_flat(right_quaternion),
            float(right_tool_command),
        )
        if policy_controller is not None and recorded_frames % policy_stride_frames == 0:
            latest_policy_action, telemetry = policy_controller.select(
                rgb=np.asarray(rgb)[..., :3],
                depth=np.asarray(depth, dtype=np.float32),
                state=state_vector,
                task=task_text,
                expert_action=action_vector,
                stage=stage,
            )
            latest_policy_stage = stage
            arm_residual_telemetry = {
                "enabled": args.policy_mode in {
                    "base_arm_residual",
                    "base_dual_arm_residual",
                },
                "mode": args.policy_mode,
                "stage_authorized": stage == "transport",
                "ik_accepted": False,
                "target_position_m": None,
                "right_target_position_m": None,
                "anchor_position_m": None,
                "right_anchor_position_m": None,
                "residual_norm_m": None,
                "right_residual_norm_m": None,
                "projection": None,
                "rejection": None,
            }
            if args.policy_mode == "base_arm_residual" and stage == "transport":
                arm_policy_update_attempts += 1
                if (
                    transport_arm_anchor_position is None
                    or transport_arm_anchor_quaternion is None
                    or transport_arm_anchor_base is None
                ):
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "transport_anchor_unavailable"
                elif telemetry["emergency_stop"]:
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "harness_emergency_stop"
                else:
                    current_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
                    dynamic_anchor = np.asarray(transport_arm_anchor_position).copy()
                    dynamic_anchor[:2] += current_base[:2] - np.asarray(
                        transport_arm_anchor_base
                    )[:2]
                    target_position = np.asarray(
                        clamp_position_residual_to_anchor(
                            latest_policy_action[3:6],
                            dynamic_anchor,
                            max_residual_m=0.01,
                        )
                    )
                    try:
                        arm_solution = robot.inverse_kinematics(
                            link=hand,
                            pos=target_position,
                            quat=np.asarray(transport_arm_anchor_quaternion),
                            init_qpos=np.asarray(_flat(robot.get_qpos())),
                            respect_joint_limit=True,
                            max_samples=4,
                            max_solver_iters=40,
                            damping=0.03,
                            max_step_size=0.08,
                            dofs_idx_local=left_arm_dofs,
                        )
                        candidate_qpos = np.asarray(_flat(arm_solution))[left_arm_dofs]
                        if not np.isfinite(candidate_qpos).all():
                            raise ValueError("IK returned non-finite joint targets")
                    except (RuntimeError, ValueError) as exc:
                        latest_policy_left_arm_qpos = None
                        latest_policy_arm_stage = None
                        arm_policy_update_rejections += 1
                        arm_residual_telemetry["rejection"] = str(exc)
                    else:
                        latest_policy_left_arm_qpos = candidate_qpos
                        latest_policy_arm_stage = stage
                        arm_policy_update_accepts += 1
                        arm_residual_telemetry.update(
                            {
                                "ik_accepted": True,
                                "target_position_m": target_position.tolist(),
                                "anchor_position_m": dynamic_anchor.tolist(),
                                "residual_norm_m": float(
                                    np.linalg.norm(target_position - dynamic_anchor)
                                ),
                            }
                        )
            elif args.policy_mode == "base_dual_arm_residual" and stage == "transport":
                arm_policy_update_attempts += 1
                authority = transport_arm_authority(
                    stage=stage,
                    remaining_distance_m=policy_remaining_distance_m,
                )
                if (
                    transport_arm_anchor_position is None
                    or transport_arm_anchor_quaternion is None
                    or transport_right_arm_anchor_position is None
                    or transport_right_arm_anchor_quaternion is None
                    or transport_arm_anchor_base is None
                ):
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "transport_anchor_unavailable"
                elif telemetry["emergency_stop"]:
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "harness_emergency_stop"
                elif telemetry["fallback_to_expert"] or float(telemetry["selected_scale"]) <= 0.0:
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "no_learned_authority"
                elif authority <= 0.0:
                    arm_policy_update_rejections += 1
                    arm_residual_telemetry["rejection"] = "precision_authority_handoff"
                else:
                    current_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
                    base_delta = current_base[:2] - np.asarray(transport_arm_anchor_base)[:2]
                    dynamic_left_anchor = np.asarray(transport_arm_anchor_position).copy()
                    dynamic_right_anchor = np.asarray(transport_right_arm_anchor_position).copy()
                    dynamic_left_anchor[:2] += base_delta
                    dynamic_right_anchor[:2] += base_delta
                    projection = project_dual_arm_residuals(
                        left_proposal_m=latest_policy_action[3:6],
                        right_proposal_m=latest_policy_action[11:14],
                        left_anchor_m=dynamic_left_anchor,
                        right_anchor_m=dynamic_right_anchor,
                        authority_scale=authority,
                        cooperative_carry=args.cooperative_cradle,
                    )
                    try:
                        arm_solution = robot.inverse_kinematics_multilink(
                            links=(left_hand, right_hand),
                            poss=(
                                np.asarray(projection.left_target_m),
                                np.asarray(projection.right_target_m),
                            ),
                            quats=(
                                np.asarray(transport_arm_anchor_quaternion),
                                np.asarray(transport_right_arm_anchor_quaternion),
                            ),
                            init_qpos=np.asarray(_flat(robot.get_qpos())),
                            respect_joint_limit=True,
                            max_samples=4,
                            max_solver_iters=50,
                            damping=0.03,
                            max_step_size=0.08,
                            dofs_idx_local=arm_dofs,
                        )
                        candidate_qpos = np.asarray(_flat(arm_solution))[arm_dofs]
                        if not np.isfinite(candidate_qpos).all():
                            raise ValueError("dual-arm IK returned non-finite joint targets")
                    except (RuntimeError, ValueError) as exc:
                        latest_policy_dual_arm_qpos = None
                        latest_policy_arm_stage = None
                        arm_policy_update_rejections += 1
                        arm_residual_telemetry["rejection"] = str(exc)
                    else:
                        latest_policy_dual_arm_qpos = candidate_qpos
                        latest_policy_arm_stage = stage
                        arm_policy_update_accepts += 1
                        arm_residual_telemetry.update(
                            {
                                "ik_accepted": True,
                                "target_position_m": list(projection.left_target_m),
                                "right_target_position_m": list(projection.right_target_m),
                                "anchor_position_m": dynamic_left_anchor.tolist(),
                                "right_anchor_position_m": dynamic_right_anchor.tolist(),
                                "residual_norm_m": float(
                                    np.linalg.norm(
                                        np.asarray(projection.left_target_m)
                                        - dynamic_left_anchor
                                    )
                                ),
                                "right_residual_norm_m": float(
                                    np.linalg.norm(
                                        np.asarray(projection.right_target_m)
                                        - dynamic_right_anchor
                                    )
                                ),
                                "projection": projection.to_dict(),
                            }
                        )
            elif args.policy_mode in {"base_arm_residual", "base_dual_arm_residual"}:
                latest_policy_left_arm_qpos = None
                latest_policy_dual_arm_qpos = None
                latest_policy_arm_stage = None
            policy_trace.append(
                {
                    **telemetry,
                    "arm_residual": arm_residual_telemetry,
                    "observation_frame": recorded_frames,
                    "physics_step": recorded_physics_steps,
                    "actuation_mode": args.policy_mode,
                    "executed_base_action": _flat(base_action),
                }
            )
        if writer is not None:
            writer.add_frame(
                MobileBimanualFrame(
                    frame_index=recorded_frames,
                    timestamp_seconds=recorded_frames / 30.0,
                    stage=stage,
                    state=tuple(float(value) for value in state_vector),
                    action=tuple(float(value) for value in action_vector),
                    privileged_state=tuple(float(value) for value in parcel_pose),
                    task=task_text,
                    rgb=np.asarray(rgb)[..., :3],
                    depth=np.asarray(depth, dtype=np.float32),
                )
            )
        recorded_frames += 1

    pregrasp_start_arm_qpos = np.asarray(_flat(robot.get_qpos()))[arm_dofs]
    pregrasp_target_arm_qpos = pregrasp_values[arm_dofs]
    pregrasp_physics_steps = 1200 if args.cooperative_cradle else 240
    for pregrasp_step in range(1, pregrasp_physics_steps + 1 if scene_stable else 1):
        if args.cooperative_cradle:
            progress = min(pregrasp_step / 480.0, 1.0)
            smooth_progress = progress * progress * (3.0 - 2.0 * progress)
            pregrasp_command = pregrasp_start_arm_qpos + smooth_progress * (
                pregrasp_target_arm_qpos - pregrasp_start_arm_qpos
            )
        else:
            pregrasp_command = pregrasp_target_arm_qpos
        robot.control_dofs_position(pregrasp_command, arm_dofs)
        scene.step()
        record_control_frame(
            stage="pregrasp",
            base_action=np.zeros(3),
            left_position=pregrasp_targets[0],
            left_quaternion=pregrasp_quaternions[0],
            left_tool_command=-1.0,
            right_position=pregrasp_targets[1],
            right_quaternion=pregrasp_quaternions[1],
            right_tool_command=1.0,
        )
    pregrasp_tracking_error_m = (
        math.dist(_flat(left_hand.get_pos()), pregrasp_targets[0].tolist()),
        math.dist(_flat(right_hand.get_pos()), pregrasp_targets[1].tolist()),
    )
    pregrasp_final_positions = (
        _flat(left_hand.get_pos()),
        _flat(right_hand.get_pos()),
    )

    contact_quaternion = np.asarray(_flat(hand.get_quat()))
    approach_axis = _normalized(
        rotate_vector(tuple(contact_quaternion.tolist()), (0.0, 0.0, 1.0)), np
    )
    current_parcel_position = np.asarray(_flat(parcel.get_pos()))
    current_half_extent_on_axis = _box_ray_extent(approach_axis, parcel_size)
    contact_penetration_m = (
        cooperative_contact_penetration_m if args.cooperative_cradle else 0.003
    )
    contact_hand_target = (
        current_parcel_position
        + left_contact_lateral_offset
        - approach_axis
        * (cup_tip_offset_m + current_half_extent_on_axis - contact_penetration_m)
    )
    precontact_target = contact_hand_target - approach_axis * 0.040

    suction = MobileTriSuctionController(
        robot=robot,
        hand=hand,
        parcel=parcel,
        torch=torch,
        np=np,
        min_sealed_cups=2,
        force_limit_n=30.0,
    )
    parcel_initial_z = _flat(parcel.get_pos())[2]
    contact_start = np.asarray(_flat(hand.get_pos()))
    approach_trace = []
    max_base_speed_m_s = 0.0
    for approach_step in range(2400 if scene_stable else 0):
        current_position = np.asarray(_flat(hand.get_pos()))
        current_quaternion = tuple(_flat(hand.get_quat()))
        current_axis = _normalized(
            rotate_vector(current_quaternion, (0.0, 0.0, 1.0)), np
        )
        dynamic_contact_surface = (
            np.asarray(_flat(parcel.get_pos()))
            + left_contact_lateral_offset
            - approach_axis
            * (current_half_extent_on_axis - contact_penetration_m)
        )
        dynamic_contact_target = (
            dynamic_contact_surface - approach_axis * cup_tip_offset_m
        )
        current_tcp = current_position + current_axis * cup_tip_offset_m
        if args.cooperative_cradle:
            horizontal_error = dynamic_contact_surface[:2] - current_tcp[:2]
            if abs(float(horizontal_error[0])) > 0.010:
                horizontal_error[1] = 0.0
            else:
                horizontal_error[0] = 0.0
        else:
            horizontal_error = dynamic_contact_target[:2] - current_position[:2]
        base_velocity_xy = horizontal_error * 2.0
        base_speed = float(np.linalg.norm(base_velocity_xy))
        if base_speed > 0.05:
            base_velocity_xy *= 0.05 / base_speed
            base_speed = 0.05
        expert_base_velocity_xy = base_velocity_xy.copy()
        if (
            args.policy_mode
            in {"base_residual", "base_arm_residual", "base_dual_arm_residual"}
            and latest_policy_action is not None
            and latest_policy_stage == "grasp_approach"
        ):
            base_velocity_xy = np.asarray(latest_policy_action[:2], dtype=np.float64)
            base_speed = float(np.linalg.norm(base_velocity_xy))
            policy_applied_physics_steps += 1
        robot.control_dofs_velocity(
            np.asarray((base_velocity_xy[0], base_velocity_xy[1], 0.0)),
            base_dofs,
        )
        robot.control_dofs_position(pregrasp_values[arm_dofs], arm_dofs)
        scene.step()
        max_base_speed_m_s = max(max_base_speed_m_s, base_speed)
        sealed, force_n = suction.contact_snapshot()
        record_control_frame(
            stage="grasp_approach",
            base_action=np.asarray((base_velocity_xy[0], base_velocity_xy[1], 0.0)),
            left_position=dynamic_contact_target,
            left_quaternion=current_quaternion,
            left_tool_command=1.0 if sealed >= 2 else -1.0,
            right_position=pregrasp_targets[1],
            right_quaternion=pregrasp_quaternions[1],
            right_tool_command=1.0,
            suction_controller=suction,
            policy_expert_base_action=np.asarray(
                (expert_base_velocity_xy[0], expert_base_velocity_xy[1], 0.0)
            ),
        )
        actual_hand_position = _flat(hand.get_pos())
        actual_tcp = np.asarray(actual_hand_position) + current_axis * cup_tip_offset_m
        distance_to_contact_m = float(
            np.linalg.norm(
                actual_tcp[:2] - dynamic_contact_surface[:2]
                if args.cooperative_cradle
                else np.asarray(actual_hand_position[:2]) - dynamic_contact_target[:2]
            )
        )
        axis_alignment = float(np.dot(current_axis, approach_axis))
        if approach_step % 12 == 0 or sealed or force_n >= 35.0:
            approach_trace.append(
                {
                    "physics_step": approach_step,
                    "distance_to_contact_m": distance_to_contact_m,
                    "axis_alignment": axis_alignment,
                    "dynamic_contact_target_m": dynamic_contact_target.tolist(),
                    "actual_hand_position_m": actual_hand_position,
                    "actual_hand_quaternion_wxyz": _flat(hand.get_quat()),
                    "parcel_position_m": _flat(parcel.get_pos()),
                    "sealed_cups": sealed,
                    "contact_force_n": force_n,
                }
            )
        if sealed >= 2 or force_n >= 35.0:
            break
        if axis_alignment < math.cos(0.25):
            break
        if math.dist(_flat(parcel.get_pos()), settled_parcel_position.tolist()) >= 0.030:
            break
    robot.control_dofs_velocity(np.zeros(3), base_dofs)

    latched = suction.try_latch()
    if latched and args.cooperative_cradle and cradle_monitor is not None:
        engage_start_right_hand = np.asarray(_flat(right_hand.get_pos()))
        engage_left_qpos = np.asarray(_flat(robot.get_qpos()))[left_arm_dofs]
        engage_right_command = np.asarray(_flat(robot.get_qpos()))[right_arm_dofs]
        consecutive_cradle_contact_steps = 0
        for engage_step in range(1, 241):
            cradle_engage_steps += 1
            engage_progress = min(engage_step / 120.0, 1.0)
            if (engage_step - 1) % 8 == 0:
                engage_target = (
                    engage_start_right_hand
                    + np.asarray(right_tool_axis) * (0.015 * engage_progress)
                )
                engage_solution = robot.inverse_kinematics(
                    link=right_hand,
                    pos=engage_target,
                    quat=np.asarray(_flat(right_hand.get_quat())),
                    init_qpos=np.asarray(_flat(robot.get_qpos())),
                    respect_joint_limit=True,
                    max_samples=4,
                    max_solver_iters=40,
                    damping=0.03,
                    max_step_size=0.08,
                    dofs_idx_local=right_arm_dofs,
                )
                candidate = np.asarray(_flat(engage_solution))[right_arm_dofs]
                if np.isfinite(candidate).all():
                    engage_right_command = candidate
            robot.control_dofs_position(engage_left_qpos, left_arm_dofs)
            robot.control_dofs_position(engage_right_command, right_arm_dofs)
            suction.update()
            scene.step()
            cradle_contacts, cradle_force_n = cradle_monitor.snapshot()
            if cradle_contacts > 0:
                cradle_engage_contact_steps += 1
                consecutive_cradle_contact_steps += 1
            else:
                consecutive_cradle_contact_steps = 0
            if (
                suction.attachment is None
                or cradle_force_n >= 35.0
                or consecutive_cradle_contact_steps >= 24
            ):
                break
        cradle_engaged_before_lift = bool(
            suction.attachment is not None
            and consecutive_cradle_contact_steps >= 24
            and cradle_monitor.max_contact_force_n < 35.0
        )
    lift_trace = []
    lift_target_delta_m = 0.10 + min(
        0.02, max(0.0, args.parcel_mass_kg - 0.40) * 0.08
    ) + (0.02 if args.cooperative_cradle else 0.0)
    if latched:
        start_hand = np.asarray(_flat(hand.get_pos()))
        start_right_hand = np.asarray(_flat(right_hand.get_pos()))
        start_qpos = np.asarray(_flat(robot.get_qpos()))
        controlled_arm_dofs = arm_dofs if args.cooperative_cradle else left_arm_dofs
        start_arm_qpos = start_qpos[controlled_arm_dofs]
        lift_target = start_hand + np.asarray((0.0, 0.0, lift_target_delta_m))
        right_lift_target = start_right_hand + np.asarray(
            (0.0, 0.0, lift_target_delta_m)
        )
        lift_quaternion = np.asarray(_flat(hand.get_quat()))
        right_lift_quaternion = np.asarray(_flat(right_hand.get_quat()))
        if not args.cooperative_cradle:
            solution = robot.inverse_kinematics(
                link=hand,
                pos=lift_target,
                quat=lift_quaternion,
                init_qpos=start_qpos,
                respect_joint_limit=True,
                max_samples=8,
                max_solver_iters=80,
                damping=0.02,
                max_step_size=0.15,
                dofs_idx_local=left_arm_dofs,
            )
            target_arm_qpos = np.asarray(_flat(solution))[controlled_arm_dofs]
        else:
            target_arm_qpos = start_arm_qpos.copy()
        for physics_step in range(1, 721):
            progress = min(physics_step / 480.0, 1.0)
            smooth_progress = progress * progress * (3.0 - 2.0 * progress)
            if args.cooperative_cradle and (physics_step - 1) % 8 == 0:
                cooperative_lift_ik_attempts += 1
                current_qpos = np.asarray(_flat(robot.get_qpos()))
                desired_offset = np.asarray(
                    (0.0, 0.0, lift_target_delta_m * smooth_progress)
                )
                try:
                    left_incremental_solution = robot.inverse_kinematics(
                        link=hand,
                        pos=start_hand + desired_offset,
                        quat=lift_quaternion,
                        init_qpos=current_qpos,
                        respect_joint_limit=True,
                        max_samples=4,
                        max_solver_iters=40,
                        damping=0.03,
                        max_step_size=0.08,
                        dofs_idx_local=left_arm_dofs,
                    )
                    right_incremental_solution = robot.inverse_kinematics(
                        link=right_hand,
                        pos=start_right_hand + desired_offset,
                        quat=right_lift_quaternion,
                        init_qpos=current_qpos,
                        respect_joint_limit=True,
                        max_samples=4,
                        max_solver_iters=40,
                        damping=0.03,
                        max_step_size=0.08,
                        dofs_idx_local=right_arm_dofs,
                    )
                    candidate_full_qpos = current_qpos.copy()
                    candidate_full_qpos[left_arm_dofs] = np.asarray(
                        _flat(left_incremental_solution)
                    )[left_arm_dofs]
                    candidate_full_qpos[right_arm_dofs] = np.asarray(
                        _flat(right_incremental_solution)
                    )[right_arm_dofs]
                    candidate_qpos = candidate_full_qpos[arm_dofs]
                    if not np.isfinite(candidate_qpos).all():
                        raise ValueError("incremental dual-arm IK returned non-finite values")
                except (RuntimeError, ValueError):
                    cooperative_lift_ik_rejections += 1
                else:
                    target_arm_qpos = candidate_qpos
                    cooperative_lift_ik_accepts += 1
            command = (
                target_arm_qpos
                if args.cooperative_cradle
                else start_arm_qpos
                + smooth_progress * (target_arm_qpos - start_arm_qpos)
            )
            robot.control_dofs_position(command, controlled_arm_dofs)
            suction.update()
            scene.step()
            if cradle_monitor is not None:
                cradle_lift_steps += 1
                cradle_contacts, _ = cradle_monitor.snapshot()
                cradle_lift_contact_steps += int(cradle_contacts > 0)
            record_control_frame(
                stage="lift",
                base_action=np.zeros(3),
                left_position=start_hand
                + np.asarray((0.0, 0.0, lift_target_delta_m * smooth_progress)),
                left_quaternion=lift_quaternion,
                left_tool_command=1.0,
                right_position=start_right_hand
                + np.asarray((0.0, 0.0, lift_target_delta_m * smooth_progress)),
                right_quaternion=right_lift_quaternion,
                right_tool_command=1.0,
                suction_controller=suction,
            )
            if physics_step % 40 == 0 or suction.attachment is None:
                lift_trace.append(
                    {
                        "physics_step": physics_step,
                        "target_hand_position_m": lift_target.tolist(),
                        "actual_hand_position_m": _flat(hand.get_pos()),
                        "actual_right_hand_position_m": _flat(right_hand.get_pos()),
                        "parcel_position_m": _flat(parcel.get_pos()),
                        "cradle": (
                            cradle_monitor.summary()
                            if cradle_monitor is not None
                            else None
                        ),
                        **suction.summary(),
                    }
                )
            if suction.attachment is None:
                break

    lift_parcel_z = _flat(parcel.get_pos())[2]
    lift_delta = lift_parcel_z - parcel_initial_z
    lift_success = bool(
        latched
        and suction.attachment is not None
        and lift_delta >= 0.08
        and suction.max_force_n < 35.0
        and suction.max_contact_force_n < 35.0
        and (
            not args.cooperative_cradle
            or (
                cradle_monitor is not None
                and cradle_engaged_before_lift
                and cradle_lift_steps > 0
                and cradle_lift_contact_steps / cradle_lift_steps >= 0.50
                and cradle_monitor.max_contact_force_n < 35.0
            )
        )
    )
    transport_trace = []
    transport_success = False
    transport_deadline_handoff = False
    transport_deadline_handoff_step = None
    transport_deadline_handoff_distance_m = None
    transport_deadline_handoff_remaining_s = None
    transport_deadline_handoff_physics_steps = 0
    if lift_success:
        transport_start_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
        transport_target_base = transport_start_base + transport_delta
        transport_arm_anchor_position = np.asarray(_flat(hand.get_pos()))
        transport_arm_anchor_quaternion = np.asarray(_flat(hand.get_quat()))
        transport_right_arm_anchor_position = np.asarray(_flat(right_hand.get_pos()))
        transport_right_arm_anchor_quaternion = np.asarray(_flat(right_hand.get_quat()))
        transport_arm_anchor_base = transport_start_base.copy()
        for physics_step in range(1, 2401):
            current_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
            error_xy = transport_target_base[:2] - current_base[:2]
            distance_m = float(np.linalg.norm(error_xy))
            velocity_xy = error_xy * 2.0
            speed_m_s = float(np.linalg.norm(velocity_xy))
            if speed_m_s > 0.05:
                velocity_xy *= 0.05 / speed_m_s
                speed_m_s = 0.05
            expert_velocity_xy = velocity_xy.copy()
            expert_forward_speed_m_s = (
                float(np.dot(expert_velocity_xy, error_xy / distance_m))
                if distance_m > 1e-9
                else 0.0
            )
            if (
                args.policy_mode
                in {"base_residual", "base_arm_residual", "base_dual_arm_residual"}
                and latest_policy_action is not None
                and latest_policy_stage == "transport"
            ):
                remaining_time_s = (2401 - physics_step) / 240.0
                if not transport_deadline_handoff:
                    transport_deadline_handoff = transport_deadline_requires_expert(
                        distance_m=distance_m,
                        remaining_time_s=remaining_time_s,
                        expert_forward_speed_m_s=expert_forward_speed_m_s,
                        minimum_capacity_ratio=transport_capacity_ratio,
                    )
                    if transport_deadline_handoff:
                        transport_deadline_handoff_step = physics_step
                        transport_deadline_handoff_distance_m = distance_m
                        transport_deadline_handoff_remaining_s = remaining_time_s
                if transport_deadline_handoff:
                    velocity_xy = expert_velocity_xy
                    transport_deadline_handoff_physics_steps += 1
                else:
                    velocity_xy = np.asarray(
                        latest_policy_action[:2], dtype=np.float64
                    )
                    policy_applied_physics_steps += 1
                speed_m_s = float(np.linalg.norm(velocity_xy))
            robot.control_dofs_velocity(
                np.asarray((velocity_xy[0], velocity_xy[1], 0.0)), base_dofs
            )
            if (
                args.policy_mode == "base_dual_arm_residual"
                and latest_policy_dual_arm_qpos is not None
                and latest_policy_arm_stage == "transport"
            ):
                robot.control_dofs_position(latest_policy_dual_arm_qpos, arm_dofs)
                arm_policy_applied_physics_steps += 1
            elif args.cooperative_cradle:
                robot.control_dofs_position(target_arm_qpos, arm_dofs)
            else:
                arm_command = target_arm_qpos
                if (
                    args.policy_mode == "base_arm_residual"
                    and latest_policy_left_arm_qpos is not None
                    and latest_policy_arm_stage == "transport"
                ):
                    arm_command = latest_policy_left_arm_qpos
                    arm_policy_applied_physics_steps += 1
                robot.control_dofs_position(arm_command, left_arm_dofs)
            suction.update()
            scene.step()
            if cradle_monitor is not None:
                cradle_transport_steps += 1
                cradle_contacts, _ = cradle_monitor.snapshot()
                cradle_transport_contact_steps += int(cradle_contacts > 0)
            record_control_frame(
                stage="transport",
                base_action=np.asarray((velocity_xy[0], velocity_xy[1], 0.0)),
                left_position=_flat(hand.get_pos()),
                left_quaternion=_flat(hand.get_quat()),
                left_tool_command=1.0,
                right_position=_flat(right_hand.get_pos()),
                right_quaternion=_flat(right_hand.get_quat()),
                right_tool_command=1.0,
                suction_controller=suction,
                policy_expert_base_action=np.asarray(
                    (expert_velocity_xy[0], expert_velocity_xy[1], 0.0)
                ),
                policy_remaining_distance_m=distance_m,
            )
            if physics_step % 120 == 0 or suction.attachment is None or distance_m <= 0.005:
                transport_trace.append(
                    {
                        "physics_step": physics_step,
                        "base_position_xy_m": _flat(robot.get_qpos())[base_dofs[0] : base_dofs[1] + 1],
                        "distance_to_destination_m": distance_m,
                        "parcel_position_m": _flat(parcel.get_pos()),
                        "cradle": (
                            cradle_monitor.summary()
                            if cradle_monitor is not None
                            else None
                        ),
                        **suction.summary(),
                    }
                )
            if suction.attachment is None or distance_m <= 0.005:
                break
        robot.control_dofs_velocity(np.zeros(3), base_dofs)
        final_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
        transport_success = bool(
            suction.attachment is not None
            and float(np.linalg.norm(transport_target_base[:2] - final_base[:2])) <= 0.010
            and math.dist(
                _flat(parcel.get_pos())[:2],
                (initial_parcel_position + transport_delta)[:2].tolist(),
            )
            <= 0.040
            and (
                not args.cooperative_cradle
                or (
                    cradle_transport_steps > 0
                    and cradle_transport_contact_steps / cradle_transport_steps >= 0.50
                )
            )
        )

    place_trace = []
    placed_before_release = False
    released = False
    consecutive_place_target_steps = 0
    place_completed_early = False
    if transport_success:
        place_start_hand = np.asarray(_flat(hand.get_pos()))
        place_start_right_hand = np.asarray(_flat(right_hand.get_pos()))
        place_start_qpos = np.asarray(_flat(robot.get_qpos()))
        controlled_place_dofs = arm_dofs if args.cooperative_cradle else left_arm_dofs
        place_start_arm_qpos = place_start_qpos[controlled_place_dofs]
        place_drop_m = lift_target_delta_m - 0.015
        place_target = place_start_hand - np.asarray((0.0, 0.0, place_drop_m))
        right_place_target = place_start_right_hand - np.asarray(
            (0.0, 0.0, place_drop_m)
        )
        place_quaternion = np.asarray(_flat(hand.get_quat()))
        right_place_quaternion = np.asarray(_flat(right_hand.get_quat()))
        expected_placed_position = initial_parcel_position + transport_delta
        if not args.cooperative_cradle:
            place_solution = robot.inverse_kinematics(
                link=hand,
                pos=place_target,
                quat=place_quaternion,
                init_qpos=place_start_qpos,
                respect_joint_limit=True,
                max_samples=8,
                max_solver_iters=80,
                damping=0.02,
                max_step_size=0.15,
                dofs_idx_local=left_arm_dofs,
            )
            place_target_arm_qpos = np.asarray(_flat(place_solution))[
                controlled_place_dofs
            ]
        else:
            place_target_arm_qpos = place_start_arm_qpos.copy()
        for physics_step in range(1, 721):
            progress = min(physics_step / 480.0, 1.0)
            smooth_progress = progress * progress * (3.0 - 2.0 * progress)
            if args.cooperative_cradle and (physics_step - 1) % 8 == 0:
                cooperative_place_ik_attempts += 1
                current_qpos = np.asarray(_flat(robot.get_qpos()))
                desired_offset = np.asarray(
                    (0.0, 0.0, -place_drop_m * smooth_progress)
                )
                try:
                    left_incremental_solution = robot.inverse_kinematics(
                        link=hand,
                        pos=place_start_hand + desired_offset,
                        quat=place_quaternion,
                        init_qpos=current_qpos,
                        respect_joint_limit=True,
                        max_samples=4,
                        max_solver_iters=40,
                        damping=0.03,
                        max_step_size=0.08,
                        dofs_idx_local=left_arm_dofs,
                    )
                    right_incremental_solution = robot.inverse_kinematics(
                        link=right_hand,
                        pos=place_start_right_hand + desired_offset,
                        quat=right_place_quaternion,
                        init_qpos=current_qpos,
                        respect_joint_limit=True,
                        max_samples=4,
                        max_solver_iters=40,
                        damping=0.03,
                        max_step_size=0.08,
                        dofs_idx_local=right_arm_dofs,
                    )
                    candidate_full_qpos = current_qpos.copy()
                    candidate_full_qpos[left_arm_dofs] = np.asarray(
                        _flat(left_incremental_solution)
                    )[left_arm_dofs]
                    candidate_full_qpos[right_arm_dofs] = np.asarray(
                        _flat(right_incremental_solution)
                    )[right_arm_dofs]
                    candidate_qpos = candidate_full_qpos[arm_dofs]
                    if not np.isfinite(candidate_qpos).all():
                        raise ValueError(
                            "incremental dual-arm place IK returned non-finite values"
                        )
                except (RuntimeError, ValueError):
                    cooperative_place_ik_rejections += 1
                else:
                    place_target_arm_qpos = candidate_qpos
                    cooperative_place_ik_accepts += 1
            command = (
                place_target_arm_qpos
                if args.cooperative_cradle
                else place_start_arm_qpos
                + smooth_progress * (place_target_arm_qpos - place_start_arm_qpos)
            )
            robot.control_dofs_position(command, controlled_place_dofs)
            suction.update()
            scene.step()
            if cradle_monitor is not None:
                cradle_place_steps += 1
                cradle_contacts, _ = cradle_monitor.snapshot()
                cradle_place_contact_steps += int(cradle_contacts > 0)
            if (
                args.cooperative_cradle
                and suction.attachment is not None
                and placement_within_release_gate(
                    _flat(parcel.get_pos()), expected_placed_position
                )
            ):
                consecutive_place_target_steps += 1
            else:
                consecutive_place_target_steps = 0
            place_completed_early = bool(
                args.cooperative_cradle and consecutive_place_target_steps >= 24
            )
            record_control_frame(
                stage="place",
                base_action=np.zeros(3),
                left_position=place_start_hand
                - np.asarray((0.0, 0.0, place_drop_m * smooth_progress)),
                left_quaternion=place_quaternion,
                left_tool_command=1.0,
                right_position=place_start_right_hand
                - np.asarray((0.0, 0.0, place_drop_m * smooth_progress)),
                right_quaternion=right_place_quaternion,
                right_tool_command=1.0,
                suction_controller=suction,
            )
            if (
                physics_step % 40 == 0
                or suction.attachment is None
                or place_completed_early
            ):
                place_trace.append(
                    {
                        "physics_step": physics_step,
                        "actual_hand_position_m": _flat(hand.get_pos()),
                        "actual_right_hand_position_m": _flat(right_hand.get_pos()),
                        "parcel_position_m": _flat(parcel.get_pos()),
                        "cradle": (
                            cradle_monitor.summary()
                            if cradle_monitor is not None
                            else None
                        ),
                        **suction.summary(),
                    }
                )
            if suction.attachment is None:
                break
            if place_completed_early:
                break
        parcel_before_release = np.asarray(_flat(parcel.get_pos()))
        placed_before_release = bool(
            suction.attachment is not None
            and placement_within_release_gate(
                parcel_before_release, expected_placed_position
            )
        )
        if placed_before_release:
            suction.release()
            released = True
            for _ in range(240):
                scene.step()
                record_control_frame(
                    stage="release",
                    base_action=np.zeros(3),
                    left_position=_flat(hand.get_pos()),
                    left_quaternion=_flat(hand.get_quat()),
                    left_tool_command=-1.0,
                    right_position=_flat(right_hand.get_pos()),
                    right_quaternion=_flat(right_hand.get_quat()),
                    right_tool_command=1.0,
                    suction_controller=suction,
                )

    parcel_final_position = np.asarray(_flat(parcel.get_pos()))
    expected_final_position = initial_parcel_position + transport_delta
    placement_error_m = float(np.linalg.norm(parcel_final_position - expected_final_position))
    success = bool(
        lift_success
        and transport_success
        and placed_before_release
        and released
        and placement_error_m <= 0.040
        and suction.max_force_n < 35.0
        and suction.max_contact_force_n < 35.0
        and (
            cradle_monitor is None or cradle_monitor.max_contact_force_n < 35.0
        )
    )
    dataset_saved = False
    if writer is not None:
        if success and recorded_frames > 0:
            writer.save_episode()
            writer.finalize()
            dataset_saved = True
        else:
            writer.clear_episode()
    policy_latencies = [float(item["latency_ms"]) for item in policy_trace]
    warm_policy_latencies = policy_latencies[1:]
    policy_stages = sorted({str(item["stage"]) for item in policy_trace})
    accepted_dual_arm_updates = [
        item["arm_residual"]
        for item in policy_trace
        if args.policy_mode == "base_dual_arm_residual"
        and bool(item["arm_residual"]["ik_accepted"])
        and item["arm_residual"]["projection"] is not None
    ]
    depth_risk_updates = [
        item["depth_risk"]
        for item in policy_trace
        if item["depth_risk"] is not None
    ]
    policy_summary = {
        "enabled": policy_controller is not None,
        "mode": args.policy_mode if policy_controller is not None else "expert_only",
        "checkpoint": (
            str(args.smolvla_checkpoint.resolve())
            if args.smolvla_checkpoint is not None
            else None
        ),
        "requested_hz": args.policy_hz if policy_controller is not None else 0,
        "minimum_expert_progress_ratio": harness_config.min_progress_ratio,
        "force_memory_enabled": args.force_memory_harness,
        "depth_sidecar_enabled": args.depth_risk_sidecar,
        "depth_sidecar_tighten_count": sum(
            float(item["scale_cap"]) < 1.0 - 1e-9 for item in depth_risk_updates
        ),
        "depth_sidecar_fail_closed_count": sum(
            bool(item["fail_closed"]) for item in depth_risk_updates
        ),
        "mean_depth_sidecar_scale_cap": (
            statistics.fmean(float(item["scale_cap"]) for item in depth_risk_updates)
            if depth_risk_updates
            else None
        ),
        "force_memory_tighten_count": sum(
            bool(item["force_memory_enabled"])
            and float(item["force_memory"]["scale_cap"]) < 1.0 - 1e-9
            for item in policy_trace
        ),
        "force_memory_full_fallback_count": sum(
            bool(item["force_memory_enabled"])
            and float(item["force_memory"]["scale_cap"]) <= 1e-9
            for item in policy_trace
        ),
        "mean_force_memory_scale_cap": (
            statistics.fmean(
                float(item["force_memory"]["scale_cap"]) for item in policy_trace
            )
            if policy_trace
            else None
        ),
        "transport_capacity_ratio": transport_capacity_ratio,
        "transport_deadline_handoff": transport_deadline_handoff,
        "transport_deadline_handoff_step": transport_deadline_handoff_step,
        "transport_deadline_handoff_distance_m": transport_deadline_handoff_distance_m,
        "transport_deadline_handoff_remaining_s": transport_deadline_handoff_remaining_s,
        "transport_deadline_handoff_physics_steps": transport_deadline_handoff_physics_steps,
        "inference_calls": len(policy_trace),
        "mean_latency_ms": statistics.fmean(policy_latencies) if policy_latencies else None,
        "p95_latency_ms": (
            sorted(policy_latencies)[math.ceil(0.95 * len(policy_latencies)) - 1]
            if policy_latencies
            else None
        ),
        "cold_start_latency_ms": policy_latencies[0] if policy_latencies else None,
        "warm_mean_latency_ms": (
            statistics.fmean(warm_policy_latencies) if warm_policy_latencies else None
        ),
        "warm_p95_latency_ms": (
            sorted(warm_policy_latencies)[
                math.ceil(0.95 * len(warm_policy_latencies)) - 1
            ]
            if warm_policy_latencies
            else None
        ),
        "stages": {
            stage: sum(str(item["stage"]) == stage for item in policy_trace)
            for stage in policy_stages
        },
        "mean_selected_scale": (
            statistics.fmean(float(item["selected_scale"]) for item in policy_trace)
            if policy_trace
            else None
        ),
        "expert_fallback_count": sum(
            bool(item["fallback_to_expert"]) for item in policy_trace
        ),
        "emergency_stop_count": sum(
            bool(item["emergency_stop"]) for item in policy_trace
        ),
        "tool_command_correction_count": sum(
            int(item["tool_command_corrections"]) for item in policy_trace
        ),
        "applied_physics_steps": policy_applied_physics_steps,
        "arm_residual": {
            "enabled": args.policy_mode
            in {"base_arm_residual", "base_dual_arm_residual"},
            "authorized_stages": ["transport"],
            "max_cumulative_position_residual_m": 0.01,
            "dual_arm_common_mode": args.policy_mode == "base_dual_arm_residual",
            "maximum_differential_residual_m": (
                0.0 if args.cooperative_cradle else 0.0015
            )
            if args.policy_mode == "base_dual_arm_residual"
            else None,
            "precision_fade_distance_m": (
                {"zero": 0.025, "full": 0.120}
                if args.policy_mode == "base_dual_arm_residual"
                else None
            ),
            "orientation_control": "expert_locked",
            "tool_control": "expert_locked",
            "ik_update_attempts": arm_policy_update_attempts,
            "ik_update_accepts": arm_policy_update_accepts,
            "ik_update_rejections": arm_policy_update_rejections,
            "applied_physics_steps": arm_policy_applied_physics_steps,
            "accepted_dual_arm_updates": len(accepted_dual_arm_updates),
            "left_material_updates": sum(
                float(item["residual_norm_m"] or 0.0) > 1e-5
                for item in accepted_dual_arm_updates
            ),
            "right_material_updates": sum(
                float(item["right_residual_norm_m"] or 0.0) > 1e-5
                for item in accepted_dual_arm_updates
            ),
            "maximum_tool_separation_change_m": (
                max(
                    float(item["projection"]["separation_change_m"])
                    for item in accepted_dual_arm_updates
                )
                if accepted_dual_arm_updates
                else None
            ),
        },
        "actuation_scope": (
            "grasp-approach and transport base velocity residual only"
            if args.policy_mode == "base_residual" and policy_controller is not None
            else (
                "grasp-approach/transport base velocity plus anchored transport left-arm "
                "position residual"
            )
            if args.policy_mode == "base_arm_residual" and policy_controller is not None
            else (
                "grasp-approach/transport base velocity plus rigid-object-consistent "
                "dual-arm transport position residual"
            )
            if args.policy_mode == "base_dual_arm_residual" and policy_controller is not None
            else "none; shadow evaluation"
            if policy_controller is not None
            else "deterministic expert"
        ),
        "trace": policy_trace,
    }
    payload = {
        "runtime": runtime_report(),
        "task": (
            "mobile cooperative tri-suction and V-cradle parcel transport"
            if args.cooperative_cradle
            else "mobile tri-suction parcel pickup, transport, and place"
        ),
        "parcel_profile": args.parcel_profile,
        "parcel_mass_kg": args.parcel_mass_kg,
        "parcel_size_m": parcel_size.tolist(),
        "parcel_friction": args.parcel_friction,
        "parcel_offset_m": list(args.parcel_offset_m),
        "task_text": task_text,
        "policy": policy_summary,
        "tool_axis_world": tool_axis.tolist(),
        "approach_axis_world": approach_axis.tolist(),
        "precontact_target_m": precontact_target.tolist(),
        "contact_hand_target_m": contact_hand_target.tolist(),
        "right_cradle_contact_target_m": (
            right_cradle_contact_target.tolist()
            if right_cradle_contact_target is not None
            else None
        ),
        "contact_penetration_m": contact_penetration_m,
        "max_approach_base_speed_m_s": max_base_speed_m_s,
        "pregrasp_tracking_error_m": list(pregrasp_tracking_error_m),
        "pregrasp_targets_m": [target.tolist() for target in pregrasp_targets],
        "pregrasp_final_positions_m": list(pregrasp_final_positions),
        "planned_parcel_position_m": planned_parcel_position.tolist(),
        "parcel_spawn_position_m": parcel_spawn.tolist(),
        "pedestal_position_m": pedestal_position.tolist(),
        "destination_pedestal_position_m": destination_pedestal_position.tolist(),
        "scene_stable": scene_stable,
        "settle_position_error_m": settle_position_error_m,
        "settle_linear_speed_m_s": settle_linear_speed_m_s,
        "settle_trace": settle_trace,
        "parcel_initial_z_m": parcel_initial_z,
        "parcel_lift_z_m": lift_parcel_z,
        "parcel_final_position_m": parcel_final_position.tolist(),
        "lift_delta_m": lift_delta,
        "lift_target_delta_m": lift_target_delta_m,
        "lift_success": lift_success,
        "transport_success": transport_success,
        "placed_before_release": placed_before_release,
        "place_release_gate_required_steps": 24,
        "place_release_gate_consecutive_steps": consecutive_place_target_steps,
        "place_completed_early": place_completed_early,
        "released": released,
        "placement_error_m": placement_error_m,
        "latched": latched,
        "approach_trace": approach_trace,
        "lift_trace": lift_trace,
        "transport_trace": transport_trace,
        "place_trace": place_trace,
        "dataset": {
            "requested": args.record_dataset is not None,
            "saved": dataset_saved,
            "root": str(args.record_dataset) if args.record_dataset is not None else None,
            "frames": recorded_frames if writer is not None else 0,
            "fps": 30,
            "state_dim": 43,
            "action_dim": 19,
            "rgb_shape": [args.image_size, args.image_size, 3],
            "depth_shape": [args.image_size, args.image_size, 1],
            "privileged_state_in_policy": False,
        },
        "suction": suction.summary(),
        "cradle": {
            "enabled": args.cooperative_cradle,
            "lift_contact_steps": cradle_lift_contact_steps,
            "lift_steps": cradle_lift_steps,
            "lift_contact_ratio": (
                cradle_lift_contact_steps / cradle_lift_steps
                if cradle_lift_steps
                else 0.0
            ),
            "transport_contact_steps": cradle_transport_contact_steps,
            "transport_steps": cradle_transport_steps,
            "transport_contact_ratio": (
                cradle_transport_contact_steps / cradle_transport_steps
                if cradle_transport_steps
                else 0.0
            ),
            "place_contact_steps": cradle_place_contact_steps,
            "place_steps": cradle_place_steps,
            "place_contact_ratio": (
                cradle_place_contact_steps / cradle_place_steps
                if cradle_place_steps
                else 0.0
            ),
            "minimum_required_lift_transport_contact_ratio": (
                0.50 if args.cooperative_cradle else None
            ),
            "engage_steps": cradle_engage_steps,
            "engage_contact_steps": cradle_engage_contact_steps,
            "engaged_before_lift": cradle_engaged_before_lift,
            "incremental_lift_ik_attempts": cooperative_lift_ik_attempts,
            "incremental_lift_ik_accepts": cooperative_lift_ik_accepts,
            "incremental_lift_ik_rejections": cooperative_lift_ik_rejections,
            "incremental_place_ik_attempts": cooperative_place_ik_attempts,
            "incremental_place_ik_accepts": cooperative_place_ik_accepts,
            "incremental_place_ik_rejections": cooperative_place_ik_rejections,
            "physical": (
                cradle_monitor.summary() if cradle_monitor is not None else None
            ),
        },
        "success": success,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
