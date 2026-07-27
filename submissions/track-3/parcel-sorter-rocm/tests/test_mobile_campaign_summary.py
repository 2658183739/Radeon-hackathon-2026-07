import unittest

from scripts.summarize_mobile_vla_campaign import _profile_summaries


class MobileCampaignSummaryTests(unittest.TestCase):
    def test_groups_success_and_failure_by_profile(self) -> None:
        runs = [
            {
                "profile": "small_carton",
                "success": True,
                "placement_error_m": 0.01,
                "failure_stage": None,
                "suction": {"max_contact_force_n": 4.0},
            },
            {
                "profile": "small_carton",
                "success": False,
                "placement_error_m": 0.20,
                "failure_stage": "lift_success",
                "suction": {"max_contact_force_n": 5.0},
            },
            {
                "profile": "flat_mailer",
                "success": True,
                "placement_error_m": 0.02,
                "failure_stage": None,
                "suction": {"max_contact_force_n": 3.0},
            },
        ]
        result = _profile_summaries(runs)
        self.assertEqual(result["small_carton"]["successes"], 1)
        self.assertEqual(result["small_carton"]["trials"], 2)
        self.assertEqual(
            result["small_carton"]["failure_stages"], {"lift_success": 1}
        )
        self.assertEqual(result["flat_mailer"]["success_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
