import unittest

import numpy as np

from parcel_sorter.genesis_env import genesis_depth_to_meters


class GenesisDepthTests(unittest.TestCase):
    def test_converts_camera_depth_from_millimeters_to_meters(self) -> None:
        depth_mm = np.asarray([[800.0, 3418.5]], dtype=np.float32)

        depth_m = genesis_depth_to_meters(depth_mm, np)

        np.testing.assert_allclose(depth_m, [[0.8, 3.4185]], rtol=1e-6)
        self.assertEqual(depth_m.dtype, np.float32)


if __name__ == "__main__":
    unittest.main()
