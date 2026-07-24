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
        self.assertEqual(config.task.left_bin_center_m, (0.48, -0.34, 0.025))


if __name__ == "__main__":
    unittest.main()
