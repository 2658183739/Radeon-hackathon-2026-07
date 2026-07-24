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


if __name__ == "__main__":
    unittest.main()
