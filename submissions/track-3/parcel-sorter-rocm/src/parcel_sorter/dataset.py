from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .contracts import TrajectoryFrame


STATE_NAMES = (
    *(f"joint_{index}" for index in range(9)),
    "ee_x",
    "ee_y",
    "ee_z",
    "ee_qw",
    "ee_qx",
    "ee_qy",
    "ee_qz",
    "target_x",
    "target_y",
    "target_z",
    "contact_force_n",
)
PRIVILEGED_STATE_NAMES = (
    "parcel_x",
    "parcel_y",
    "parcel_z",
    "parcel_qw",
    "parcel_qx",
    "parcel_qy",
    "parcel_qz",
)
ACTION_NAMES = ("x", "y", "z", "qw", "qx", "qy", "qz", "gripper")


class JsonlTrajectoryWriter:
    """Dependency-free audit log for expert episodes and evaluation traces."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._frames: list[dict[str, Any]] = []

    def add_frame(self, frame: TrajectoryFrame) -> None:
        payload = asdict(frame)
        payload.pop("rgb", None)
        payload.pop("depth", None)
        payload["has_rgb"] = frame.rgb is not None
        payload["has_depth"] = frame.depth is not None
        self._frames.append(payload)

    def assert_episode_available(self, episode_index: int) -> None:
        """Fail before simulation rather than silently replacing prior evidence."""
        episode_path = self.root / f"episode_{episode_index:06d}.jsonl"
        if episode_path.exists():
            raise FileExistsError(
                f"audit episode already exists: {episode_path}; use a new output shard"
            )

    def save_episode(self, episode_index: int, metadata: dict[str, Any]) -> Path:
        self.assert_episode_available(episode_index)
        episode_path = self.root / f"episode_{episode_index:06d}.jsonl"
        with episode_path.open("w", encoding="utf-8", newline="\n") as handle:
            for frame in self._frames:
                handle.write(json.dumps(frame, ensure_ascii=False, separators=(",", ":")))
                handle.write("\n")

        manifest_path = self.root / "episodes.jsonl"
        manifest = {"episode_index": episode_index, "frames": len(self._frames), **metadata}
        with manifest_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")
        self._frames.clear()
        return episode_path


class LeRobotTrajectoryWriter:
    """Thin adapter around the pinned LeRobotDataset writer."""

    def __init__(
        self,
        root: str | Path,
        fps: int,
        image_size: tuple[int, int],
        include_rgb: bool,
        include_depth: bool,
        repo_id: str = "local/parcel-sorter-expert",
    ) -> None:
        try:
            from lerobot.datasets.lerobot_dataset import LeRobotDataset
        except ImportError as exc:
            raise RuntimeError(
                "LeRobot is not installed; rerun bootstrap with INSTALL_LEROBOT=1"
            ) from exc

        width, height = image_size
        features: dict[str, dict[str, Any]] = {
            "observation.state": {
                "dtype": "float32",
                "shape": (len(STATE_NAMES),),
                "names": list(STATE_NAMES),
            },
            "action": {
                "dtype": "float32",
                "shape": (len(ACTION_NAMES),),
                "names": list(ACTION_NAMES),
            },
            "observation.privileged_state": {
                "dtype": "float32",
                "shape": (len(PRIVILEGED_STATE_NAMES),),
                "names": list(PRIVILEGED_STATE_NAMES),
            },
        }
        if include_rgb:
            features["observation.images.overhead_rgb"] = {
                "dtype": "image",
                "shape": (height, width, 3),
                "names": ["height", "width", "channels"],
            }
        if include_depth:
            features["observation.images.overhead_depth"] = {
                "dtype": "image",
                "shape": (height, width, 1),
                "names": ["height", "width", "channels"],
                "info": {"is_depth_map": True},
            }
        self._include_rgb = include_rgb
        self._include_depth = include_depth
        self._dataset = LeRobotDataset.create(
            repo_id=repo_id,
            root=Path(root),
            fps=fps,
            features=features,
            robot_type="franka_panda_sim",
            use_videos=False,
            image_writer_threads=4 if include_rgb or include_depth else 0,
        )

    def add_frame(self, frame: TrajectoryFrame) -> None:
        import numpy as np

        payload: dict[str, Any] = {
            "observation.state": np.asarray(frame.state.policy_vector(), dtype=np.float32),
            "observation.privileged_state": np.asarray(
                frame.state.privileged_vector(), dtype=np.float32
            ),
            "action": np.asarray(frame.action.vector(), dtype=np.float32),
            "task": frame.task,
        }
        if self._include_rgb:
            if frame.rgb is None:
                raise ValueError("RGB recording is enabled but the frame has no RGB image")
            payload["observation.images.overhead_rgb"] = np.asarray(frame.rgb, dtype=np.uint8)[..., :3]
        if self._include_depth:
            if frame.depth is None:
                raise ValueError("depth recording is enabled but the frame has no depth image")
            depth = np.asarray(frame.depth, dtype=np.float32)
            payload["observation.images.overhead_depth"] = depth[..., None] if depth.ndim == 2 else depth
        self._dataset.add_frame(payload)

    def save_episode(self) -> None:
        self._dataset.save_episode()

    def clear_episode(self) -> None:
        self._dataset.clear_episode_buffer()

    def finalize(self) -> None:
        self._dataset.finalize()
