from __future__ import annotations

import importlib.util
from pathlib import Path
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
        plan = PLANNER.build_plan(30, 20260729, "pilot")
        episodes = plan["episodes"]

        self.assertEqual(len(episodes), 90)
        self.assertEqual(len({item["episode_id"] for item in episodes}), 90)
        self.assertEqual(len({item["source_identity"] for item in episodes}), 90)
        seen: set[str] = set()
        for item in episodes:
            COLLECTOR._validate_episode(item, seen)
        for mode in PLANNER.GRASP_MODES:
            selected = [item for item in episodes if item["grasp_mode"] == mode]
            self.assertEqual(len(selected), 30)
            self.assertEqual(len({item["design_cell"] for item in selected}), 8)

    def test_plan_is_reproducible_and_seed_sensitive(self) -> None:
        first = PLANNER.build_plan(8, 11, "pilot")
        repeated = PLANNER.build_plan(8, 11, "pilot")
        changed = PLANNER.build_plan(8, 12, "pilot")

        self.assertEqual(first, repeated)
        self.assertNotEqual(first["episodes"], changed["episodes"])

    def test_bulk_target_matches_fifty_examples_per_design_cell(self) -> None:
        plan = PLANNER.build_plan(500, 20260729, "bulk")

        self.assertEqual(plan["planned_attempts"], 1500)
        self.assertEqual(plan["target_success_dataset"]["train"], 1200)
        self.assertEqual(
            plan["literature_alignment"]["target_domain_examples_per_cell"], 50
        )


if __name__ == "__main__":
    unittest.main()
