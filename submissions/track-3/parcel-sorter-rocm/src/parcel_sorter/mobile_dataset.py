"""LeRobot dataset contract for the mobile bimanual parcel platform."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dataset import DEPTH_RGB_KEY, metric_depth_to_visual_rgb


MOBILE_RGB_KEY = "observation.images.overhead_rgb"
MOBILE_DEPTH_KEY = "observation.images.overhead_depth"
MOBILE_DEPTH_RGB_KEY = DEPTH_RGB_KEY
MOBILE_POLICY_MODALITIES = ("rgb", "rgbd")


def mobile_policy_visual_keys(modality: str) -> tuple[str, ...]:
    """Return the audited camera contract for a mobile policy modality."""

    if modality == "rgb":
        return (MOBILE_RGB_KEY,)
    if modality == "rgbd":
        return (MOBILE_RGB_KEY, MOBILE_DEPTH_RGB_KEY)
    raise ValueError(f"unsupported mobile policy modality: {modality!r}")


MOBILE_STATE_NAMES = (
    "base_x",
    "base_y",
    "base_yaw",
    "base_vx",
    "base_vy",
    "base_vyaw",
    *(f"left_arm_joint_{index}" for index in range(7)),
    "left_finger_joint_0",
    "left_finger_joint_1",
    *(f"right_arm_joint_{index}" for index in range(7)),
    "right_finger_joint_0",
    "right_finger_joint_1",
    *(f"left_ee_{name}" for name in ("x", "y", "z", "qw", "qx", "qy", "qz")),
    *(f"right_ee_{name}" for name in ("x", "y", "z", "qw", "qx", "qy", "qz")),
    "left_contact_force_n",
    "right_contact_force_n",
    "goal_x",
    "goal_y",
    "goal_yaw",
)
MOBILE_ACTION_NAMES = (
    "base_vx",
    "base_vy",
    "base_vyaw",
    *(f"left_{name}" for name in ("x", "y", "z", "qw", "qx", "qy", "qz", "gripper")),
    *(f"right_{name}" for name in ("x", "y", "z", "qw", "qx", "qy", "qz", "gripper")),
)
MOBILE_PRIVILEGED_STATE_NAMES = (
    "parcel_x",
    "parcel_y",
    "parcel_z",
    "parcel_qw",
    "parcel_qx",
    "parcel_qy",
    "parcel_qz",
)
MOBILE_STAGE_NAMES = (
    "pregrasp",
    "grasp_approach",
    "lift",
    "transport",
    "place",
    "release",
)


@dataclass(frozen=True)
class MobileBimanualFrame:
    frame_index: int
    timestamp_seconds: float
    stage: str
    state: tuple[float, ...]
    action: tuple[float, ...]
    privileged_state: tuple[float, ...]
    task: str
    rgb: Any | None = None
    depth: Any | None = None

    def __post_init__(self) -> None:
        if self.stage not in MOBILE_STAGE_NAMES:
            raise ValueError(f"unknown mobile task stage: {self.stage}")
        if len(self.state) != len(MOBILE_STATE_NAMES):
            raise ValueError(
                f"mobile state must have {len(MOBILE_STATE_NAMES)} values, got {len(self.state)}"
            )
        if len(self.action) != len(MOBILE_ACTION_NAMES):
            raise ValueError(
                f"mobile action must have {len(MOBILE_ACTION_NAMES)} values, got {len(self.action)}"
            )
        if len(self.privileged_state) != len(MOBILE_PRIVILEGED_STATE_NAMES):
            raise ValueError(
                "mobile privileged state must have "
                f"{len(MOBILE_PRIVILEGED_STATE_NAMES)} values, got {len(self.privileged_state)}"
            )


class MobileBimanualLeRobotWriter:
    """Write the 43-D state and 19-D action contract without privileged leakage."""

    def __init__(
        self,
        root: str | Path,
        *,
        fps: int = 30,
        image_size: tuple[int, int] = (224, 224),
        include_depth: bool = True,
        repo_id: str = "local/mobile-bimanual-parcel-expert",
    ) -> None:
        try:
            from lerobot.datasets.lerobot_dataset import LeRobotDataset
        except ImportError as exc:
            raise RuntimeError("LeRobot is required to record the mobile dataset") from exc

        width, height = image_size
        features: dict[str, dict[str, Any]] = {
            "observation.state": {
                "dtype": "float32",
                "shape": (len(MOBILE_STATE_NAMES),),
                "names": list(MOBILE_STATE_NAMES),
            },
            "action": {
                "dtype": "float32",
                "shape": (len(MOBILE_ACTION_NAMES),),
                "names": list(MOBILE_ACTION_NAMES),
            },
            "observation.privileged_state": {
                "dtype": "float32",
                "shape": (len(MOBILE_PRIVILEGED_STATE_NAMES),),
                "names": list(MOBILE_PRIVILEGED_STATE_NAMES),
            },
            "observation.stage_id": {
                "dtype": "int64",
                "shape": (1,),
                "names": ["stage_id"],
                "info": {"stages": list(MOBILE_STAGE_NAMES), "policy_input": False},
            },
            MOBILE_RGB_KEY: {
                "dtype": "image",
                "shape": (height, width, 3),
                "names": ["height", "width", "channels"],
            },
        }
        if include_depth:
            features[MOBILE_DEPTH_KEY] = {
                "dtype": "image",
                "shape": (height, width, 1),
                "names": ["height", "width", "channels"],
                "info": {"is_depth_map": True, "depth_unit": "m"},
            }
            features[MOBILE_DEPTH_RGB_KEY] = {
                "dtype": "image",
                "shape": (height, width, 3),
                "names": ["height", "width", "channels"],
                "info": {"derived_from": "observation.images.overhead_depth"},
            }
        self._include_depth = include_depth
        self._dataset = LeRobotDataset.create(
            repo_id=repo_id,
            root=Path(root),
            fps=fps,
            features=features,
            robot_type="mobile_bi_franka_sim",
            use_videos=False,
            image_writer_threads=4,
        )

    def add_frame(self, frame: MobileBimanualFrame) -> None:
        import numpy as np

        if frame.rgb is None:
            raise ValueError("mobile dataset recording requires an RGB image")
        payload: dict[str, Any] = {
            "observation.state": np.asarray(frame.state, dtype=np.float32),
            "action": np.asarray(frame.action, dtype=np.float32),
            "observation.privileged_state": np.asarray(
                frame.privileged_state, dtype=np.float32
            ),
            "observation.stage_id": np.asarray(
                [MOBILE_STAGE_NAMES.index(frame.stage)], dtype=np.int64
            ),
            MOBILE_RGB_KEY: np.asarray(frame.rgb, dtype=np.uint8)[..., :3],
            "task": frame.task,
        }
        if self._include_depth:
            if frame.depth is None:
                raise ValueError("mobile RGB-D recording requires a depth image")
            depth = np.asarray(frame.depth, dtype=np.float32)
            payload[MOBILE_DEPTH_KEY] = (
                depth[..., None] if depth.ndim == 2 else depth
            )
            payload[MOBILE_DEPTH_RGB_KEY] = metric_depth_to_visual_rgb(depth, np)
        self._dataset.add_frame(payload)

    def save_episode(self) -> None:
        self._dataset.save_episode()

    def clear_episode(self) -> None:
        self._dataset.clear_episode_buffer()

    def finalize(self) -> None:
        self._dataset.finalize()
