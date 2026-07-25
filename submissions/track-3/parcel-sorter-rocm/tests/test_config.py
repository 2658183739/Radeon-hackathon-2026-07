from dataclasses import replace
from pathlib import Path
import unittest

from parcel_sorter.config import load_config


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_baseline_config_is_valid(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        self.assertEqual(config.simulation.backend, "rocm")
        self.assertEqual(config.simulation.device, "cuda:0")
        self.assertEqual(config.simulation.physics_hz, 240)
        self.assertEqual(config.simulation.control_hz, 30)
        self.assertEqual(config.simulation.camera_hz, 10)
        self.assertTrue(config.sensors.depth)
        self.assertTrue(config.randomization.enabled)
        self.assertEqual(len(config.control.arm_kp), 7)
        self.assertEqual(len(config.control.reset_qpos), 9)
        self.assertLessEqual(config.control.final_approach_step_m, config.control.max_ee_step_m)
        self.assertEqual(config.task.left_bin_center_m, (0.48, -0.34, 0.025))

    def test_final_approach_limit_cannot_exceed_global_limit(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(config.control, final_approach_step_m=0.05),
        )

        with self.assertRaisesRegex(ValueError, "final_approach_step_m"):
            invalid.validate()

    def test_approach_step_cannot_exceed_global_limit(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(config.control, approach_step_m=0.05),
        )

        with self.assertRaisesRegex(ValueError, "approach_step_m"):
            invalid.validate()

    def test_approach_contact_brake_threshold_stays_below_safety_limit(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(config.control, approach_contact_brake_force_n=35.0),
        )

        with self.assertRaisesRegex(ValueError, "approach_contact_brake_force_n"):
            invalid.validate()

    def test_approach_barrier_recovery_step_is_bounded(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(
                config.control,
                approach_barrier_recovery_step_m=config.control.max_ee_step_m * 4.01,
            ),
        )

        with self.assertRaisesRegex(ValueError, "approach_barrier_recovery_step_m"):
            invalid.validate()

    def test_precontact_aabb_guard_distance_is_bounded(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(
                config.control,
                precontact_aabb_guard_distance_m=config.control.max_ee_step_m * 4.01,
            ),
        )

        with self.assertRaisesRegex(ValueError, "precontact_aabb_guard_distance_m"):
            invalid.validate()

    def test_approach_stiffness_scale_is_at_most_one(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(config.control, approach_stiffness_scale=1.01),
        )

        with self.assertRaisesRegex(ValueError, "approach_stiffness_scale"):
            invalid.validate()

    def test_approach_velocity_parameters_are_positive_and_bounded(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            control=replace(config.control, approach_velocity_damping=1.01),
        )

        with self.assertRaisesRegex(ValueError, "approach_velocity_damping"):
            invalid.validate()
        invalid_weight = replace(
            config,
            control=replace(config.control, approach_velocity_orientation_weight=1.01),
        )
        with self.assertRaisesRegex(ValueError, "orientation_weight"):
            invalid_weight.validate()

    def test_parcel_profile_rejects_negative_rolling_friction(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "catalog_v2.toml")
        invalid_profile = replace(config.parcel_profiles[0], rolling_friction=-0.001)
        invalid = replace(
            config,
            parcel_profiles=(invalid_profile, *config.parcel_profiles[1:]),
        )

        with self.assertRaisesRegex(ValueError, "rolling_friction"):
            invalid.validate()

    def test_reset_pose_requires_nine_finite_values(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(config, control=replace(config.control, reset_qpos=(0.0,) * 8))

        with self.assertRaisesRegex(ValueError, "reset_qpos"):
            invalid.validate()

    def test_approach_clearance_margin_must_be_non_negative(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            task=replace(config.task, approach_clearance_margin_m=-0.001),
        )

        with self.assertRaisesRegex(ValueError, "approach_clearance_margin_m"):
            invalid.validate()

    def test_retry_retreat_distance_must_be_non_negative(self) -> None:
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        invalid = replace(
            config,
            task=replace(config.task, retry_retreat_distance_m=-0.001),
        )

        with self.assertRaisesRegex(ValueError, "retry_retreat_distance_m"):
            invalid.validate()


if __name__ == "__main__":
    unittest.main()
