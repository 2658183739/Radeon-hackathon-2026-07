import math
import unittest

from parcel_sorter.mobile_task import (
    MOBILE_BIMANUAL_ACTION_DIM,
    MobileBimanualTaskSupervisor,
    MobileTaskObservation,
    decode_mobile_bimanual_action,
    limit_mobile_arm_step,
)


class MobileBimanualActionTests(unittest.TestCase):
    def test_decodes_normalizes_and_bounds_nineteen_dimensional_action(self) -> None:
        arm = (0.4, 0.1, 0.2, 2.0, 0.0, 0.0, 0.0, -0.2)
        action = decode_mobile_bimanual_action((1.0, 1.0, 4.0, *arm, *arm))
        self.assertEqual(MOBILE_BIMANUAL_ACTION_DIM, 19)
        self.assertAlmostEqual(math.hypot(*action.base_velocity_xy_yaw[:2]), 0.35)
        self.assertEqual(action.base_velocity_xy_yaw[2], 1.0)
        self.assertEqual(action.left.quaternion_wxyz, (1.0, 0.0, 0.0, 0.0))
        self.assertEqual(action.left.gripper, -1.0)

    def test_rejects_invalid_action_and_limits_cartesian_step(self) -> None:
        with self.assertRaisesRegex(ValueError, "19"):
            decode_mobile_bimanual_action((0.0,) * 18)
        arm = (0.2, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
        bounded = limit_mobile_arm_step(
            decode_mobile_bimanual_action((0.0, 0.0, 0.0, *arm, *arm)).left,
            (0.0, 0.0, 0.0),
        )
        self.assertAlmostEqual(bounded.position_m[0], 0.04)


class MobileTaskSupervisorTests(unittest.TestCase):
    def test_completes_navigation_bimanual_pick_transport_and_place(self) -> None:
        supervisor = MobileBimanualTaskSupervisor()
        observations = (
            MobileTaskObservation(base_at_pickup=True),
            MobileTaskObservation(arms_at_pregrasp=True),
            MobileTaskObservation(left_grasp_contact=True, right_grasp_contact=True),
            MobileTaskObservation(parcel_lifted=True),
            MobileTaskObservation(base_at_destination=True),
            MobileTaskObservation(parcel_placed=True),
            MobileTaskObservation(grippers_open=True),
            MobileTaskObservation(arms_retreated=True),
        )
        decision = None
        for observation in observations:
            decision = supervisor.step(observation)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.stage, "complete")

    def test_force_gate_aborts_without_using_retry_budget(self) -> None:
        supervisor = MobileBimanualTaskSupervisor(max_retries=2)
        decision = supervisor.step(MobileTaskObservation(excessive_contact_force=True))
        self.assertEqual(decision.stage, "abort")
        self.assertEqual(decision.retry_count, 0)

    def test_drop_retries_then_aborts(self) -> None:
        supervisor = MobileBimanualTaskSupervisor(max_retries=1)
        self.assertEqual(
            supervisor.step(MobileTaskObservation(parcel_dropped=True)).stage,
            "navigate_pickup",
        )
        self.assertEqual(
            supervisor.step(MobileTaskObservation(parcel_dropped=True)).stage,
            "abort",
        )


if __name__ == "__main__":
    unittest.main()
