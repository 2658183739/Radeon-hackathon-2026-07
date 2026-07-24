from collections import Counter
from pathlib import Path
import unittest

from parcel_sorter.config import load_config
from parcel_sorter.genesis_env import parcel_spawn_spec
from parcel_sorter.randomization import DomainRandomizer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ParcelCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(PROJECT_ROOT / "configs" / "catalog_v1.toml")
        self.randomizer = DomainRandomizer(
            self.config.randomization,
            self.config.seed,
            self.config.parcel_profiles,
        )

    def test_training_block_has_exact_predeclared_mix(self) -> None:
        counts = Counter(
            self.randomizer.sample(index).profile_id
            for index in range(self.config.randomization.catalog_block_size)
        )

        self.assertEqual(
            counts,
            Counter(
                {
                    profile.profile_id: round(
                        profile.selection_weight
                        * self.config.randomization.catalog_block_size
                    )
                    for profile in self.config.parcel_profiles
                    if not profile.evaluation_only
                }
            ),
        )

    def test_profile_dimensions_stay_inside_declared_ranges(self) -> None:
        profile = next(item for item in self.config.parcel_profiles if item.profile_id == "long_box")
        sample = self.randomizer.sample_profile(profile.profile_id, 123)

        self.assertEqual(sample.shape, "box")
        self.assertTrue(
            all(
                lower <= value <= upper
                for lower, value, upper in zip(
                    profile.dimensions_min_m,
                    sample.dimensions_m,
                    profile.dimensions_max_m,
                    strict=True,
                )
            )
        )

    def test_real_carrier_profile_remains_evaluation_only(self) -> None:
        sample = self.randomizer.sample_profile("usps_medium_flat_rate", 7)

        self.assertEqual(sample.handling_class, "suction_required")
        self.assertEqual(sample.dimensions_m, (0.28575, 0.22225, 0.1524))

    def test_horizontal_tube_maps_to_cylinder_axis(self) -> None:
        sample = self.randomizer.sample_profile("mailing_tube", 8)
        spec = parcel_spawn_spec(self.config, sample)

        self.assertEqual(spec.shape, "cylinder")
        self.assertEqual(spec.euler_degrees[1], 90.0)
        self.assertAlmostEqual(spec.cylinder_height_m, sample.dimensions_m[0])
        self.assertAlmostEqual(spec.cylinder_radius_m, sample.dimensions_m[1] / 2)
        self.assertAlmostEqual(spec.initial_z_m, sample.dimensions_m[2] / 2)

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown parcel profile"):
            self.randomizer.sample_profile("not-real", 0)


if __name__ == "__main__":
    unittest.main()
