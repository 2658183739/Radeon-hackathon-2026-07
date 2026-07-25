from __future__ import annotations

import argparse
from pathlib import Path
import tempfile
import unittest

from scripts.run_grasp_candidate_collection import planned_runs, run


class GraspCandidateCollectionTests(unittest.TestCase):
    def _protocol(self, directory: str) -> Path:
        path = Path(directory) / "protocol.toml"
        path.write_text(
            """
[[splits]]
name = "train"
profile_id = "medium_carton"
episode_ids = [2, 1]

[[splits]]
name = "holdout"
profile_id = "medium_carton"
episode_ids = [3]
""".strip(),
            encoding="utf-8",
        )
        return path

    def test_plans_split_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            rows = planned_runs(
                self._protocol(directory),
                "train",
                Path(directory) / "output",
            )

        self.assertEqual([row["episode"] for row in rows], [1, 2])
        self.assertEqual(
            Path(rows[0]["output"]).parts[-3:],
            ("train", "medium_carton", "1.json"),
        )

    def test_holdout_is_locked_before_any_process_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = self._protocol(directory)
            args = argparse.Namespace(
                protocol=protocol,
                split="holdout",
                output_dir=Path(directory) / "output",
                config=Path(directory) / "config.toml",
                backend="rocm",
                max_candidates=6,
                repeats=1,
                resume=False,
                dry_run=True,
                unlock_holdout=False,
            )
            with self.assertRaisesRegex(PermissionError, "holdout collection is locked"):
                run(args)

    def test_dry_run_does_not_create_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            protocol = self._protocol(directory)
            output = Path(directory) / "output"
            args = argparse.Namespace(
                protocol=protocol,
                split="train",
                output_dir=output,
                config=Path(directory) / "config.toml",
                backend="rocm",
                max_candidates=6,
                repeats=1,
                resume=False,
                dry_run=True,
                unlock_holdout=False,
            )

            result = run(args)

            self.assertEqual(result["planned_episode_count"], 2)
            self.assertEqual(result["planned_max_rollouts"], 12)
            self.assertFalse((output / "train/manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
