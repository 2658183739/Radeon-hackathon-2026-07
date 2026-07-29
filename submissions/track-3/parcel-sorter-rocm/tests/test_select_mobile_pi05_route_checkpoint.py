import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).parents[1]
    / "scripts"
    / "select_mobile_pi05_route_checkpoint.py"
)
SPEC = importlib.util.spec_from_file_location("select_pi05_checkpoint", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

SUMMARY_SCRIPT = (
    Path(__file__).parents[1]
    / "scripts"
    / "summarize_mobile_pi05_mode_screen.py"
)
SUMMARY_SPEC = importlib.util.spec_from_file_location(
    "summarize_mobile_pi05_mode_screen_for_selection", SUMMARY_SCRIPT
)
SUMMARY_MODULE = importlib.util.module_from_spec(SUMMARY_SPEC)
assert SUMMARY_SPEC.loader is not None
SUMMARY_SPEC.loader.exec_module(SUMMARY_MODULE)


def _write_checkpoint(root: Path, step: int) -> Path:
    checkpoint = root / "checkpoints" / f"{step:06d}" / "pretrained_model"
    checkpoint.mkdir(parents=True)
    for name in (
        "adapter_model.safetensors",
        "adapter_config.json",
        "config.json",
    ):
        (checkpoint / name).write_text(name, encoding="utf-8")
    (root / "PI05_TRAINING_CONTRACT.json").write_text(
        "training-contract", encoding="utf-8"
    )
    return checkpoint


def _write_screen(root: Path, step: int, *, passed: bool = True) -> Path:
    checkpoint = _write_checkpoint(root, step)
    path = root / f"step-{step}.json"
    payload = {
        "protocol": MODULE.SCREEN_PROTOCOL,
        "status": "passed" if passed else "failed",
        "checkpoint": str(checkpoint),
        "dataset": "/frozen/development",
        "observation_panel_role": MODULE.PANEL_ROLE,
        "sample_seeds": [11, 12, 13],
        "errors": [] if passed else ["mode_error"],
        "metrics": {
            "probes": 6,
            "correct_probes": 6 if passed else 5,
            "probe_accuracy": 1.0 if passed else 5 / 6,
            "macro_mode_accuracy": 1.0 if passed else 5 / 6,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class PI05RouteCheckpointSelectionTests(unittest.TestCase):
    def test_selector_accepts_the_current_screen_summary_protocol(self) -> None:
        summary = SUMMARY_MODULE.summarize_mode_screen(
            [
                {
                    "checkpoint": "/checkpoint",
                    "dataset": "/dataset",
                    "expected_grasp_mode": mode,
                    "predicted_grasp_mode": mode,
                    "grasp_mode_conditioned": False,
                    "sample_count": 3,
                    "grasp_mode_correct": True,
                    "finite": True,
                    "material_residual": True,
                    "fallback_to_expert": False,
                    "policy_type": "pi05",
                }
                for mode in SUMMARY_MODULE.PI05_GRASP_MODES
            ]
        )

        self.assertEqual(summary["protocol"], MODULE.SCREEN_PROTOCOL)

    def test_selects_earliest_checkpoint_among_equal_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screens = [_write_screen(root, step) for step in (12000, 3000, 9000, 6000)]

            result = MODULE.select_checkpoint(screens, expected_count=4)

            self.assertEqual(result["selected_step"], 3000)
            self.assertFalse(result["heldout_observations_accessed"])
            self.assertFalse(result["closed_loop_results_accessed"])
            self.assertEqual(len(result["candidates"]), 4)

    def test_rejects_incomplete_screen_panel(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screens = [_write_screen(root, step) for step in (3000, 6000, 9000)]

            with self.assertRaisesRegex(ValueError, "expected 4"):
                MODULE.select_checkpoint(screens, expected_count=4)

    def test_skips_a_failed_earlier_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screens = [
                _write_screen(root, 3000, passed=False),
                _write_screen(root, 6000),
                _write_screen(root, 9000),
                _write_screen(root, 12000),
            ]

            result = MODULE.select_checkpoint(screens, expected_count=4)

            self.assertEqual(result["selected_step"], 6000)


if __name__ == "__main__":
    unittest.main()
