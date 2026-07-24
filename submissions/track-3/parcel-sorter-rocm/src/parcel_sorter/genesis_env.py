from __future__ import annotations

from collections import deque
import math
from pathlib import Path
from typing import Any

from .config import ExperimentConfig
from .contracts import CartesianAction, Observation, RobotState
from .expert import ScriptedPickPlaceExpert
from .randomization import ParcelSample


_INITIALIZED_BACKEND: str | None = None


def genesis_depth_to_meters(depth: Any, np: Any) -> Any:
    """Convert Genesis camera depth from millimeters to float32 meters."""
    return np.asarray(depth, dtype=np.float32) * np.float32(0.001)


def initialize_genesis(backend: str) -> tuple[Any, Any, Any]:
    """Initialize the pinned Genesis runtime and validate the selected GPU stack."""
    global _INITIALIZED_BACKEND

    if backend not in {"rocm", "cuda", "cpu"}:
        raise ValueError("backend must be one of: rocm, cuda, cpu")
    if _INITIALIZED_BACKEND is not None and _INITIALIZED_BACKEND != backend:
        raise RuntimeError(
            f"Genesis is already initialized for {_INITIALIZED_BACKEND}; use a new process for {backend}"
        )

    import numpy as np
    import torch
    import genesis as gs

    if _INITIALIZED_BACKEND is None:
        if backend == "rocm":
            if getattr(torch.version, "hip", None) is None:
                raise RuntimeError("ROCm backend requires a PyTorch HIP build")
            if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
                raise RuntimeError("ROCm execution requires exactly one visible Radeon GPU")
            gs.init(backend=gs.gpu, precision="32", seed=0)
        elif backend == "cuda":
            if getattr(torch.version, "cuda", None) is None or getattr(torch.version, "hip", None) is not None:
                raise RuntimeError("CUDA backend requires an NVIDIA PyTorch CUDA build")
            if not torch.cuda.is_available():
                raise RuntimeError("PyTorch cannot access the NVIDIA GPU")
            gs.init(backend=gs.gpu, precision="32", seed=0)
        else:
            gs.init(backend=gs.cpu, precision="32", seed=0)
        _INITIALIZED_BACKEND = backend
    return gs, torch, np


