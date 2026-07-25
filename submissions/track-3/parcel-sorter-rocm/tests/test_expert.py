from dataclasses import replace
import math
from pathlib import Path
import unittest

from parcel_sorter.config import load_config
from parcel_sorter.contracts import ControlDecision, RobotState
from parcel_sorter.expert import ScriptedPickPlaceExpert, canonical_grasp_yaw, profile_grasp_yaw
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

    def test_size_aware_approach_is_disabled_by_default(self) -> None:
        self.assertAlmostEqual(
            self.expert.approach_clearance_m(),
            self.config.task.approach_clearance_m,
        )

    def test_size_aware_approach_adds_only_vertical_envelope_delta_and_margin(self) -> None:
        candidate_config = replace(
            self.config,
            task=replace(
                self.config.task,
                size_aware_approach_enabled=True,
                approach_clearance_margin_m=0.02,
            ),
        )
        sample = replace(self.sample, dimensions_m=(0.30, 0.079, 0.18))
        expert = ScriptedPickPlaceExpert(candidate_config, sample)
        expected = candidate_config.task.approach_clearance_m + (0.18 / 2 - 0.04 / 2) + 0.02
        self.assertAlmostEqual(expert.approach_clearance_m(), expected)

    def test_retry_retreat_moves_laterally_before_reapproach(self) -> None:
        candidate_config = replace(
            self.config,
            task=replace(self.config.task, retry_retreat_distance_m=0.12),
        )
        expert = ScriptedPickPlaceExpert(candidate_config, self.sample)
        parcel = self.state.parcel_pose
        retry_state = replace(
            self.state,
            end_effector_pose=(parcel[0], parcel[1], 0.18, 1.0, 0.0, 0.0, 0.0),
        )
        action = expert.action(
            ControlDecision("approach", Command.MOVE_PREGRASP.value, "retry", 1),
            retry_state,
        )

        self.assertGreater(action.target_position[0], parcel[0])
        self.assertAlmostEqual(action.target_position[1], parcel[1])
        self.assertAlmostEqual(action.target_position[2], retry_state.end_effector_pose[2])
        self.assertGreater(action.gripper, 0)

    def test_final_descent_stays_committed_after_xy_alignment(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        parcel = self.state.parcel_pose
        aligned_state = replace(
            self.state,
            end_effector_pose=(parcel[0], parcel[1], 0.30, 1.0, 0.0, 0.0, 0.0),
        )
        self.expert.action(decision, aligned_state)
        drifted_state = replace(
            aligned_state,
            end_effector_pose=(parcel[0] + 0.05, parcel[1], 0.25, 1.0, 0.0, 0.0, 0.0),
        )

        action = self.expert.action(decision, drifted_state)

        self.assertLess(action.target_position[2], drifted_state.end_effector_pose[2])

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

    def test_free_space_approach_can_use_a_separate_step_limit(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        candidate_config = replace(
            self.config,
            control=replace(self.config.control, approach_step_m=0.02),
        )
        expert = ScriptedPickPlaceExpert(candidate_config, self.sample)
        action = expert.action(decision, self.state)
        distance = math.dist(action.target_position, self.state.end_effector_pose[:3])

        self.assertAlmostEqual(distance, 0.02)
        self.assertLess(distance, candidate_config.control.max_ee_step_m)

    def test_contact_brake_prioritizes_vertical_clearance(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        candidate_config = replace(
            self.config,
            control=replace(
                self.config.control,
                approach_contact_brake_force_n=20.0,
                approach_contact_brake_step_m=0.01,
            ),
        )
        expert = ScriptedPickPlaceExpert(candidate_config, self.sample)
        state = replace(
            self.state,
            end_effector_pose=(0.35, 0.0, 0.10, 1.0, 0.0, 0.0, 0.0),
            gripper_contact_force_n=20.0,
        )
        action = expert.action(decision, state)

        distance = math.dist(action.target_position, state.end_effector_pose[:3])
        self.assertGreater(action.target_position[2], state.end_effector_pose[2])
        self.assertLessEqual(distance, 0.01 + 1e-9)

    def test_approach_barrier_allows_vertical_recovery_without_horizontal_motion(self) -> None:
        decision = ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0)
        candidate_config = replace(
            self.config,
            control=replace(
                self.config.control,
                approach_barrier_recovery_step_m=0.12,
            ),
        )
        expert = ScriptedPickPlaceExpert(candidate_config, self.sample)
        state = replace(
            self.state,
            end_effector_pose=(0.35, 0.0, 0.10, 1.0, 0.0, 0.0, 0.0),
        )
        action = expert.action(decision, state)

        self.assertAlmostEqual(action.target_position[0], state.end_effector_pose[0])
        self.assertAlmostEqual(action.target_position[1], state.end_effector_pose[1])
        self.assertGreater(action.target_position[2], state.end_effector_pose[2])
        self.assertLessEqual(math.dist(action.target_position, state.end_effector_pose[:3]), 0.12 + 1e-9)

    def test_profile_can_reduce_final_approach_step(self) -> None:
        sample = replace(self.sample, final_approach_step_m=0.005)
        expert = ScriptedPickPlaceExpert(self.config, sample)
        parcel = self.state.parcel_pose
        state = replace(
            self.state,
            end_effector_pose=(parcel[0], parcel[1], 0.30, 1.0, 0.0, 0.0, 0.0),
        )

        action = expert.action(
            ControlDecision("approach", Command.MOVE_PREGRASP.value, "test", 0),
            state,
        )

        self.assertAlmostEqual(math.dist(action.target_position, state.end_effector_pose[:3]), 0.005)

    def test_profile_can_reduce_lift_step(self) -> None:
        sample = replace(self.sample, lift_step_m=0.01)
        expert = ScriptedPickPlaceExpert(self.config, sample)

        action = expert.action(
            ControlDecision("lift", Command.MOVE_LIFT.value, "test", 0),
            self.state,
        )

        self.assertAlmostEqual(math.dist(action.target_position, self.state.end_effector_pose[:3]), 0.01)
        self.assertLess(0.01, self.config.control.max_ee_step_m)

    def test_profile_can_override_pregrasp_tolerance(self) -> None:
        sample = replace(
            self.sample,
            shape="cylinder",
            orientation_mode="horizontal",
            pregrasp_tolerance_m=0.01,
        )

        self.assertAlmostEqual(ScriptedPickPlaceExpert(self.config, sample).pregrasp_tolerance_m(), 0.01)

    def test_lift_and_drop_keep_gripper_closed(self) -> None:
        for command in (Command.MOVE_LIFT, Command.MOVE_DROP):
            action = self.expert.action(ControlDecision("test", command.value, "test", 0), self.state)
            self.assertLess(action.gripper, 0)

    def test_drop_path_rises_before_translating(self) -> None:
        decision = ControlDecision("place", Command.MOVE_DROP.value, "test", 0)
        state = replace(
            self.state,
            end_effector_pose=(0.35, 0.0, 0.20, 1.0, 0.0, 0.0, 0.0),
        )

        action = self.expert.action(decision, state)

        self.assertAlmostEqual(action.target_position[0], state.end_effector_pose[0])
        self.assertAlmostEqual(action.target_position[1], state.end_effector_pose[1])
        self.assertGreater(action.target_position[2], state.end_effector_pose[2])

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

    def test_catalog_profile_uses_full_parallel_jaw_symmetry(self) -> None:
        sample = replace(self.sample, profile_id="small_carton", yaw_rad=-1.5037)
        self.assertAlmostEqual(profile_grasp_yaw(sample), -1.5037)

    def test_upright_cylinder_does_not_rotate_wrist_for_symmetric_shape(self) -> None:
        sample = replace(
            self.sample,
            profile_id="upright_canister",
            shape="cylinder",
            orientation_mode="upright",
        )
        self.assertEqual(profile_grasp_yaw(sample), 0.0)

    def test_upright_cylinder_uses_extra_palm_clearance(self) -> None:
        sample = replace(
            self.sample,
            profile_id="upright_canister",
            shape="cylinder",
            orientation_mode="upright",
        )
        expert = ScriptedPickPlaceExpert(self.config, sample)
        self.assertAlmostEqual(
            expert.grasp_hand_clearance_m(),
            self.config.task.grasp_hand_clearance_m + 0.008,
        )

    def test_horizontal_cylinder_fingers_are_parallel_to_axis(self) -> None:
        sample = replace(
            self.sample,
            profile_id="mailing_tube",
            shape="cylinder",
            orientation_mode="horizontal",
            yaw_rad=0.0,
        )
        self.assertAlmostEqual(profile_grasp_yaw(sample), 0.0)

    def test_large_nonflat_box_gets_a_larger_pregrasp_window(self) -> None:
        sample = replace(
            self.sample,
            profile_id="long_box",
            dimensions_m=(0.25, 0.06, 0.08),
        )
        expert = ScriptedPickPlaceExpert(self.config, sample)
        self.assertAlmostEqual(expert.pregrasp_tolerance_m(), 0.035)

    def test_surface_aware_pregrasp_is_disabled_by_default(self) -> None:
        sample = replace(self.sample, dimensions_m=(0.35, 0.07, 0.16))
        expert = ScriptedPickPlaceExpert(self.config, sample)
        parcel = self.state.parcel_pose
        target = expert.pregrasp_position(parcel)

        self.assertFalse(expert.at_pregrasp((target[0], target[1], target[2] + 0.04), parcel))

    def test_surface_aware_pregrasp_accepts_a_height_supported_contact_band(self) -> None:
        config = replace(
            self.config,
            task=replace(self.config.task, surface_aware_pregrasp_enabled=True),
        )
        sample = replace(self.sample, dimensions_m=(0.35, 0.07, 0.16))
        expert = ScriptedPickPlaceExpert(config, sample)
        parcel = self.state.parcel_pose
        target = expert.pregrasp_position(parcel)

        self.assertTrue(expert.at_pregrasp((target[0] + 0.005, target[1], target[2] + 0.05), parcel))

    def test_surface_aware_pregrasp_rejects_insufficient_vertical_overlap(self) -> None:
        config = replace(
            self.config,
            task=replace(self.config.task, surface_aware_pregrasp_enabled=True),
        )
        sample = replace(self.sample, dimensions_m=(0.35, 0.07, 0.16))
        expert = ScriptedPickPlaceExpert(config, sample)
        parcel = self.state.parcel_pose
        target = expert.pregrasp_position(parcel)

        self.assertFalse(expert.at_pregrasp((target[0], target[1], target[2] + 0.061), parcel))

    def test_surface_aware_pregrasp_rejects_horizontal_misalignment(self) -> None:
        config = replace(
            self.config,
            task=replace(self.config.task, surface_aware_pregrasp_enabled=True),
        )
        sample = replace(self.sample, dimensions_m=(0.35, 0.07, 0.16))
        expert = ScriptedPickPlaceExpert(config, sample)
        parcel = self.state.parcel_pose
        target = expert.pregrasp_position(parcel)

        self.assertFalse(expert.at_pregrasp((target[0] + 0.020, target[1], target[2] + 0.04), parcel))

    def test_surface_aware_pregrasp_does_not_expand_short_box_window(self) -> None:
        config = replace(
            self.config,
            task=replace(self.config.task, surface_aware_pregrasp_enabled=True),
        )
        sample = replace(self.sample, dimensions_m=(0.30, 0.07, 0.114))
        expert = ScriptedPickPlaceExpert(config, sample)
        parcel = self.state.parcel_pose
        target = expert.pregrasp_position(parcel)

        self.assertFalse(expert.at_pregrasp((target[0], target[1], target[2] + 0.04), parcel))

    def test_flat_box_keeps_the_precise_pregrasp_window(self) -> None:
        sample = replace(
            self.sample,
            profile_id="flat_box",
            dimensions_m=(0.22, 0.05, 0.035),
        )
        expert = ScriptedPickPlaceExpert(self.config, sample)
        self.assertAlmostEqual(expert.pregrasp_tolerance_m(), 0.010)

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
