import json
from pathlib import Path
import tempfile
import unittest

from parcel_sorter.contracts import CartesianAction, RobotState, TrajectoryFrame
from parcel_sorter.dataset import JsonlTrajectoryWriter, STATE_NAMES


class JsonlTrajectoryWriterTests(unittest.TestCase):
    def test_writes_auditable_episode_without_serializing_images(self) -> None:
        frame = TrajectoryFrame(
            frame_index=0,
            timestamp_seconds=0.0,
            stage="approach",
            state=RobotState((0.0,) * 9, (0.0,) * 7, (0.0,) * 7, (0.0,) * 3, 0.0),
            action=CartesianAction((0.1, 0.2, 0.3), (0.0, 1.0, 0.0, 0.0), 1.0, "move_pregrasp"),
            task="sort parcel",
            rgb=object(),
        )
        with tempfile.TemporaryDirectory() as directory:
            writer = JsonlTrajectoryWriter(directory)
            writer.add_frame(frame)
            path = writer.save_episode(2, {"success": True})
            payload = json.loads(path.read_text(encoding="utf-8"))
            manifest = json.loads((Path(directory) / "episodes.jsonl").read_text(encoding="utf-8"))

        self.assertTrue(payload["has_rgb"])
        self.assertNotIn("rgb", payload)
        self.assertEqual(manifest["frames"], 1)
        self.assertEqual(len(frame.state.policy_vector()), len(STATE_NAMES))


if __name__ == "__main__":
    unittest.main()