class GenesisParcelEnv:
    """Single-environment Franka parcel sorting task with aligned RGB-D output."""

    def __init__(
        self,
        config: ExperimentConfig,
        sample: ParcelSample,
        *,
        backend: str = "rocm",
        show_viewer: bool = False,
        video_path: str | Path | None = None,
        capture_sensors: bool = False,
    ) -> None:
        self.config = config
        self.sample = sample
        self.backend = backend
        self.gs, self.torch, self.np = initialize_genesis(backend)
        self.gs.set_random_seed(config.seed + sample.episode_index)
        self.expert = ScriptedPickPlaceExpert(config, sample)
        self.control_step = 0
        self._release_steps = 0
        self._gripper_force_n = 0.0
        self._closed = False
        self._capture_sensors = capture_sensors
        self._latest_rgb: Any | None = None
        self._latest_depth: Any | None = None
        self._video_path = Path(video_path) if video_path else None
        self._action_queue: deque[CartesianAction | None] = deque(
            [None] * sample.action_delay_steps
        )

        physics_dt = 1.0 / config.simulation.physics_hz
        self.scene = self.gs.Scene(
            sim_options=self.gs.options.SimOptions(dt=physics_dt),
            rigid_options=self.gs.options.RigidOptions(
                box_box_detection=True,
                enable_collision=True,
                enable_joint_limit=True,
            ),
            viewer_options=self.gs.options.ViewerOptions(
                camera_pos=(1.35, -1.15, 0.95),
                camera_lookat=(0.48, 0.0, 0.08),
                camera_fov=48,
                res=(960, 640),
            ),
            profiling_options=self.gs.options.ProfilingOptions(show_FPS=False),
            show_viewer=show_viewer,
        )
        self.scene.add_entity(self.gs.morphs.Plane())
        self._add_sorting_targets()
        self.robot = self.scene.add_entity(
            self.gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
            visualize_contact=show_viewer,
        )

        parcel_size = tuple(
            base * scale
            for base, scale in zip(
                config.task.parcel_base_size_m,
                sample.size_scale_xyz,
                strict=True,
            )
        )
        self._initial_parcel_z = parcel_size[2] / 2
        color = (0.10, 0.55, 0.92) if sample.destination == "left" else (0.96, 0.55, 0.12)
        self.parcel = self.scene.add_entity(
            self.gs.morphs.Box(
                size=parcel_size,
                pos=(sample.position_xy[0], sample.position_xy[1], self._initial_parcel_z),
                euler=(0.0, 0.0, math.degrees(sample.yaw_rad)),
            ),
            material=self.gs.materials.Rigid(friction=sample.friction),
            surface=self.gs.surfaces.Rough(
                diffuse_texture=self.gs.textures.ColorTexture(color=color)
            ),
        )

        self.camera = None
        if config.sensors.rgb or config.sensors.depth or self._video_path:
            camera_base = (1.10, -0.78, 0.78)
            camera_position = tuple(
                base + noise
                for base, noise in zip(camera_base, sample.camera_noise_xyz_m, strict=True)
            )
            self.camera = self.scene.add_camera(
                res=(config.sensors.image_width, config.sensors.image_height),
                pos=camera_position,
                lookat=(0.50, 0.0, 0.04),
                fov=52,
                GUI=show_viewer,
            )

        self.scene.build()
        self._configure_robot()
        self.parcel.set_mass(sample.mass_kg)
        self.end_effector = self.robot.get_link("hand")
        self.left_finger = self.robot.get_link("left_finger")
        self.right_finger = self.robot.get_link("right_finger")
        self.arm_dofs = self.np.arange(7)
        self.finger_dofs = self.np.arange(7, 9)

        if self.camera is not None and self._video_path is not None:
            self._video_path.parent.mkdir(parents=True, exist_ok=True)
            self.camera.start_recording()

        for _ in range(max(2, config.simulation.physics_hz // 30)):
            self.scene.step()
        if self.camera is not None and (self._capture_sensors or self._video_path):
            self._render_camera()

    def _add_sorting_targets(self) -> None:
        for center, color in (
            (self.config.task.left_bin_center_m, (0.08, 0.55, 0.92)),
            (self.config.task.right_bin_center_m, (0.96, 0.50, 0.08)),
        ):
            self.scene.add_entity(
                self.gs.morphs.Box(
                    size=(
                        self.config.task.bin_half_extent_m[0] * 2,
                        self.config.task.bin_half_extent_m[1] * 2,
                        0.01,
                    ),
                    pos=(center[0], center[1], 0.005),
                    fixed=True,
                ),
                surface=self.gs.surfaces.Rough(
                    diffuse_texture=self.gs.textures.ColorTexture(color=color)
                ),
            )

    def _configure_robot(self) -> None:
        control = self.config.control
        gains_kp = self.np.asarray((*control.arm_kp, control.finger_kp, control.finger_kp))
        gains_kv = self.np.asarray((*control.arm_kv, control.finger_kv, control.finger_kv))
        self.robot.set_dofs_kp(gains_kp)
        self.robot.set_dofs_kv(gains_kv)
        self.robot.set_dofs_force_range(
            self.np.asarray((-87, -87, -87, -87, -12, -12, -12, -100, -100)),
            self.np.asarray((87, 87, 87, 87, 12, 12, 12, 100, 100)),
        )
        self.robot.set_qpos(
            self.np.asarray(
                (-1.0124, 1.5559, 1.3662, -1.6878, -1.5799, 1.7757, 1.4602, 0.04, 0.04)
            )
        )

    def state(self) -> RobotState:
        joint_positions = self._flat_tuple(self.robot.get_qpos())
        ee_pose = (
            *self._flat_tuple(self.end_effector.get_pos()),
            *self._flat_tuple(self.end_effector.get_quat()),
        )
        parcel_pose = (
            *self._flat_tuple(self.parcel.get_pos()),
            *self._flat_tuple(self.parcel.get_quat()),
        )
        _, max_force = self._finger_contact()
        return RobotState(
            joint_positions=joint_positions,
            end_effector_pose=ee_pose,
            parcel_pose=parcel_pose,
            target_position=self.expert.destination_position,
            gripper_contact_force_n=max_force,
        )

    def observation(self, state: RobotState | None = None) -> Observation:
        state = state or self.state()
        parcel_position = state.parcel_pose[:3]
        ee_position = state.end_effector_pose[:3]
        has_contact, max_force = self._finger_contact()
        destination = self.expert.destination_position
        in_bin = (
            abs(parcel_position[0] - destination[0]) <= self.config.task.bin_half_extent_m[0]
            and abs(parcel_position[1] - destination[1]) <= self.config.task.bin_half_extent_m[1]
        )
        at_drop = self._distance(ee_position, self.expert.drop_position()) <= self.config.task.position_tolerance_m
        if in_bin and not has_contact:
            self._release_steps += 1
        else:
            self._release_steps = 0

        values = (*state.joint_positions, *state.end_effector_pose, *state.parcel_pose)
        finite = all(math.isfinite(value) for value in values)
        return Observation(
            parcel_visible=finite and parcel_position[2] > -0.02,
            at_pregrasp=self._distance(
                ee_position, self.expert.pregrasp_position(state.parcel_pose)
            ) <= self.config.task.position_tolerance_m,
            grasp_contact=has_contact,
            parcel_lifted=parcel_position[2]
            >= self._initial_parcel_z + self.config.task.lift_height_m * 0.65,
            at_drop_pose=at_drop,
            parcel_in_bin=in_bin,
            parcel_released=self._release_steps >= self.config.task.release_settle_steps,
            excessive_contact_force=max_force > self.config.task.max_contact_force_n,
            fault=not finite,
        )

    def step(self, action: CartesianAction) -> None:
        self._action_queue.append(action)
        delayed_action = self._action_queue.popleft()
        if delayed_action is not None:
            self._apply_action(delayed_action)

        physics_steps = self.config.simulation.physics_hz // self.config.simulation.control_hz
        for _ in range(physics_steps):
            self.scene.step()
        self.control_step += 1

        camera_stride = self.config.simulation.control_hz // self.config.simulation.camera_hz
        if self.camera is not None and self.control_step % camera_stride == 0:
            if self._capture_sensors or self._video_path:
                self._render_camera()

    def sensor_frame(self) -> tuple[Any | None, Any | None]:
        if not self._capture_sensors:
            return None, None
        if self._latest_rgb is None and self.camera is not None:
            self._render_camera()
        return self._latest_rgb, self._latest_depth

    def parcel_dropped(self) -> bool:
        position = self._flat_tuple(self.parcel.get_pos())
        return position[2] < -0.02 or abs(position[0]) > 1.2 or abs(position[1]) > 1.2

    def close(self) -> None:
        if self._closed:
            return
        try:
            if self.camera is not None and self._video_path is not None:
                self.camera.stop_recording(
                    save_to_filename=str(self._video_path),
                    fps=self.config.simulation.camera_hz,
                )
        finally:
            self.scene.destroy()
            self._closed = True

    def _apply_action(self, action: CartesianAction) -> None:
        qpos = self.robot.inverse_kinematics(
            link=self.end_effector,
            pos=self.np.asarray(action.target_position),
            quat=self.np.asarray(action.target_quaternion),
        )
        qpos_array = self.np.asarray(qpos.detach().cpu() if hasattr(qpos, "detach") else qpos)
        if not self.np.isfinite(qpos_array).all():
            raise RuntimeError(f"IK returned a non-finite solution for {action.command}")
        self.robot.control_dofs_position(qpos_array[:7], self.arm_dofs)
        if action.gripper > 0:
            self._gripper_force_n = 0.0
            width = self.config.control.open_width_m
            self.robot.control_dofs_position(self.np.asarray((width, width)), self.finger_dofs)
        else:
            self._gripper_force_n = min(
                self.config.control.close_force_n,
                self._gripper_force_n + self.config.control.close_force_ramp_n_per_step,
            )
            force = self._gripper_force_n
            self.robot.control_dofs_force(self.np.asarray((-force, -force)), self.finger_dofs)

    def _finger_contact(self) -> tuple[bool, float]:
        contacts = self.robot.get_contacts(with_entity=self.parcel)
        forces = contacts["force_a"]
        if forces.numel() == 0:
            return False, 0.0

        link_a = contacts["link_a"]
        link_b = contacts["link_b"]
        finger_ids = (self.left_finger.idx, self.right_finger.idx)
        mask = self.torch.zeros_like(link_a, dtype=self.torch.bool)
        finger_contacts = []
        for finger_id in finger_ids:
            finger_mask = (link_a == finger_id) | (link_b == finger_id)
            if "valid_mask" in contacts:
                finger_mask &= contacts["valid_mask"]
            finger_contacts.append(bool(finger_mask.any().item()))
            mask |= finger_mask
        if not bool(mask.any().item()):
            return False, 0.0
        magnitudes = self.torch.linalg.vector_norm(forces[mask], dim=-1)
        return all(finger_contacts), float(magnitudes.max().item())

    def _render_camera(self) -> None:
        if self.camera is None:
            return
        rgb, depth, _, _ = self.camera.render(
            rgb=self.config.sensors.rgb or self._video_path is not None,
            depth=self.config.sensors.depth,
        )
        if rgb is not None:
            self._latest_rgb = self.np.asarray(rgb)[..., :3]
        if depth is not None:
            self._latest_depth = genesis_depth_to_meters(depth, self.np)

    @staticmethod
    def _distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)))

    @staticmethod
    def _flat_tuple(value: Any) -> tuple[float, ...]:
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        return tuple(float(item) for item in value.reshape(-1))

    def __enter__(self) -> "GenesisParcelEnv":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
