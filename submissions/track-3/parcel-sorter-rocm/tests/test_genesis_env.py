import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from parcel_sorter.config import load_config
from parcel_sorter.contracts import CartesianAction
from parcel_sorter.genesis_env import GenesisParcelEnv, aabb_gap_m, genesis_depth_to_meters


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class GenesisDepthTests(unittest.TestCase):
    def test_preserves_genesis_depth_in_meters(self) -> None:
        raw_depth_m = np.asarray([[0.8, 3.4185]], dtype=np.float32)

        depth_m = genesis_depth_to_meters(raw_depth_m, np)

        np.testing.assert_allclose(depth_m, [[0.8, 3.4185]], rtol=1e-6)
        self.assertEqual(depth_m.dtype, np.float32)


class AabbGapTests(unittest.TestCase):
    def test_separated_boxes_use_euclidean_axis_gap(self) -> None:
        first = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        second = ((2.0, 3.0, 1.0), (3.0, 4.0, 2.0))

        self.assertAlmostEqual(aabb_gap_m(first, second), np.sqrt(5.0))

    def test_overlapping_boxes_have_zero_gap(self) -> None:
        first = ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        second = ((0.5, -1.0, 0.2), (2.0, 0.5, 0.8))

        self.assertEqual(aabb_gap_m(first, second), 0.0)

    def test_rejects_malformed_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "min and max"):
            aabb_gap_m(((0.0, 0.0, 0.0),), ((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))


class PrecontactAabbGuardTests(unittest.TestCase):
    def _environment(
        self,
        end_effector_position: tuple[float, float, float],
        parcel_position: tuple[float, float, float],
    ) -> GenesisParcelEnv:
        env = GenesisParcelEnv.__new__(GenesisParcelEnv)
        config = load_config(PROJECT_ROOT / "configs" / "baseline.toml")
        env.config = replace(
            config,
            control=replace(config.control, precontact_aabb_guard_distance_m=0.04),
        )
        env.end_effector = SimpleNamespace(
            get_pos=lambda: np.asarray(end_effector_position, dtype=np.float32)
        )
        env.parcel = SimpleNamespace(
            get_pos=lambda: np.asarray(parcel_position, dtype=np.float32)
        )
        env.expert = SimpleNamespace(approach_clearance_m=lambda: 0.26)
        env._finger_parcel_aabb_gap_m = lambda: 0.01
        env._aabb_guard_filter_count = 0
        env._aabb_guard_active_steps = 0
        env._aabb_guard_max_active_steps = 0
        env._aabb_guard_samples = 0
        env._aabb_guard_compute_ms_total = 0.0
        env._aabb_guard_last_gap_m = None
        env._aabb_guard_last_compute_ms = 0.0
        env._aabb_guard_last_triggered = False
        env._aabb_guard_last_reason = None
        env._aabb_guard_last_nominal_target_m = None
        env._aabb_guard_last_filtered_target_m = None
        return env

    def test_filters_horizontal_approach_into_vertical_recovery(self) -> None:
        env = self._environment((0.30, 0.0, 0.10), (0.60, 0.0, 0.05))
        action = CartesianAction(
            target_position=(0.34, 0.0, 0.10),
            target_quaternion=(0.0, 1.0, 0.0, 0.0),
            gripper=1.0,
            command="move_pregrasp",
        )

        filtered = env._filter_precontact_action(action)

        self.assertAlmostEqual(filtered.target_position[0], 0.30, places=6)
        self.assertGreater(filtered.target_position[2], 0.10)
        self.assertEqual(env._aabb_guard_filter_count, 1)
        self.assertEqual(env._aabb_guard_last_reason, "raise_to_transit")

    def test_does_not_filter_inside_final_descent_window(self) -> None:
        env = self._environment((0.59, 0.0, 0.20), (0.60, 0.0, 0.05))
        action = CartesianAction(
            target_position=(0.60, 0.0, 0.18),
            target_quaternion=(0.0, 1.0, 0.0, 0.0),
            gripper=1.0,
            command="move_pregrasp",
        )

        filtered = env._filter_precontact_action(action)

        self.assertEqual(filtered, action)
        self.assertEqual(env._aabb_guard_filter_count, 0)


if __name__ == "__main__":
    unittest.main()
