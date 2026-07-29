import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "summarize_mobile_pi05_mode_screen.py"
SPEC = importlib.util.spec_from_file_location("summarize_mobile_pi05_mode_screen", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _probe(mode: str) -> dict:
    return {
        "checkpoint": "/checkpoint",
        "dataset": "/dataset",
        "expected_grasp_mode": mode,
        "predicted_grasp_mode": mode,
        "grasp_mode_conditioned": False,
        "sample_count": 3,
        "sample_seeds": [20260727, 20260728, 20260729],
        "sampling_seed_protocol": "common-random-numbers-per-observation-v1",
        "grasp_mode_correct": True,
        "finite": True,
        "material_residual": True,
        "fallback_to_expert": False,
        "policy_type": "pi05",
        "mode_vote_counts": {mode: 3},
        "mode_consensus_fraction": 1.0,
        "maximum_residual_norm": 0.001,
        "mean_latency_ms": 450.0,
    }


def _absolute_probe(mode: str) -> dict:
    probe = _probe(mode)
    probe.update(
        {
            "action_contract": "pi05_absolute_v1",
            "material_residual": None,
            "material_action": True,
            "maximum_absolute_motion": 0.04,
            "expert_reference_used": False,
            "pure_vla_qualified": True,
            "selected_scale_min": 1.0,
            "action_fidelity": {
                "finite": True,
                "median_maximum_arm_position_l2_m": 0.02,
                "maximum_maximum_arm_position_l2_m": 0.04,
                "median_maximum_arm_orientation_error_rad": 0.2,
                "maximum_maximum_arm_orientation_error_rad": 0.3,
                "median_base_velocity_l2": 0.01,
                "maximum_base_velocity_l2": 0.02,
                "median_progress_absolute_error": 0.1,
                "left_tool_accuracy": 1.0,
                "right_tool_accuracy": 1.0,
            },
        }
    )
    return probe


class MobilePI05ModeScreenTests(unittest.TestCase):
    def test_passes_complete_hidden_three_mode_screen(self) -> None:
        probes = [
            _probe("top_suction"),
            _probe("side_suction"),
            _probe("cooperative_cradle"),
        ]
        summary = MODULE.summarize_mode_screen(probes)
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["error_count"], 0)
        self.assertEqual(summary["metrics"]["probe_accuracy"], 1.0)
        self.assertEqual(summary["metrics"]["macro_mode_accuracy"], 1.0)
        self.assertEqual(summary["sample_seeds"], [20260727, 20260728, 20260729])

    def test_rejects_wrong_mode_or_expert_fallback(self) -> None:
        probes = [
            _probe("top_suction"),
            _probe("side_suction"),
            _probe("cooperative_cradle"),
        ]
        probes[1]["grasp_mode_correct"] = False
        probes[2]["fallback_to_expert"] = True
        summary = MODULE.summarize_mode_screen(probes)
        self.assertEqual(summary["status"], "failed")
        self.assertIn("side_suction:mode_correct", summary["errors"])
        self.assertIn("cooperative_cradle:no_expert_fallback", summary["errors"])
        self.assertEqual(summary["metrics"]["probe_accuracy"], 2 / 3)

    def test_absolute_screen_requires_no_reference_and_full_authority(self) -> None:
        probes = [_absolute_probe(mode) for mode in MODULE.PI05_GRASP_MODES]
        passed = MODULE.summarize_mode_screen(probes)
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["action_contract"], "pi05_absolute_v1")

        probes[0]["expert_reference_used"] = True
        probes[1]["selected_scale_min"] = 0.75
        failed = MODULE.summarize_mode_screen(probes)
        self.assertIn("top_suction:no_expert_reference", failed["errors"])
        self.assertIn("side_suction:full_absolute_authority", failed["errors"])

    def test_supports_strict_replicated_mode_coverage(self) -> None:
        probes = []
        for mode in MODULE.PI05_GRASP_MODES:
            probes.extend([_probe(mode), _probe(mode)])

        summary = MODULE.summarize_mode_screen(probes, min_probes_per_mode=2)

        self.assertEqual(summary["status"], "passed")
        self.assertEqual(
            summary["probe_counts_by_mode"],
            {
                "top_suction": 2,
                "side_suction": 2,
                "cooperative_cradle": 2,
            },
        )

    def test_optional_action_fidelity_gate_fails_closed(self) -> None:
        probes = [_absolute_probe(mode) for mode in MODULE.PI05_GRASP_MODES]
        probes[1]["action_fidelity"]["median_maximum_arm_position_l2_m"] = 0.2
        probes[2].pop("action_fidelity")

        summary = MODULE.summarize_mode_screen(
            probes, require_action_fidelity=True
        )

        self.assertEqual(summary["status"], "failed")
        self.assertIn(
            "side_suction:action_fidelity_median_arm_position", summary["errors"]
        )
        self.assertIn(
            "cooperative_cradle:action_fidelity_available", summary["errors"]
        )

    def test_rejects_inconsistent_common_random_number_panel(self) -> None:
        probes = [
            _probe("top_suction"),
            _probe("side_suction"),
            _probe("cooperative_cradle"),
        ]
        probes[1]["sample_seeds"] = [20260730, 20260731, 20260732]

        summary = MODULE.summarize_mode_screen(probes)

        self.assertEqual(summary["status"], "failed")
        self.assertIn("sampling_seed_panel_mismatch", summary["errors"])

    def test_keeps_legacy_artifacts_without_seed_metadata_compatible(self) -> None:
        probes = [
            _probe("top_suction"),
            _probe("side_suction"),
            _probe("cooperative_cradle"),
        ]
        for probe in probes:
            probe.pop("sample_seeds")
            probe.pop("sampling_seed_protocol")

        summary = MODULE.summarize_mode_screen(probes)

        self.assertEqual(summary["status"], "passed")
        self.assertIsNone(summary["sample_seeds"])


if __name__ == "__main__":
    unittest.main()
