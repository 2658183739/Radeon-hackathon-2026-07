import math
import unittest

from parcel_sorter.mobile_harness import (
    MobileHarnessConfig,
    build_mobile_failure_replay_manifest,
    force_memory_scale_cap,
    select_mobile_harness_action,
    transport_deadline_requires_expert,
)
from parcel_sorter.mobile_vla_controller import (
    evaluate_vla_goal_judgement,
    update_primitive_progress_peak,
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
    def test_progress_peak_is_latched_within_stage_and_reset_between_stages(self) -> None:
        peak = update_primitive_progress_peak(0.0, 0.92, stage_changed=True)
        self.assertEqual(peak, 0.92)
        self.assertEqual(
            update_primitive_progress_peak(peak, 0.78, stage_changed=False),
            0.92,
        )
        self.assertEqual(
            update_primitive_progress_peak(peak, 0.10, stage_changed=True),
            0.10,
        )

    def test_goal_judgement_blocks_a_transport_proposal_away_from_target(self) -> None:
        state = list(_state())
        state[0:2] = [0.0, 0.0]
        state[40:42] = [0.30, 0.0]
        judgement = evaluate_vla_goal_judgement(
            state,
            (-0.04, 0.0),
            stage="transport",
            primitive_complete=False,
            goal_xy=(0.30, 0.0),
        )
        self.assertFalse(judgement.direction_consistent)
        self.assertEqual(judgement.scale_cap, 0.0)

    def test_goal_judgement_accepts_arrival_only_inside_tolerance(self) -> None:
        state = list(_state())
        state[0:2] = [0.29, 0.0]
        state[40:42] = [0.30, 0.0]
        judgement = evaluate_vla_goal_judgement(
            state,
            (0.01, 0.0),
            stage="transport",
            primitive_complete=True,
            goal_xy=(0.30, 0.0),
        )
        self.assertTrue(judgement.arrival_claimed)
        self.assertTrue(judgement.arrival_verified)

    def test_force_memory_preserves_full_scale_for_stable_low_contact(self) -> None:
        decision = force_memory_scale_cap((4.0, 4.5, 4.2, 4.6))
        self.assertEqual(decision.scale_cap, 1.0)
        self.assertEqual(decision.reasons, ("stable_force_history",))

    def test_force_memory_caps_vla_for_rising_contact(self) -> None:
        memory = force_memory_scale_cap((4.0, 5.0, 8.0, 12.0))
        self.assertEqual(memory.scale_cap, 0.0)
        decision = select_mobile_harness_action(
            state=_state(),
            expert_action=_action(),
            vla_action=_action(),
            stage="transport",
            maximum_vla_scale=memory.scale_cap,
        )
        self.assertEqual(decision.selected.scale, 0.0)
        self.assertTrue(decision.fallback_to_expert)
        self.assertTrue(
            any(
                "force_memory_scale_gate" in candidate.reasons
                for candidate in decision.candidates
                if candidate.scale > 0.0
            )
        )

    def test_transport_deadline_handoff_preserves_completion_capacity(self) -> None:
        self.assertFalse(
            transport_deadline_requires_expert(
                distance_m=0.30,
                remaining_time_s=10.0,
                expert_forward_speed_m_s=0.05,
            )
        )
        self.assertTrue(
            transport_deadline_requires_expert(
                distance_m=0.045,
                remaining_time_s=1.0,
                expert_forward_speed_m_s=0.05,
            )
        )
        self.assertFalse(
            transport_deadline_requires_expert(
                distance_m=0.004,
                remaining_time_s=0.1,
                expert_forward_speed_m_s=0.0,
            )
        )

    def test_payload_aware_progress_floor_bounds_transport_slowdown(self) -> None:
        expert = list(_action())
        expert[:3] = [0.05, 0.0, 0.0]
        vla = list(expert)
        vla[:3] = [0.0, 0.0, 0.0]
        decision = select_mobile_harness_action(
            state=_state(),
            expert_action=expert,
            vla_action=vla,
            stage="transport",
            config=MobileHarnessConfig(min_progress_ratio=0.75),
        )
        self.assertGreater(decision.selected.scale, 0.0)
        self.assertAlmostEqual(decision.selected.min_progress_ratio, 0.75)
        self.assertAlmostEqual(decision.selected.action[0], 0.0375)

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
