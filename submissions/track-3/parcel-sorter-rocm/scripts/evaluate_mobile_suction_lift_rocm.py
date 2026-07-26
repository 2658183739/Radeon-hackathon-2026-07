"""Verify physical tri-cup contact, compliant attachment, and parcel lift."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from parcel_sorter.genesis_env import initialize_genesis
from parcel_sorter.mobile_bimanual import (
    ARM_JOINT_NAMES,
    BASE_JOINT_NAMES,
    END_EFFECTOR_LINK_NAMES,
    FINGER_JOINT_NAMES,
    build_mobile_bimanual_mjcf,
    joint_dof_indices,
)
from parcel_sorter.mobile_suction import MobileTriSuctionController
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
    args = parser.parse_args()

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
    pedestal_position = np.asarray((-0.6800, 0.7500, 1.3000))
    transport_delta = np.asarray((0.3000, 0.0, 0.0))
    destination_pedestal_position = pedestal_position + transport_delta
    initial_parcel_position = np.asarray((-0.6800, 0.7500, 1.4520))
    scene.add_entity(
        gs.morphs.Box(
            size=(0.16, 0.08, 0.10),
            pos=tuple(pedestal_position.tolist()),
            fixed=True,
        )
    )
    scene.add_entity(
        gs.morphs.Box(
            size=(0.16, 0.08, 0.10),
            pos=tuple(destination_pedestal_position.tolist()),
            fixed=True,
        )
    )
    parcel_size = np.asarray((0.20, 0.12, 0.20))
    parcel = scene.add_entity(
        gs.morphs.Box(
            size=tuple(parcel_size.tolist()),
            pos=tuple(initial_parcel_position.tolist()),
        ),
        material=gs.materials.Rigid(friction=0.8),
    )
    robot = scene.add_entity(gs.morphs.MJCF(file=str(asset)))
    scene.build()
    parcel.set_mass(0.40)

    base_dofs = np.asarray(joint_dof_indices(robot, BASE_JOINT_NAMES))
    left_arm_dofs = np.asarray(joint_dof_indices(robot, ARM_JOINT_NAMES["left"]))
    right_arm_dofs = np.asarray(joint_dof_indices(robot, ARM_JOINT_NAMES["right"]))
    arm_dofs = np.asarray((*left_arm_dofs.tolist(), *right_arm_dofs.tolist()))
    finger_dofs = np.asarray(
        (
            *joint_dof_indices(robot, FINGER_JOINT_NAMES["left"]),
            *joint_dof_indices(robot, FINGER_JOINT_NAMES["right"]),
        )
    )
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
        supported = bool(settled_parcel_position[2] >= pedestal_position[2] + 0.075)
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
        and settled_parcel_position[2] >= pedestal_position[2] + 0.075
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
    center_y = 0.5 * (pregrasp_start_positions[0][1] + pregrasp_start_positions[1][1])
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
        + np.asarray((-0.08, 0.20 * (center_y - pregrasp_start_positions[1][1]), -0.08)),
    )
    pregrasp_solution = robot.inverse_kinematics_multilink(
        links=(left_hand, right_hand),
        poss=pregrasp_targets,
        quats=pregrasp_quaternions,
        init_qpos=np.asarray(_flat(robot.get_qpos())),
        respect_joint_limit=True,
        max_samples=12,
        max_solver_iters=50,
        damping=0.02,
        max_step_size=0.25,
        dofs_idx_local=arm_dofs,
    )
    pregrasp_values = np.asarray(_flat(pregrasp_solution))
    robot.control_dofs_position(pregrasp_values[arm_dofs], arm_dofs)
    for _ in range(240 if scene_stable else 0):
        scene.step()
    pregrasp_tracking_error_m = (
        math.dist(_flat(left_hand.get_pos()), pregrasp_targets[0].tolist()),
        math.dist(_flat(right_hand.get_pos()), pregrasp_targets[1].tolist()),
    )

    contact_quaternion = np.asarray(_flat(hand.get_quat()))
    approach_axis = _normalized(
        rotate_vector(tuple(contact_quaternion.tolist()), (0.0, 0.0, 1.0)), np
    )
    current_parcel_position = np.asarray(_flat(parcel.get_pos()))
    current_half_extent_on_axis = _box_ray_extent(approach_axis, parcel_size)
    contact_penetration_m = 0.003
    contact_hand_target = current_parcel_position - approach_axis * (
        cup_tip_offset_m + current_half_extent_on_axis - contact_penetration_m
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
        dynamic_contact_target = np.asarray(_flat(parcel.get_pos())) - approach_axis * (
            cup_tip_offset_m + current_half_extent_on_axis - contact_penetration_m
        )
        horizontal_error = dynamic_contact_target[:2] - current_position[:2]
        base_velocity_xy = horizontal_error * 2.0
        base_speed = float(np.linalg.norm(base_velocity_xy))
        if base_speed > 0.05:
            base_velocity_xy *= 0.05 / base_speed
            base_speed = 0.05
        robot.control_dofs_velocity(
            np.asarray((base_velocity_xy[0], base_velocity_xy[1], 0.0)),
            base_dofs,
        )
        robot.control_dofs_position(pregrasp_values[arm_dofs], arm_dofs)
        scene.step()
        max_base_speed_m_s = max(max_base_speed_m_s, base_speed)
        sealed, force_n = suction.contact_snapshot()
        actual_hand_position = _flat(hand.get_pos())
        distance_to_contact_m = float(
            np.linalg.norm(np.asarray(actual_hand_position[:2]) - dynamic_contact_target[:2])
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
    lift_trace = []
    if latched:
        start_hand = np.asarray(_flat(hand.get_pos()))
        start_qpos = np.asarray(_flat(robot.get_qpos()))
        start_arm_qpos = start_qpos[left_arm_dofs]
        lift_target = start_hand + np.asarray((0.0, 0.0, 0.10))
        lift_quaternion = np.asarray(_flat(hand.get_quat()))
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
        target_arm_qpos = np.asarray(_flat(solution))[left_arm_dofs]
        for physics_step in range(1, 721):
            progress = min(physics_step / 480.0, 1.0)
            smooth_progress = progress * progress * (3.0 - 2.0 * progress)
            command = start_arm_qpos + smooth_progress * (
                target_arm_qpos - start_arm_qpos
            )
            robot.control_dofs_position(command, left_arm_dofs)
            suction.update()
            scene.step()
            if physics_step % 40 == 0 or suction.attachment is None:
                lift_trace.append(
                    {
                        "physics_step": physics_step,
                        "target_hand_position_m": lift_target.tolist(),
                        "actual_hand_position_m": _flat(hand.get_pos()),
                        "parcel_position_m": _flat(parcel.get_pos()),
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
    )
    transport_trace = []
    transport_success = False
    if lift_success:
        transport_start_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
        transport_target_base = transport_start_base + transport_delta
        for physics_step in range(1, 2401):
            current_base = np.asarray(_flat(robot.get_qpos()))[base_dofs]
            error_xy = transport_target_base[:2] - current_base[:2]
            distance_m = float(np.linalg.norm(error_xy))
            velocity_xy = error_xy * 2.0
            speed_m_s = float(np.linalg.norm(velocity_xy))
            if speed_m_s > 0.05:
                velocity_xy *= 0.05 / speed_m_s
                speed_m_s = 0.05
            robot.control_dofs_velocity(
                np.asarray((velocity_xy[0], velocity_xy[1], 0.0)), base_dofs
            )
            robot.control_dofs_position(target_arm_qpos, left_arm_dofs)
            suction.update()
            scene.step()
            if physics_step % 120 == 0 or suction.attachment is None or distance_m <= 0.005:
                transport_trace.append(
                    {
                        "physics_step": physics_step,
                        "base_position_xy_m": _flat(robot.get_qpos())[base_dofs[0] : base_dofs[1] + 1],
                        "distance_to_destination_m": distance_m,
                        "parcel_position_m": _flat(parcel.get_pos()),
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
        )

    place_trace = []
    placed_before_release = False
    released = False
    if transport_success:
        place_start_hand = np.asarray(_flat(hand.get_pos()))
        place_start_qpos = np.asarray(_flat(robot.get_qpos()))
        place_start_arm_qpos = place_start_qpos[left_arm_dofs]
        place_target = place_start_hand - np.asarray((0.0, 0.0, 0.085))
        place_quaternion = np.asarray(_flat(hand.get_quat()))
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
        place_target_arm_qpos = np.asarray(_flat(place_solution))[left_arm_dofs]
        for physics_step in range(1, 721):
            progress = min(physics_step / 480.0, 1.0)
            smooth_progress = progress * progress * (3.0 - 2.0 * progress)
            command = place_start_arm_qpos + smooth_progress * (
                place_target_arm_qpos - place_start_arm_qpos
            )
            robot.control_dofs_position(command, left_arm_dofs)
            suction.update()
            scene.step()
            if physics_step % 40 == 0 or suction.attachment is None:
                place_trace.append(
                    {
                        "physics_step": physics_step,
                        "actual_hand_position_m": _flat(hand.get_pos()),
                        "parcel_position_m": _flat(parcel.get_pos()),
                        **suction.summary(),
                    }
                )
            if suction.attachment is None:
                break
        expected_placed_position = initial_parcel_position + transport_delta
        parcel_before_release = np.asarray(_flat(parcel.get_pos()))
        placed_before_release = bool(
            suction.attachment is not None
            and float(np.linalg.norm(parcel_before_release[:2] - expected_placed_position[:2]))
            <= 0.040
            and abs(float(parcel_before_release[2] - expected_placed_position[2])) <= 0.025
        )
        if placed_before_release:
            suction.release()
            released = True
            for _ in range(240):
                scene.step()

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
    )
    payload = {
        "runtime": runtime_report(),
        "task": "mobile tri-suction parcel pickup, transport, and place",
        "parcel_mass_kg": 0.40,
        "parcel_size_m": parcel_size.tolist(),
        "tool_axis_world": tool_axis.tolist(),
        "approach_axis_world": approach_axis.tolist(),
        "precontact_target_m": precontact_target.tolist(),
        "contact_hand_target_m": contact_hand_target.tolist(),
        "contact_penetration_m": contact_penetration_m,
        "max_approach_base_speed_m_s": max_base_speed_m_s,
        "pregrasp_tracking_error_m": list(pregrasp_tracking_error_m),
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
        "lift_success": lift_success,
        "transport_success": transport_success,
        "placed_before_release": placed_before_release,
        "released": released,
        "placement_error_m": placement_error_m,
        "latched": latched,
        "approach_trace": approach_trace,
        "lift_trace": lift_trace,
        "transport_trace": transport_trace,
        "place_trace": place_trace,
        "suction": suction.summary(),
        "success": success,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
