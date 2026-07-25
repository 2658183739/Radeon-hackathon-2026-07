from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from scripts import run_expert


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RunExpertCliTests(unittest.TestCase):
    def test_reset_pose_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--reset-qpos",
            *("nan" for _ in range(9)),
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("reset_qpos must contain nine finite joint positions", stderr.getvalue())
        environment.assert_not_called()

    def test_size_aware_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--size-aware-approach",
            "--approach-clearance-margin",
            "-0.01",
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("approach_clearance_margin_m", stderr.getvalue())
        environment.assert_not_called()

    def test_retry_retreat_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--retry-retreat-distance",
            "-0.01",
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("retry_retreat_distance_m", stderr.getvalue())
        environment.assert_not_called()

    def test_approach_step_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--approach-step",
            "0.05",
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("approach_step_m", stderr.getvalue())
        environment.assert_not_called()

    def test_approach_contact_brake_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--approach-contact-brake-force",
            "35.0",
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("approach_contact_brake_force_n", stderr.getvalue())
        environment.assert_not_called()

    def test_approach_barrier_recovery_override_is_validated_before_environment_creation(self) -> None:
        argv = [
            "run_expert.py",
            "--config",
            str(PROJECT_ROOT / "configs" / "catalog_v2.toml"),
            "--backend",
            "cpu",
            "--episodes",
            "1",
            "--approach-barrier-recovery-step",
            "0.17",
        ]

        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch.object(run_expert, "GenesisParcelEnv") as environment,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_expert.main()

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("approach_barrier_recovery_step_m", stderr.getvalue())
        environment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
