from dataclasses import replace
import math
from pathlib import Path
import unittest

from parcel_sorter.config import load_config
from parcel_sorter.contracts import ControlDecision, RobotState
from parcel_sorter.expert import ScriptedPickPlaceExpert, canonical_grasp_yaw
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.state_machine import Command


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ScriptedExpertTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        self.sample = DomainRandomizer(self.config.randomization, self.config.seed).sample(0)
        self.expert = ScriptedPickPlaceExpert(self.config, self.sample)
        self.state = RobotState(
            joint_positions=(0.0,) * 9,
            end_effector_pose=(0.35, 0.0, 0.35, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=(0.60, 0.10, 0.02, 1.0, 0.0, 0.0, 0.0),
            target_position=self.expert.destination_position,
            gripper_contact_force_n=0.0,
        )

    def test_pregrasp_action_is_bounded_and_opens_gripper(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        action = self.expert.action(decision, self.state)
        squared_distance = sum(
            (target - current) ** 2
            for target, current in zip(action.target_position, self.state.end_effector_pose[:3], strict=True)
        )
        self.assertLessEqual(squared_distance ** 0.5, self.config.control.max_ee_step_m + 1e-9)
        self.assertGreater(action.gripper, 0)

    def test_pregrasp_rises_vertically_before_crossing_workspace(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        state = RobotState(
            joint_positions=self.state.joint_positions,
            end_effector_pose=(0.35, 0.0, 0.10, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=self.state.parcel_pose,
            target_position=self.state.target_position,
            gripper_contact_force_n=0.0,
        )

        action = self.expert.action(decision, state)

        self.assertAlmostEqual(action.target_position[0], state.end_effector_pose[0])
        self.assertAlmostEqual(action.target_position[1], state.end_effector_pose[1])
        self.assertGreater(action.target_position[2], state.end_effector_pose[2])

    def test_pregrasp_moves_horizontally_only_at_transit_height(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        parcel = self.state.parcel_pose
        transit_z = parcel[2] + self.config.task.approach_clearance_m
        state = RobotState(
            joint_positions=self.state.joint_positions,
            end_effector_pose=(0.35, 0.0, transit_z, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=parcel,
            target_position=self.state.target_position,
            gripper_contact_force_n=0.0,
        )

        action = self.expert.action(decision, state)

        self.assertAlmostEqual(action.target_position[2], transit_z)
        self.assertGreater(action.target_position[0], state.end_effector_pose[0])

    def test_final_pregrasp_descent_uses_reduced_step_limit(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        parcel = self.state.parcel_pose
        candidate_config = replace(
            self.config,
            control=replace(self.config.control, final_approach_step_m=0.01),
        )
        candidate_expert = ScriptedPickPlaceExpert(candidate_config, self.sample)
        state = RobotState(
            joint_positions=self.state.joint_positions,
            end_effector_pose=(parcel[0], parcel[1], 0.30, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=parcel,
            target_position=self.state.target_position,
            gripper_contact_force_n=0.0,
        )

        action = candidate_expert.action(decision, state)
        distance = math.dist(action.target_position, state.end_effector_pose[:3])

        self.assertAlmostEqual(distance, candidate_config.control.final_approach_step_m)
        self.assertLess(distance, candidate_config.control.max_ee_step_m)

    def test_lift_and_drop_keep_gripper_closed(self) -> None:
        for command in (Command.MOVE_LIFT, Command.MOVE_DROP):
            action = self.expert.action(ControlDecision("test", command.value, "test", 0), self.state)
            self.assertLess(action.gripper, 0)

    def test_retry_lift_uses_latest_grasp_location(self) -> None:
        close = ControlDecision("grasp", Command.CLOSE_GRIPPER.value, "test", 1)
        self.expert.action(close, self.state)
        lift = ControlDecision("lift", Command.MOVE_LIFT.value, "test", 1)

        action = self.expert.action(lift, self.state)

        self.assertGreater(action.target_position[0], self.state.end_effector_pose[0])
        self.assertGreater(action.target_position[1], self.state.end_effector_pose[1])

    def test_gripper_orientation_tracks_parcel_yaw(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        sample = replace(self.sample, yaw_rad=0.8)
        expert = ScriptedPickPlaceExpert(self.config, sample)

        action = expert.action(decision, self.state)

        self.assertAlmostEqual(action.target_quaternion[0], 0.0)
        self.assertAlmostEqual(action.target_quaternion[1], math.cos(sample.yaw_rad / 2))
        self.assertAlmostEqual(action.target_quaternion[2], math.sin(sample.yaw_rad / 2))
        self.assertAlmostEqual(action.target_quaternion[3], 0.0)

    def test_grasp_yaw_uses_symmetry_and_wrist_limit(self) -> None:
        self.assertAlmostEqual(canonical_grasp_yaw(-2.234778763), 0.906813891)
        self.assertEqual(canonical_grasp_yaw(-1.5037), 0.0)

    def test_gripper_keeps_downward_orientation_until_safe_height(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        state = RobotState(
            joint_positions=self.state.joint_positions,
            end_effector_pose=(0.35, 0.0, 0.10, 1.0, 0.0, 0.0, 0.0),
            parcel_pose=self.state.parcel_pose,
            target_position=self.state.target_position,
            gripper_contact_force_n=0.0,
        )

        action = self.expert.action(decision, state)

        self.assertEqual(action.target_quaternion, (0.0, 1.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
