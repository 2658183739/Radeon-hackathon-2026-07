import unittest

from parcel_sorter.metrics import EpisodeResult, MetricsAccumulator


class MetricsAccumulatorTests(unittest.TestCase):
    def test_summary_reports_success_recovery_and_latency(self) -> None:
        metrics = MetricsAccumulator()
        metrics.add(EpisodeResult(True, 0, 4.0, (5.0, 7.0), max_contact_force_n=10.0))
        metrics.add(EpisodeResult(True, 1, 6.0, (9.0, 11.0), max_contact_force_n=15.0))
        metrics.add(EpisodeResult(False, 2, 10.0, (13.0,), dropped=True, max_contact_force_n=20.0))

        summary = metrics.summary()

        self.assertEqual(summary["episodes"], 3)
        self.assertAlmostEqual(summary["success_rate"], 2 / 3)
        self.assertAlmostEqual(summary["first_attempt_success_rate"], 1 / 3)
        self.assertAlmostEqual(summary["recovery_success_rate"], 0.5)
        self.assertEqual(summary["p95_inference_latency_ms"], 13.0)
        self.assertEqual(summary["max_contact_force_n"], 20.0)


if __name__ == "__main__":
    unittest.main()
