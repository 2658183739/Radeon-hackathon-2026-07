import unittest

from parcel_sorter.mobile_adaptive_retry import (
    EXPERT_RECOVERY,
    PASH_ARM,
    PASH_BASE,
    PASH_DUAL_ARM,
    EpisodicStrategyMemory,
    build_primitive_acquisition_manifest,
    choose_retry_strategy,
    classify_mobile_failure,
    strategy_context,
    summarize_adaptive_attempts,
)


class MobileAdaptiveRetryTests(unittest.TestCase):
    def test_classifies_force_before_task_gate(self) -> None:
        summary = {
            "success": False,
            "latched": False,
            "suction": {"max_contact_force_n": 35.0},
        }
        self.assertEqual(classify_mobile_failure(summary), "force_safety_abort")

    def test_force_abort_permits_only_expert_recovery(self) -> None:
        memory = EpisodicStrategyMemory()
        selected = choose_retry_strategy(
            memory=memory,
            context="small_carton:medium:force_safety_abort",
            previous_failure="force_safety_abort",
            attempted_strategy_names=(PASH_ARM.name,),
        )
        self.assertEqual(selected, EXPERT_RECOVERY)

    def test_precision_failure_removes_arm_authority(self) -> None:
        memory = EpisodicStrategyMemory()
        selected = choose_retry_strategy(
            memory=memory,
            context="small_carton:medium:placement_success",
            previous_failure="placement_success",
        )
        self.assertEqual(selected, PASH_BASE)

    def test_cooperative_payload_selects_rigid_safe_dual_arm_projection(self) -> None:
        selected = choose_retry_strategy(
            memory=EpisodicStrategyMemory(),
            context="long_carton:medium:initial",
            previous_failure=None,
            cooperative_cradle=True,
        )
        self.assertEqual(selected, PASH_DUAL_ARM)
        self.assertTrue(selected.cooperative_safe)
        self.assertTrue(selected.depth_sidecar)

    def test_cooperative_precision_failure_removes_dual_arm_authority(self) -> None:
        selected = choose_retry_strategy(
            memory=EpisodicStrategyMemory(),
            context="long_carton:medium:placement_success",
            previous_failure="placement_success",
            cooperative_cradle=True,
        )
        self.assertEqual(selected, PASH_BASE)

    def test_memory_penalizes_force_aborts_and_retains_outcomes(self) -> None:
        context = strategy_context(
            profile="small_carton", mass_kg=0.5, previous_failure=None
        )
        memory = EpisodicStrategyMemory()
        memory.record(
            context=context, strategy=PASH_ARM, success=False, force_abort=True
        )
        memory.record(
            context=context, strategy=PASH_BASE, success=True, force_abort=False
        )
        selected = choose_retry_strategy(
            memory=memory, context=context, previous_failure=None
        )
        self.assertEqual(selected, PASH_BASE)
        payload = memory.to_dict()
        self.assertEqual(payload["contexts"][context][PASH_ARM.name]["force_aborts"], 1)
        self.assertEqual(
            payload["contexts"]["*:medium:initial"][PASH_BASE.name]["successes"], 1
        )

    def test_summary_separates_first_attempt_from_eventual_success(self) -> None:
        summary = summarize_adaptive_attempts(
            [
                {
                    "attempt_index": 0,
                    "summary_available": True,
                    "success": False,
                    "failure_stage": "lift_success",
                    "strategy": PASH_ARM.to_dict(),
                },
                {
                    "attempt_index": 1,
                    "summary_available": True,
                    "success": True,
                    "failure_stage": None,
                    "strategy": PASH_BASE.to_dict(),
                },
            ]
        )
        self.assertFalse(summary["first_attempt_success"])
        self.assertTrue(summary["eventual_success"])
        self.assertEqual(summary["attempts_to_success"], 2)
        self.assertEqual(summary["primitive_gaps"], ["lift_success"])

    def test_primitive_gap_recovery_becomes_audited_writeback_candidate(self) -> None:
        attempts = [
            {
                "attempt_index": 0,
                "summary_available": True,
                "summary": "attempt-1/summary.json",
                "success": False,
                "failure_stage": "suction_latch",
                "strategy": PASH_ARM.to_dict(),
            },
            {
                "attempt_index": 1,
                "summary_available": True,
                "summary": "attempt-2/summary.json",
                "success": True,
                "failure_stage": None,
                "strategy": PASH_BASE.to_dict(),
            },
        ]
        manifest = build_primitive_acquisition_manifest(attempts)
        self.assertEqual(manifest["retraining_candidate_count"], 1)
        self.assertEqual(
            manifest["successful_acquisitions"][0]["primitive"], "suction_latch"
        )
        self.assertEqual(
            manifest["successful_acquisitions"][0]["writeback_status"],
            "eligible_after_dataset_audit",
        )


if __name__ == "__main__":
    unittest.main()
