import unittest

from parcel_sorter.mobile_dataset import (
    MOBILE_ACTION_NAMES,
    MOBILE_PRIVILEGED_STATE_NAMES,
    MOBILE_STAGE_NAMES,
    MOBILE_STATE_NAMES,
    MobileBimanualFrame,
    mobile_policy_visual_keys,
)


class MobileDatasetContractTests(unittest.TestCase):
    def test_declares_smolvla_compatible_mobile_contract(self) -> None:
        self.assertEqual(len(MOBILE_STATE_NAMES), 43)
        self.assertEqual(len(MOBILE_ACTION_NAMES), 19)
        self.assertEqual(len(MOBILE_PRIVILEGED_STATE_NAMES), 7)
        self.assertEqual(len(MOBILE_STAGE_NAMES), 6)
        self.assertEqual(len(set(MOBILE_STATE_NAMES)), len(MOBILE_STATE_NAMES))

    def test_frame_rejects_wrong_feature_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "43"):
            MobileBimanualFrame(0, 0.0, "pregrasp", (0.0,) * 42, (0.0,) * 19, (0.0,) * 7, "task")
        with self.assertRaisesRegex(ValueError, "19"):
            MobileBimanualFrame(0, 0.0, "pregrasp", (0.0,) * 43, (0.0,) * 18, (0.0,) * 7, "task")

    def test_frame_rejects_unknown_stage(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown mobile task stage"):
            MobileBimanualFrame(
                0, 0.0, "unknown", (0.0,) * 43, (0.0,) * 19, (0.0,) * 7, "task"
            )

    def test_declares_distinct_rgb_and_rgbd_policy_contracts(self) -> None:
        self.assertEqual(
            mobile_policy_visual_keys("rgb"),
            ("observation.images.overhead_rgb",),
        )
        self.assertEqual(
            mobile_policy_visual_keys("rgbd"),
            (
                "observation.images.overhead_rgb",
                "observation.images.overhead_depth_rgb",
            ),
        )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            mobile_policy_visual_keys("depth-only")


if __name__ == "__main__":
    unittest.main()
