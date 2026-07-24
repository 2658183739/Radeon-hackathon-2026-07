import unittest

from parcel_sorter.evaluation import aggregate_checkpoint_evaluations


def _payload(checkpoint: str, episode_index: int, success: bool, latency: float) -> dict:
    return {
        "checkpoint": checkpoint,
        "episodes": [
            {
                "episode_index": episode_index,
                "result": {
                    "success": success,
                    "retries": 0,
                    "duration_seconds": 2.0,
                    "inference_latency_ms": [latency],
                    "dropped": False,
                    "max_contact_force_n": 12.0,
                },
            }
        ],
    }


class CheckpointEvaluationTests(unittest.TestCase):
    def test_non_overlapping_ranges_are_combined(self) -> None:
        records = [
            ("a.json", _payload("checkpoint-4000", 10, True, 2.0)),
            ("b.json", _payload("checkpoint-4000", 11, False, 4.0)),
        ]

        aggregate = aggregate_checkpoint_evaluations(records)[0]

        self.assertEqual(aggregate.episodes, 2)
        self.assertEqual(aggregate.episode_indices, (10, 11))
        self.assertEqual(aggregate.success_rate, 0.5)
        self.assertEqual(aggregate.mean_inference_latency_ms, 3.0)

    def test_duplicate_episode_is_rejected(self) -> None:
        records = [
            ("a.json", _payload("checkpoint-4000", 10, True, 2.0)),
            ("b.json", _payload("checkpoint-4000", 10, False, 4.0)),
        ]

        with self.assertRaisesRegex(ValueError, "repeats episode 10"):
            aggregate_checkpoint_evaluations(records)

    def test_task_success_has_priority_over_latency(self) -> None:
        records = [
            ("slow.json", _payload("checkpoint-4000", 10, True, 8.0)),
            ("fast.json", _payload("checkpoint-5000", 10, False, 1.0)),
        ]

        ranked = aggregate_checkpoint_evaluations(records)

        self.assertEqual(ranked[0].checkpoint, "checkpoint-4000")


if __name__ == "__main__":
    unittest.main()
