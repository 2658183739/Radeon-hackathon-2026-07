import unittest

import numpy as np

from parcel_sorter.genesis_env import genesis_depth_to_meters


class GenesisDepthTests(unittest.TestCase):
    def test_preserves_genesis_depth_in_meters(self) -> None:
        raw_depth_m = np.asarray([[0.8, 3.4185]], dtype=np.float32)

        depth_m = genesis_depth_to_meters(raw_depth_m, np)

        np.testing.assert_allclose(depth_m, [[0.8, 3.4185]], rtol=1e-6)
        self.assertEqual(depth_m.dtype, np.float32)


if __name__ == "__main__":
    unittest.main()
