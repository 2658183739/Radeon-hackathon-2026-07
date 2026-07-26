"""Verify physical tri-cup contact, compliant attachment, and parcel lift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from parcel_sorter.expert import DOWNWARD_QUATERNION
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


def _flat(values: object) -> list[float]:
    if hasattr(values, "detach"):
        values = values.detach().cpu()  # type: ignore[union-attr]
    if hasattr(values, "reshape"):
        values = values.reshape(-1)  # type: ignore[union-attr]
    return [float(value) for value in values]  # type: ignore[union-attr]


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
    scene.add_entity(gs.morphs.Box(size=(0.60, 0.50, 0.10), pos=(-0.55, 0.36, 1.00), fixed=True))
    parcel = scene.add_entity(
        gs.morphs.Box(size=(0.20, 0.12, 0.10), pos=(-0.55, 0.36, 1.10)),
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
    contact_target = np.asarray((-0.55, 0.36, 1.262))
    approach_trace = []
    for descent in range(10):
        target = contact_target - np.asarray((0.0, 0.0, descent * 0.004))
        solution = robot.inverse_kinematics(
            link=hand,
            pos=target,
            quat=np.asarray(DOWNWARD_QUATERNION),
            init_qpos=np.asarray(_flat(robot.get_qpos())),
            respect_joint_limit=True,
            max_samples=12,
            max_solver_iters=50,
            damping=0.02,
            max_step_size=0.20,
            dofs_idx_local=left_arm_dofs,
        )
        solution_values = np.asarray(_flat(solution))
        robot.control_dofs_position(solution_values[left_arm_dofs], left_arm_dofs)
        for _ in range(240):
            scene.step()
        sealed, force_n = suction.contact_snapshot()
        actual_hand_position = _flat(hand.get_pos())
        actual_hand_quaternion = _flat(hand.get_quat())
        approach_trace.append(
            {
                "descent_m": descent * 0.004,
                "target_position_m": target.tolist(),
                "actual_hand_position_m": actual_hand_position,
                "actual_hand_quaternion_wxyz": actual_hand_quaternion,
                "parcel_position_m": _flat(parcel.get_pos()),
                "sealed_cups": sealed,
                "contact_force_n": force_n,
            }
        )
        if sealed >= 2 or force_n >= 35.0:
            break

    latched = suction.try_latch()
    lift_trace = []
    if latched:
        start_hand = np.asarray(_flat(hand.get_pos()))
        for waypoint in range(1, 13):
            target = start_hand + np.asarray((0.0, 0.0, waypoint * 0.01))
            solution = robot.inverse_kinematics(
                link=hand,
                pos=target,
                quat=np.asarray(DOWNWARD_QUATERNION),
                init_qpos=np.asarray(_flat(robot.get_qpos())),
                respect_joint_limit=True,
                max_samples=8,
                max_solver_iters=40,
                damping=0.02,
                max_step_size=0.15,
                dofs_idx_local=left_arm_dofs,
            )
            solution_values = np.asarray(_flat(solution))
            robot.control_dofs_position(solution_values[left_arm_dofs], left_arm_dofs)
            for _ in range(24):
                suction.update()
                scene.step()
            lift_trace.append(
                {
                    "waypoint": waypoint,
                    "parcel_z_m": _flat(parcel.get_pos())[2],
                    **suction.summary(),
                }
            )
            if suction.attachment is None:
                break

    parcel_final_z = _flat(parcel.get_pos())[2]
    lift_delta = parcel_final_z - parcel_initial_z
    success = bool(
        latched
        and suction.attachment is not None
        and lift_delta >= 0.08
        and suction.max_force_n < 35.0
        and suction.max_contact_force_n < 35.0
    )
    payload = {
        "runtime": runtime_report(),
        "task": "mobile left tri-suction physical parcel lift",
        "parcel_mass_kg": 0.40,
        "parcel_initial_z_m": parcel_initial_z,
        "parcel_final_z_m": parcel_final_z,
        "lift_delta_m": lift_delta,
        "latched": latched,
        "approach_trace": approach_trace,
        "lift_trace": lift_trace,
        "suction": suction.summary(),
        "success": success,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload))
    return 0 if success else 2


if __name__ == "__main__":
    raise SystemExit(main())
