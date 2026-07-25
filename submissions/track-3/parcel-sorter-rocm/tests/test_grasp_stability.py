from __future__ import annotations

import unittest

from parcel_sorter.grasp_stability import (
    DynamicGraspThresholds,
    dynamic_grasp_is_stable,
    rank_dynamic_grasp_evaluations,
)


class DynamicGraspStabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.thresholds = DynamicGraspThresholds()

    @staticmethod
    def evaluation(candidate_id: str, **overrides: object) -> dict[str, object]:
        row: dict[str, object] = {
            "candidate_id": candidate_id,
            "seed_name": "current",
            "static_rank": 0,
            "captured": True,
            "final_dual_contact": True,
            "safety_aborted": False,
            "finite": True,
            "parcel_lift_m": 0.025,
            "max_relative_step_m": 0.004,
            "max_downward_step_m": 0.003,
            "peak_contact_force_n": 20.0,
            "dual_contact_fraction": 0.95,
            "final_relative_drift_m": 0.005,
        }
        row.update(overrides)
        return row

    def test_stable_rollout_passes_all_frozen_gates(self) -> None:
        self.assertTrue(
            dynamic_grasp_is_stable(self.evaluation("stable"), self.thresholds)
        )

    def test_each_safety_or_retention_failure_rejects_rollout(self) -> None:
        failures = (
            {"captured": False},
            {"final_dual_contact": False},
            {"safety_aborted": True},
            {"finite": False},
            {"parcel_lift_m": 0.019},
            {"max_relative_step_m": 0.0081},
            {"max_downward_step_m": 0.0061},
            {"peak_contact_force_n": 35.1},
            {"dual_contact_fraction": 0.79},
        )
        for overrides in failures:
            with self.subTest(overrides=overrides):
                self.assertFalse(
                    dynamic_grasp_is_stable(
                        self.evaluation("rejected", **overrides),
                        self.thresholds,
                    )
                )

    def test_stable_candidate_outranks_better_static_but_unstable_candidate(self) -> None:
        unstable = self.evaluation(
            "static-first",
            static_rank=0,
            final_dual_contact=False,
        )
        stable = self.evaluation("dynamic-first", static_rank=4)

        ranked = rank_dynamic_grasp_evaluations(
            (unstable, stable),
            self.thresholds,
        )

        self.assertEqual(ranked[0]["candidate_id"], "dynamic-first")

    def test_stable_candidates_use_retention_before_static_rank(self) -> None:
        weaker_retention = self.evaluation(
            "static-first",
            static_rank=0,
            dual_contact_fraction=0.85,
        )
        stronger_retention = self.evaluation(
            "retention-first",
            static_rank=3,
            dual_contact_fraction=1.0,
        )

        ranked = rank_dynamic_grasp_evaluations(
            (weaker_retention, stronger_retention),
            self.thresholds,
        )

        self.assertEqual(ranked[0]["candidate_id"], "retention-first")

    def test_threshold_validation_rejects_invalid_fraction(self) -> None:
        with self.assertRaisesRegex(ValueError, "min_dual_contact_fraction"):
            DynamicGraspThresholds(min_dual_contact_fraction=1.1).validate()


if __name__ == "__main__":
    unittest.main()
