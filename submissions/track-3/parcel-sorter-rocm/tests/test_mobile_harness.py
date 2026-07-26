import math
import unittest

from parcel_sorter.mobile_harness import (
    build_mobile_failure_replay_manifest,
    select_mobile_harness_action,
)


def _state(*, force_n: float = 0.0) -> tuple[float, ...]:
    values = [0.0] * 43
    values[24:31] = [0.40, 0.10, 0.30, 1.0, 0.0, 0.0, 0.0]
    values[31:38] = [0.40, -0.10, 0.30, 1.0, 0.0, 0.0, 0.0]
    values[38:40] = [force_n, 0.0]
    return tuple(values)


def _action(*, left_tool: float = 1.0) -> tuple[float, ...]:
    return (
        0.03, 0.0, 0.0,
        0.42, 0.10, 0.30, 1.0, 0.0, 0.0, 0.0, left_tool,
        0.42, -0.10, 0.30, 1.0, 0.0, 0.0, 0.0, 1.0,
    )


class MobileHarnessTests(unittest.TestCase):
    def test_selects_largest_safe_bounded_residual(self) -> None:
        expert = _action()
        vla = list(expert)
        vla[0] = 0.20
        vla[3] = 0.50
        decision = select_mobile_harness_action(
            state=_state(), expert_action=expert, vla_action=vla, stage="transport"
        )
        self.assertFalse(decision.emergency_stop)
        self.assertGreater(decision.selected.scale, 0.0)
        self.assertLessEqual(math.hypot(*decision.selected.action[:2]), 0.05)
        self.assertLessEqual(math.dist(decision.selected.action[3:6], _state()[24:27]), 0.04)

    def test_stage_interlock_corrects_release_tool_command(self) -> None:
        expert = _action(left_tool=-1.0)
        vla = _action(left_tool=1.0)
        decision = select_mobile_harness_action(
            state=_state(), expert_action=expert, vla_action=vla, stage="release"
        )
        self.assertEqual(decision.selected.action[10], -1.0)
        self.assertEqual(decision.selected.tool_command_corrections, 1)
        self.assertIn("stage_tool_interlock", decision.selected.reasons)

    def test_near_contact_base_residual_preserves_nominal_progress(self) -> None:
        expert = list(_action())
        expert[:3] = [0.002, 0.010, 0.0]
        vla = list(expert)
        vla[:3] = [0.002, -0.010, 0.0]
        decision = select_mobile_harness_action(
            state=_state(), expert_action=expert, vla_action=vla, stage="grasp_approach"
        )
        selected = decision.selected.action
        progress = (selected[0] * expert[0] + selected[1] * expert[1]) / (
            expert[0] ** 2 + expert[1] ** 2
        )
        self.assertGreaterEqual(progress, 0.5)
        self.assertGreaterEqual(selected[1], 0.0)
        self.assertTrue(decision.fallback_to_expert)
        self.assertIn("contact_precision_handoff", decision.selected.reasons)

    def test_force_gate_stops_base_holds_arms_and_releases_suction(self) -> None:
        decision = select_mobile_harness_action(
            state=_state(force_n=35.0),
            expert_action=_action(),
            vla_action=_action(),
            stage="lift",
        )
        self.assertTrue(decision.emergency_stop)
        self.assertEqual(decision.selected.action[:3], (0.0, 0.0, 0.0))
        self.assertEqual(decision.selected.action[10], -1.0)
        self.assertEqual(decision.selected.action[3:10], _state()[24:31])

    def test_invalid_vla_falls_back_to_expert(self) -> None:
        decision = select_mobile_harness_action(
            state=_state(), expert_action=_action(), vla_action=(math.nan,) * 19, stage="lift"
        )
        self.assertTrue(decision.rejected_vla)
        self.assertTrue(decision.fallback_to_expert)
        self.assertEqual(decision.selected.scale, 0.0)

    def test_mobile_failure_manifest_prioritizes_heavy_lift_boundaries(self) -> None:
        summary = {
            "results": [
                {"episode_id": "ok", "success": True},
                {
                    "episode_id": "heavy",
                    "profile": "medium_carton",
                    "success": False,
                    "failure_stage": "lift_success",
                    "max_contact_force_n": 13.4,
                    "parameters": {"mass_kg": 0.65, "friction": 0.8},
                },
                {
                    "episode_id": "light",
                    "profile": "small_carton",
                    "success": False,
                    "failure_stage": "lift_success",
                    "max_contact_force_n": 9.0,
                    "parameters": {"mass_kg": 0.55, "friction": 0.9},
                },
            ]
        }
        manifest = build_mobile_failure_replay_manifest(summary)
        self.assertEqual([item["episode_id"] for item in manifest["items"]], ["heavy", "light"])
        self.assertAlmostEqual(manifest["items"][0]["curriculum_bridge"]["mass_kg"], 0.585)
        self.assertEqual(manifest["counts_by_failure_stage"], {"lift_success": 2})


if __name__ == "__main__":
    unittest.main()
