from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_mobile_pi05_success_collection_plan",
    ROOT / "scripts/build_mobile_pi05_success_collection_plan.py",
)
assert SPEC is not None and SPEC.loader is not None
PLANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLANNER)

COLLECTOR_SPEC = importlib.util.spec_from_file_location(
    "collect_mobile_suction_dataset_rocm",
    ROOT / "scripts/collect_mobile_suction_dataset_rocm.py",
)
assert COLLECTOR_SPEC is not None and COLLECTOR_SPEC.loader is not None
COLLECTOR = importlib.util.module_from_spec(COLLECTOR_SPEC)
COLLECTOR_SPEC.loader.exec_module(COLLECTOR)


class BuildMobilePI05SuccessCollectionPlanTests(unittest.TestCase):
    def test_plan_is_balanced_unique_and_collector_valid(self) -> None:
        plan = PLANNER.build_plan(10, 20260729, "pilot")
        episodes = plan["episodes"]

        self.assertEqual(len(episodes), 30)
        self.assertEqual(plan["collection_id"], "parcel-success-pilot-v4")
        self.assertEqual(plan["protocol"], "pi05-success-anchor-one-factor-collection-v4")
        self.assertEqual(len({item["episode_id"] for item in episodes}), 30)
        self.assertEqual(len({item["source_identity"] for item in episodes}), 30)
        self.assertEqual(
            [item["grasp_mode"] for item in episodes[:3]], list(PLANNER.GRASP_MODES)
        )
        seen: set[str] = set()
        for item in episodes:
            COLLECTOR._validate_episode(item, seen)
            self.assertEqual(
                item["demonstration_provenance"],
                "deterministic_expert_candidate",
            )
        for mode in PLANNER.GRASP_MODES:
            selected = [item for item in episodes if item["grasp_mode"] == mode]
            self.assertEqual(len(selected), 10)
            self.assertEqual(len({item["design_cell"] for item in selected}), 8)
        top = [item for item in episodes if item["grasp_mode"] == "top_suction"]
        self.assertEqual({item["retry_index"] for item in top}, {0})
        self.assertFalse(
            any("recovery_contact_offset_m" in item for item in top),
            "nominal top-suction demonstrations must not contain recovery offsets",
        )
        self.assertEqual(
            {item["profile"] for item in top},
            {"micro_box", "flat_mailer", "small_carton"},
        )
        self.assertEqual(
            {item["parameter_envelope_revision"] for item in top},
            {"top-success-anchor-one-factor-v4"},
        )
        self.assertTrue(all("anchor_provenance" in item for item in top))
        cradle = [
            item for item in episodes if item["grasp_mode"] == "cooperative_cradle"
        ]
        self.assertEqual(
            {item["parameter_envelope_revision"] for item in cradle},
            {"cradle-success-anchor-path-v3"},
        )
        self.assertTrue(all("anchor_provenance" in item for item in cradle))

    def test_one_factor_design_changes_only_its_declared_field(self) -> None:
        anchor = PLANNER.TOP_SUCTION_ANCHORS["micro_box"][0]
        expected_keys = (
            "size_m",
            "size_m",
            "size_m",
            "mass_kg",
            "friction",
            "offset_m",
            "offset_m",
            "yaw_rad",
        )
        baseline = {
            key: list(value) if isinstance(value, tuple) else float(value)
            for key, value in anchor.items()
        }
        for design_cell, expected_key in enumerate(expected_keys):
            physical, provenance = PLANNER._single_factor_perturbation(
                anchor,
                design_cell,
                1.0,
                size_relative=0.005,
                mass_relative=0.01,
                friction_relative=0.01,
                offset_delta_m=0.0005,
                yaw_delta_rad=0.005,
            )
            changed = {key for key in baseline if physical[key] != baseline[key]}
            self.assertEqual(changed, {expected_key})
            self.assertEqual(provenance["one_factor_cell"], design_cell)

        cradle, provenance = PLANNER._interpolate_anchor_path(
            PLANNER.CRADLE_ANCHORS, 0.5
        )
        self.assertEqual(
            cradle["recovery_contact_offset_m"],
            list(PLANNER.CRADLE_ANCHORS[1]["recovery_contact_offset_m"]),
        )
        self.assertEqual(
            cradle["recovery_left_lift_offset_m"],
            list(PLANNER.CRADLE_ANCHORS[1]["recovery_left_lift_offset_m"]),
        )
        self.assertEqual(provenance["anchor_lower_index"], 1)
        self.assertEqual(provenance["anchor_alpha"], 0.0)

    def test_plan_is_reproducible_and_seed_sensitive(self) -> None:
        first = PLANNER.build_plan(8, 11, "pilot")
        repeated = PLANNER.build_plan(8, 11, "pilot")
        changed = PLANNER.build_plan(8, 12, "pilot")

        self.assertEqual(first, repeated)
        self.assertNotEqual(first["episodes"], changed["episodes"])

    def test_bulk_target_matches_fifty_examples_per_design_cell(self) -> None:
        plan = PLANNER.build_plan(960, 20260729, "bulk")

        self.assertEqual(plan["planned_attempts"], 2880)
        self.assertEqual(sum(plan["success_quotas_by_design_cell"].values()), 1500)
        self.assertEqual(len(plan["success_quotas_by_design_cell"]), 24)
        self.assertEqual(
            set(plan["success_quotas_by_design_cell"].values()), {62, 63}
        )
        self.assertEqual(plan["target_success_dataset"]["train"], 1200)
        self.assertEqual(
            plan["literature_alignment"]["target_domain_examples_per_cell"], 50
        )
        self.assertEqual(
            plan["training_mixture"]["bootstrap_behavior_cloning"][
                "verified_target_successes"
            ],
            1.0,
        )
        attempts_by_cell: dict[str, int] = {}
        for item in plan["episodes"]:
            cell = item["design_cell"]
            attempts_by_cell[cell] = attempts_by_cell.get(cell, 0) + 1
        self.assertEqual(set(attempts_by_cell.values()), {120})
        self.assertEqual(
            set(
                plan["target_success_dataset"][
                    "candidate_attempts_by_design_cell"
                ].values()
            ),
            {120},
        )

        physical_keys = (
            "size_m",
            "mass_kg",
            "friction",
            "offset_m",
            "yaw_rad",
            "recovery_contact_offset_m",
            "recovery_contact_penetration_delta_m",
            "recovery_vertical_speed_scale",
            "recovery_left_lift_offset_m",
            "recovery_right_lift_offset_m",
        )
        physical_signatures = {
            json.dumps(
                {
                    "grasp_mode": item["grasp_mode"],
                    **{key: item[key] for key in physical_keys if key in item},
                },
                sort_keys=True,
            )
            for item in plan["episodes"]
        }
        self.assertEqual(len(physical_signatures), plan["planned_attempts"])

    def test_bulk_plan_rejects_an_impossible_candidate_budget(self) -> None:
        with self.assertRaisesRegex(ValueError, "below its success quota"):
            PLANNER.build_plan(499, 20260729, "bulk")

    def test_yield_and_quota_statistics_use_successful_episodes_only(self) -> None:
        results = [
            {
                "success": True,
                "parameters": {
                    "grasp_mode": "top_suction",
                    "design_cell": "top_suction-cell-00",
                },
            },
            {
                "success": False,
                "parameters": {
                    "grasp_mode": "top_suction",
                    "design_cell": "top_suction-cell-00",
                },
            },
            {
                "success": True,
                "parameters": {
                    "grasp_mode": "side_suction",
                    "design_cell": "side_suction-cell-00",
                },
            },
        ]
        modes = COLLECTOR._mode_statistics(
            results, ["top_suction", "side_suction", "cooperative_cradle"]
        )
        self.assertEqual(modes["top_suction"]["attempts"], 2)
        self.assertEqual(modes["top_suction"]["success_rate"], 0.5)
        self.assertIsNone(modes["cooperative_cradle"]["success_rate"])

        quota = COLLECTOR._quota_statistics(
            results,
            {"top_suction-cell-00": 1, "side_suction-cell-00": 2},
        )
        self.assertEqual(quota["accepted_successes"], 2)
        self.assertEqual(quota["remaining_by_design_cell"]["top_suction-cell-00"], 0)
        self.assertEqual(quota["remaining_by_design_cell"]["side_suction-cell-00"], 1)
        self.assertFalse(quota["complete"])

    def test_pilot_yield_gate_waits_for_every_mode_and_fails_closed(self) -> None:
        pending = COLLECTOR._pilot_yield_gate(
            {
                "top_suction": {
                    "attempts": 10,
                    "successes": 9,
                    "success_rate": 0.9,
                },
                "side_suction": {
                    "attempts": 10,
                    "successes": 8,
                    "success_rate": 0.8,
                },
                "cooperative_cradle": {
                    "attempts": 9,
                    "successes": 9,
                    "success_rate": 1.0,
                },
            },
            10,
            0.7,
        )
        self.assertEqual(pending["status"], "pending")

        failed = COLLECTOR._pilot_yield_gate(
            {
                "top_suction": {
                    "attempts": 10,
                    "successes": 9,
                    "success_rate": 0.9,
                },
                "side_suction": {
                    "attempts": 10,
                    "successes": 8,
                    "success_rate": 0.8,
                },
                "cooperative_cradle": {
                    "attempts": 10,
                    "successes": 6,
                    "success_rate": 0.6,
                },
            },
            10,
            0.7,
        )
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(failed["failed_modes"], ["cooperative_cradle"])

        passed = COLLECTOR._pilot_yield_gate(
            {
                "top_suction": {
                    "attempts": 10,
                    "successes": 7,
                    "success_rate": 0.7,
                },
                "side_suction": {
                    "attempts": 10,
                    "successes": 8,
                    "success_rate": 0.8,
                },
                "cooperative_cradle": {
                    "attempts": 10,
                    "successes": 9,
                    "success_rate": 0.9,
                },
            },
            10,
            0.7,
        )
        self.assertEqual(passed["status"], "passed")

        futile = COLLECTOR._pilot_yield_gate(
            {
                "top_suction": {
                    "attempts": 5,
                    "successes": 1,
                    "success_rate": 0.2,
                },
                "side_suction": {
                    "attempts": 5,
                    "successes": 5,
                    "success_rate": 1.0,
                },
                "cooperative_cradle": {
                    "attempts": 4,
                    "successes": 1,
                    "success_rate": 0.25,
                },
            },
            10,
            0.7,
        )
        self.assertEqual(futile["status"], "failed")
        self.assertEqual(futile["required_successes_per_mode"], 7)
        self.assertEqual(futile["futile_modes"], ["top_suction"])

    def test_collection_success_requires_a_saved_nonempty_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "episode"
            summary = {"success": True, "dataset": {"saved": True, "frames": 90}}

            self.assertFalse(
                COLLECTOR._verified_collection_success(
                    0, summary, audit_only=False, dataset_root=root
                )
            )
            root.mkdir()
            self.assertTrue(
                COLLECTOR._verified_collection_success(
                    0, summary, audit_only=False, dataset_root=root
                )
            )
            summary["dataset"]["frames"] = 0
            self.assertFalse(
                COLLECTOR._verified_collection_success(
                    0, summary, audit_only=False, dataset_root=root
                )
            )
            self.assertTrue(
                COLLECTOR._verified_collection_success(
                    0,
                    {"success": True},
                    audit_only=True,
                    dataset_root=Path(temporary) / "missing",
                )
            )


if __name__ == "__main__":
    unittest.main()
