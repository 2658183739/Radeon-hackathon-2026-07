import unittest

from parcel_sorter.comparison import compare_expert_runs


def _run(successes: tuple[bool, ...], forces: tuple[float, ...]) -> dict:
    episodes = [
        {
            "episode_index": index,
            "sample": {"episode_index": index, "mass_kg": 0.5 + index * 0.1},
            "result": {
                "success": success,
                "max_contact_force_n": force,
            },
        }
        for index, (success, force) in enumerate(zip(successes, forces, strict=True))
    ]
    successful = sum(successes)
    return {
        "config": {"task": {"max_contact_force_n": 35.0}},
        "summary": {
            "success_rate": successful / len(episodes),
            "drop_rate": 0.0,
            "successful_parcels_per_hour": successful * 100.0,
        },
        "episodes": episodes,
    }


class ExpertComparisonTests(unittest.TestCase):
    def test_same_episode_comparison_reports_recovery_and_force_aborts(self) -> None:
        baseline = _run((False, True), (50.0, 20.0))
        candidate = _run((True, True), (20.0, 18.0))

        result = compare_expert_runs(baseline, candidate)

        self.assertEqual(result["recovered_episode_indices"], [0])
        self.assertEqual(result["regressed_episode_indices"], [])
        self.assertEqual(result["baseline_force_abort_indices"], [0])
        self.assertEqual(result["candidate_force_abort_indices"], [])
        self.assertEqual(result["recommendation"], "keep")

    def test_mismatched_episode_sets_are_rejected(self) -> None:
        baseline = _run((True, True), (10.0, 10.0))
        candidate = _run((True,), (10.0,))

        with self.assertRaisesRegex(ValueError, "episode sets differ"):
            compare_expert_runs(baseline, candidate)

    def test_mismatched_randomization_sample_is_rejected(self) -> None:
        baseline = _run((True,), (10.0,))
        candidate = _run((True,), (10.0,))
        candidate["episodes"][0]["sample"]["mass_kg"] = 0.9

        with self.assertRaisesRegex(ValueError, "randomization samples differ"):
            compare_expert_runs(baseline, candidate)

    def test_mismatched_safety_threshold_is_rejected(self) -> None:
        baseline = _run((True,), (10.0,))
        candidate = _run((True,), (10.0,))
        candidate["config"]["task"]["max_contact_force_n"] = 40.0

        with self.assertRaisesRegex(ValueError, "thresholds differ"):
            compare_expert_runs(baseline, candidate)

    def test_config_difference_contract_requires_exact_paths(self) -> None:
        baseline = _run((True,), (10.0,))
        candidate = _run((True,), (10.0,))
        baseline["config"]["control"] = {"reset_qpos": [0.0, 1.0]}
        candidate["config"]["control"] = {"reset_qpos": [0.5, 1.0]}

        result = compare_expert_runs(
            baseline,
            candidate,
            allowed_config_differences=("control.reset_qpos",),
        )
        self.assertEqual(result["config_difference_paths"], ["control.reset_qpos"])

        candidate["config"]["task"]["episode_seconds"] = 30.0
        with self.assertRaisesRegex(ValueError, "unexpected=.*task.episode_seconds"):
            compare_expert_runs(
                baseline,
                candidate,
                allowed_config_differences=("control.reset_qpos",),
            )


if __name__ == "__main__":
    unittest.main()
