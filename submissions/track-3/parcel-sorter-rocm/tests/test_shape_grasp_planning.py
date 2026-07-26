from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

from parcel_sorter.config import load_config
from parcel_sorter.randomization import DomainRandomizer
from parcel_sorter.shape_grasp_planning import (
    ShapeGraspPlannerConfig,
    build_shape_grasp_plan,
    generate_shape_grasp_pose_candidates,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ShapeGraspPlanningTests(unittest.TestCase):
    def setUp(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "catalog_v2.toml")
        randomizer = DomainRandomizer(config.randomization, config.seed, config.parcel_profiles)
        self.box = replace(
            randomizer.sample_profile("large_narrow_carton", 20_000_001),
            dimensions_m=(0.320, 0.070, 0.160),
            position_xy=(0.60, 0.0),
            yaw_rad=0.0,
        )
        self.canister = replace(
            randomizer.sample_profile("upright_canister", 20_000_002),
            dimensions_m=(0.060, 0.060, 0.140),
            position_xy=(0.60, -0.06),
            yaw_rad=0.0,
        )
        self.tube = replace(
            randomizer.sample_profile("mailing_tube", 20_000_003),
            dimensions_m=(0.240, 0.050, 0.050),
            position_xy=(0.60, 0.06),
            yaw_rad=0.0,
            rolling_friction=0.005,
        )
        self.box_pose = (0.60, 0.0, 0.08, 1.0, 0.0, 0.0, 0.0)
        self.canister_pose = (0.60, -0.06, 0.07, 1.0, 0.0, 0.0, 0.0)
        self.tube_pose = (0.60, 0.06, 0.025, 0.7071067811865476, 0.0, 0.7071067811865476, 0.0)

    def test_dispatches_box_without_broadening_box_scope(self) -> None:
        plan = build_shape_grasp_plan(
            self.box,
            self.box_pose,
            hand_clearance_m=0.105,
        )

        self.assertTrue(plan.supported)
        self.assertTrue(plan.activation_eligible)
        self.assertEqual(plan.reason, "supported")
        self.assertGreater(len(plan.candidates), 0)
        self.assertTrue(all(item.approach_variant == "top_down" for item in plan.candidates))

    def test_dispatches_upright_cylinder_with_explicit_candidates(self) -> None:
        plan = build_shape_grasp_plan(
            self.canister,
            self.canister_pose,
            hand_clearance_m=0.105,
        )

        self.assertTrue(plan.supported)
        self.assertTrue(plan.activation_eligible)
        self.assertEqual(plan.reason, "supported")
        self.assertEqual(len(plan.candidates), 16)
        self.assertTrue(all(item.approach_variant == "upright_top_down_radial" for item in plan.candidates))

    def test_dispatches_horizontal_tube_and_preserves_axis_family(self) -> None:
        candidates = generate_shape_grasp_pose_candidates(
            self.tube,
            self.tube_pose,
            hand_clearance_m=0.105,
        )

        self.assertEqual(len(candidates), 18)
        self.assertTrue(all(item.approach_variant == "horizontal_cross_diameter" for item in candidates))
        self.assertEqual(len({item.candidate_id for item in candidates}), len(candidates))

    def test_unsupported_handling_class_is_explicitly_empty(self) -> None:
        boundary = replace(
            self.tube,
            handling_class="cradle_required",
            dimensions_m=(0.50, 0.10, 0.10),
        )
        plan = build_shape_grasp_plan(
            boundary,
            self.tube_pose,
            hand_clearance_m=0.105,
        )

        self.assertFalse(plan.supported)
        self.assertFalse(plan.activation_eligible)
        self.assertEqual(plan.reason, "unsupported_handling_class:cradle_required")
        self.assertEqual(plan.candidates, ())

    def test_cylinder_can_be_disabled_without_raising(self) -> None:
        plan = build_shape_grasp_plan(
            self.canister,
            self.canister_pose,
            hand_clearance_m=0.105,
            config=ShapeGraspPlannerConfig(cylinder_enabled=False),
        )

        self.assertFalse(plan.supported)
        self.assertFalse(plan.activation_eligible)
        self.assertEqual(plan.reason, "cylinder_planner_disabled")
        self.assertEqual(plan.candidates, ())

    def test_low_rolling_friction_tube_cannot_be_activated(self) -> None:
        unstable = replace(self.tube, rolling_friction=0.0)
        plan = build_shape_grasp_plan(
            unstable,
            self.tube_pose,
            hand_clearance_m=0.105,
        )

        self.assertFalse(plan.supported)
        self.assertFalse(plan.activation_eligible)
        self.assertEqual(plan.reason, "horizontal_tube_requires_guarded_support")


if __name__ == "__main__":
    unittest.main()
