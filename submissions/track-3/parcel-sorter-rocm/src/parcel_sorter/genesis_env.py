from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from pathlib import Path
import time
from typing import Any

from .config import ExperimentConfig
from .contracts import CartesianAction, Observation, RobotState
from .capabilities import require_supported_handling
from .expert import ScriptedPickPlaceExpert
from .randomization import ParcelSample


_INITIALIZED_BACKEND: str | None = None


def aabb_gap_m(first_aabb: Any, second_aabb: Any) -> float:
    """Return Euclidean separation between two world-space AABBs in metres."""
    first = first_aabb
    second = second_aabb
    if len(first) != 2 or len(second) != 2:
        raise ValueError("AABBs must contain min and max corners")
    if any(len(corner) != 3 for corner in (*first, *second)):
        raise ValueError("AABB corners must contain three coordinates")
    gap = []
    for axis in range(3):
        gap.append(
            max(
                0.0,
                float(first[0][axis]) - float(second[1][axis]),
                float(second[0][axis]) - float(first[1][axis]),
            )
        )
    return math.sqrt(sum(value * value for value in gap))


def scaled_robot_gains(
    arm_kp: tuple[float, ...],
    arm_kv: tuple[float, ...],
    finger_kp: float,
    finger_kv: float,
    stiffness_scale: float,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Scale arm stiffness while preserving its nominal damping relationship."""
    velocity_scale = math.sqrt(stiffness_scale)
    return (
        (*tuple(value * stiffness_scale for value in arm_kp), finger_kp, finger_kp),
        (*tuple(value * velocity_scale for value in arm_kv), finger_kv, finger_kv),
    )


def _limit_vector(values: tuple[float, ...], maximum_norm: float) -> tuple[float, ...]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm <= maximum_norm or norm == 0.0:
        return values
    scale = maximum_norm / norm
    return tuple(value * scale for value in values)


def cartesian_velocity_twist(
    current_position: tuple[float, float, float],
    current_quaternion: tuple[float, float, float, float],
    target_position: tuple[float, float, float],
    target_quaternion: tuple[float, float, float, float],
    *,
    position_gain_s: float,
    orientation_gain_s: float,
    max_linear_m_s: float,
    max_angular_rad_s: float,
) -> tuple[float, float, float, float, float, float]:
    """Build a bounded world-frame twist from a Cartesian pose error.

    Genesis quaternions are ordered wxyz. The shortest quaternion arc avoids a
    discontinuity when equivalent quaternions have opposite signs.
    """
    linear = _limit_vector(
        tuple(
            (target - current) * position_gain_s
            for current, target in zip(current_position, target_position, strict=True)
        ),
        max_linear_m_s,
    )
    current_norm = math.sqrt(sum(value * value for value in current_quaternion))
    target_norm = math.sqrt(sum(value * value for value in target_quaternion))
    if current_norm == 0.0 or target_norm == 0.0:
        raise ValueError("Cartesian velocity control requires non-zero quaternions")
    cw, cx, cy, cz = (value / current_norm for value in current_quaternion)
    tw, tx, ty, tz = (value / target_norm for value in target_quaternion)
    # target * conjugate(current)
    error = (
        tw * cw + tx * cx + ty * cy + tz * cz,
        -tw * cx + tx * cw - ty * cz + tz * cy,
        -tw * cy + tx * cz + ty * cw - tz * cx,
        -tw * cz - tx * cy + ty * cx + tz * cw,
    )
    if error[0] < 0.0:
        error = tuple(-value for value in error)
    vector_norm = math.sqrt(sum(value * value for value in error[1:]))
    if vector_norm < 1e-12:
        angular = (0.0, 0.0, 0.0)
    else:
        angle = 2.0 * math.atan2(vector_norm, max(0.0, min(1.0, error[0])))
        angular = _limit_vector(
            tuple(value / vector_norm * angle * orientation_gain_s for value in error[1:]),
            max_angular_rad_s,
        )
    return (*linear, *angular)


def damped_least_squares_velocity(
    jacobian: Any,
    twist: Any,
    *,
    damping: float,
    max_joint_velocity: float,
    array_module: Any,
) -> Any:
    """Map a Cartesian twist to bounded joint velocity for NumPy or Torch arrays."""
    if tuple(jacobian.shape)[0] != 6 or tuple(twist.shape) != (6,):
        raise ValueError("expected a 6xN Jacobian and a six-element twist")
    if hasattr(jacobian, "new_zeros"):
        identity = jacobian.new_zeros((6, 6))
        identity.diagonal().fill_(1.0)
    else:
        identity = array_module.eye(6, dtype=jacobian.dtype)
    joint_velocity = jacobian.transpose(-2, -1) @ array_module.linalg.solve(
        jacobian @ jacobian.transpose(-2, -1) + identity * damping * damping,
        twist,
    )
    if hasattr(joint_velocity, "abs"):
        peak = joint_velocity.abs().max()
        scale = (joint_velocity.new_tensor(max_joint_velocity) / (peak + 1e-12)).clamp(max=1.0)
        return joint_velocity * scale
    peak = float(array_module.max(array_module.abs(joint_velocity)))
    if peak > max_joint_velocity:
        joint_velocity = joint_velocity * (max_joint_velocity / peak)
    return joint_velocity


@dataclass(frozen=True)
class ParcelSpawnSpec:
    shape: str
    dimensions_m: tuple[float, float, float]
    initial_z_m: float
    euler_degrees: tuple[float, float, float]
    cylinder_height_m: float | None = None
    cylinder_radius_m: float | None = None


def parcel_spawn_spec(config: ExperimentConfig, sample: ParcelSample) -> ParcelSpawnSpec:
    dimensions = sample.dimensions_m or tuple(
        base * scale
        for base, scale in zip(
            config.task.parcel_base_size_m,
            sample.size_scale_xyz,
            strict=True,
        )
    )
    yaw_degrees = math.degrees(sample.yaw_rad)
    if sample.shape == "box":
        return ParcelSpawnSpec(
            shape="box",
            dimensions_m=dimensions,
            initial_z_m=dimensions[2] / 2,
            euler_degrees=(0.0, 0.0, yaw_degrees),
        )
    if sample.shape != "cylinder":
        raise ValueError(f"unsupported parcel shape: {sample.shape}")
    if sample.orientation_mode == "upright":
        height, radius = dimensions[2], dimensions[0] / 2
        euler = (0.0, 0.0, yaw_degrees)
        initial_z = height / 2
    elif sample.orientation_mode == "horizontal":
        height, radius = dimensions[0], dimensions[1] / 2
        euler = (0.0, 90.0, yaw_degrees)
        initial_z = radius
    else:
        raise ValueError(f"unsupported cylinder orientation: {sample.orientation_mode}")
    return ParcelSpawnSpec(
        shape="cylinder",
        dimensions_m=dimensions,
        initial_z_m=initial_z,
        euler_degrees=euler,
        cylinder_height_m=height,
        cylinder_radius_m=radius,
    )


def genesis_depth_to_meters(depth: Any, np: Any) -> Any:
    """Return Genesis rasterizer depth as float32 metres.

    Genesis camera near/far planes and reconstructed point clouds use metres,
    so applying an additional millimetre conversion corrupts the sensor scale.
    """
    return np.asarray(depth, dtype=np.float32)


def needs_rolling_friction(sample: ParcelSample) -> bool:
    """Enable the more expensive solver path only for rolling-prone parcels."""
    return (
        sample.shape == "cylinder"
        and sample.orientation_mode == "horizontal"
        and sample.rolling_friction > 0
    )


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
        # Check the end-effector contract before importing/building Genesis.
        # Evaluation-only catalog entries must not be mistaken for support.
        require_supported_handling(sample.handling_class)
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
        self._aabb_guard_filter_count = 0
        self._aabb_guard_active_steps = 0
        self._aabb_guard_max_active_steps = 0
        self._aabb_guard_samples = 0
        self._aabb_guard_compute_ms_total = 0.0
        self._aabb_guard_last_gap_m: float | None = None
        self._aabb_guard_last_compute_ms = 0.0
        self._aabb_guard_last_triggered = False
        self._aabb_guard_last_reason: str | None = None
        self._aabb_guard_last_nominal_target_m: tuple[float, float, float] | None = None
        self._aabb_guard_last_filtered_target_m: tuple[float, float, float] | None = None
        self._approach_velocity_samples = 0
        self._approach_velocity_compute_ms_total = 0.0
        self._approach_velocity_max_joint_rad_s = 0.0
        self._approach_velocity_max_pose_error_m = 0.0
        self._approach_velocity_last_twist: tuple[float, ...] | None = None
        self._approach_velocity_last_joint_command: tuple[float, ...] | None = None
        self._approach_velocity_last_predicted_twist: tuple[float, ...] | None = None
        self._approach_velocity_last_actual_joint_velocity: tuple[float, ...] | None = None

        physics_dt = 1.0 / config.simulation.physics_hz
        rolling_friction = needs_rolling_friction(sample)
        self.scene = self.gs.Scene(
            sim_options=self.gs.options.SimOptions(dt=physics_dt),
            rigid_options=self.gs.options.RigidOptions(
                box_box_detection=True,
                enable_collision=True,
                enable_joint_limit=True,
                enable_torsional_friction=rolling_friction,
                enable_rolling_friction=rolling_friction,
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

        spawn = parcel_spawn_spec(config, sample)
        self._initial_parcel_z = spawn.initial_z_m
        color = (0.10, 0.55, 0.92) if sample.destination == "left" else (0.96, 0.55, 0.12)
        if spawn.shape == "box":
            parcel_morph = self.gs.morphs.Box(
                size=spawn.dimensions_m,
                pos=(sample.position_xy[0], sample.position_xy[1], spawn.initial_z_m),
                euler=spawn.euler_degrees,
            )
        else:
            parcel_morph = self.gs.morphs.Cylinder(
                height=spawn.cylinder_height_m,
                radius=spawn.cylinder_radius_m,
                pos=(sample.position_xy[0], sample.position_xy[1], spawn.initial_z_m),
                euler=spawn.euler_degrees,
            )
        self.parcel = self.scene.add_entity(
            parcel_morph,
            material=self.gs.materials.Rigid(
                friction=sample.friction,
                friction_rolling=sample.rolling_friction,
            ),
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
        if sample.finger_friction is not None:
            self.left_finger.set_friction(sample.finger_friction)
            self.right_finger.set_friction(sample.finger_friction)
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
        gains_kp, gains_kv = scaled_robot_gains(
            control.arm_kp,
            control.arm_kv,
            control.finger_kp,
            control.finger_kv,
            1.0,
        )
        gains_kp = self.np.asarray(gains_kp)
        gains_kv = self.np.asarray(gains_kv)
        self.robot.set_dofs_kp(gains_kp)
        self.robot.set_dofs_kv(gains_kv)
        self._active_arm_stiffness_scale = 1.0
        self.robot.set_dofs_force_range(
            self.np.asarray((-87, -87, -87, -87, -12, -12, -12, -100, -100)),
            self.np.asarray((87, 87, 87, 87, 12, 12, 12, 100, 100)),
        )
        self.robot.set_qpos(
            self.np.asarray(control.reset_qpos)
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
            ) <= self.expert.pregrasp_tolerance_m(),
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

    def safety_snapshot(self) -> dict[str, Any]:
        """Return the last action-filter event without changing the policy action schema."""
        return {
            "precontact_aabb_guard_enabled": (
                self.config.control.precontact_aabb_guard_distance_m is not None
            ),
            "precontact_aabb_gap_m": self._aabb_guard_last_gap_m,
            "precontact_aabb_guard_triggered": self._aabb_guard_last_triggered,
            "precontact_aabb_guard_reason": self._aabb_guard_last_reason,
            "precontact_aabb_nominal_target_m": self._aabb_guard_last_nominal_target_m,
            "precontact_aabb_filtered_target_m": self._aabb_guard_last_filtered_target_m,
            "precontact_aabb_guard_compute_ms": self._aabb_guard_last_compute_ms,
            "precontact_aabb_guard_filter_count": self._aabb_guard_filter_count,
            "precontact_aabb_guard_active_steps": self._aabb_guard_active_steps,
        }

    def safety_summary(self) -> dict[str, Any]:
        mean_compute_ms = (
            self._aabb_guard_compute_ms_total / self._aabb_guard_samples
            if self._aabb_guard_samples
            else 0.0
        )
        return {
            "precontact_aabb_guard_enabled": (
                self.config.control.precontact_aabb_guard_distance_m is not None
            ),
            "precontact_aabb_guard_distance_m": (
                self.config.control.precontact_aabb_guard_distance_m
            ),
            "precontact_aabb_guard_filter_count": self._aabb_guard_filter_count,
            "precontact_aabb_guard_max_active_steps": self._aabb_guard_max_active_steps,
            "precontact_aabb_guard_samples": self._aabb_guard_samples,
            "precontact_aabb_guard_compute_ms_total": self._aabb_guard_compute_ms_total,
            "precontact_aabb_guard_compute_ms_mean": mean_compute_ms,
            "approach_velocity_control_enabled": (
                self.config.control.approach_velocity_control_enabled
            ),
            "approach_velocity_control_samples": self._approach_velocity_samples,
            "approach_velocity_control_compute_ms_total": (
                self._approach_velocity_compute_ms_total
            ),
            "approach_velocity_control_compute_ms_mean": (
                self._approach_velocity_compute_ms_total / self._approach_velocity_samples
                if self._approach_velocity_samples
                else 0.0
            ),
            "approach_velocity_control_max_joint_rad_s": (
                self._approach_velocity_max_joint_rad_s
            ),
            "approach_velocity_control_max_pose_error_m": (
                self._approach_velocity_max_pose_error_m
            ),
            "approach_velocity_control_last_twist": self._approach_velocity_last_twist,
            "approach_velocity_control_last_joint_command": (
                self._approach_velocity_last_joint_command
            ),
            "approach_velocity_control_last_predicted_twist": (
                self._approach_velocity_last_predicted_twist
            ),
            "approach_velocity_control_last_actual_joint_velocity": (
                self._approach_velocity_last_actual_joint_velocity
            ),
        }

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
        action = self._filter_precontact_action(action)
        self._set_arm_stiffness_for_command(action.command)
        if (
            self.config.control.approach_velocity_control_enabled
            and action.command == "move_pregrasp"
        ):
            self._apply_approach_velocity(action)
        else:
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

    def _apply_approach_velocity(self, action: CartesianAction) -> None:
        """Execute one bounded operational-space velocity command on the Radeon."""
        started = time.perf_counter_ns()
        actual_joint_velocity = self.robot.get_dofs_velocity(self.arm_dofs)
        current_position = self._flat_tuple(self.end_effector.get_pos())
        current_quaternion = self._flat_tuple(self.end_effector.get_quat())
        control = self.config.control
        twist_values = cartesian_velocity_twist(
            current_position,
            current_quaternion,
            action.target_position,
            action.target_quaternion,
            position_gain_s=control.approach_velocity_position_gain_s,
            orientation_gain_s=control.approach_velocity_orientation_gain_s,
            max_linear_m_s=control.approach_velocity_max_linear_m_s,
            max_angular_rad_s=control.approach_velocity_max_angular_rad_s,
        )
        jacobian = self.robot.get_jacobian(self.end_effector)[..., :7]
        twist = jacobian.new_tensor(twist_values)
        task_weights = jacobian.new_tensor(
            (1.0, 1.0, 1.0) + (control.approach_velocity_orientation_weight,) * 3
        )
        weighted_jacobian = jacobian * task_weights[:, None]
        weighted_twist = twist * task_weights
        joint_velocity = damped_least_squares_velocity(
            weighted_jacobian,
            weighted_twist,
            damping=control.approach_velocity_damping,
            max_joint_velocity=control.approach_velocity_max_joint_rad_s,
            array_module=self.torch,
        )
        if not bool(self.torch.isfinite(joint_velocity).all().item()):
            raise RuntimeError("approach velocity control produced a non-finite command")
        self.robot.control_dofs_velocity(joint_velocity, self.arm_dofs)
        predicted_twist = jacobian @ joint_velocity
        compute_ms = (time.perf_counter_ns() - started) / 1_000_000
        self._approach_velocity_samples += 1
        self._approach_velocity_compute_ms_total += compute_ms
        self._approach_velocity_max_joint_rad_s = max(
            self._approach_velocity_max_joint_rad_s,
            float(joint_velocity.abs().max().item()),
        )
        self._approach_velocity_max_pose_error_m = max(
            self._approach_velocity_max_pose_error_m,
            self._distance(current_position, action.target_position),
        )
        self._approach_velocity_last_twist = tuple(float(value) for value in twist_values)
        self._approach_velocity_last_joint_command = self._flat_tuple(joint_velocity)
        self._approach_velocity_last_predicted_twist = self._flat_tuple(predicted_twist)
        self._approach_velocity_last_actual_joint_velocity = self._flat_tuple(
            actual_joint_velocity
        )

    def _set_arm_stiffness_for_command(self, command: str) -> None:
        scale = (
            self.config.control.approach_stiffness_scale
            if command == "move_pregrasp"
            else 1.0
        )
        if math.isclose(scale, self._active_arm_stiffness_scale, rel_tol=0.0, abs_tol=1e-12):
            return
        control = self.config.control
        gains_kp, gains_kv = scaled_robot_gains(
            control.arm_kp,
            control.arm_kv,
            control.finger_kp,
            control.finger_kv,
            scale,
        )
        self.robot.set_dofs_kp(self.np.asarray(gains_kp))
        self.robot.set_dofs_kv(self.np.asarray(gains_kv))
        self._active_arm_stiffness_scale = scale

    def _filter_precontact_action(self, action: CartesianAction) -> CartesianAction:
        """Apply a geometry guard before IK while preserving the 8-D action contract."""
        self._aabb_guard_last_gap_m = None
        self._aabb_guard_last_compute_ms = 0.0
        self._aabb_guard_last_triggered = False
        self._aabb_guard_last_reason = None
        self._aabb_guard_last_nominal_target_m = None
        self._aabb_guard_last_filtered_target_m = None
        threshold = self.config.control.precontact_aabb_guard_distance_m
        if threshold is None or action.command != "move_pregrasp":
            self._aabb_guard_active_steps = 0
            return action

        started = time.perf_counter_ns()
        gap_m = self._finger_parcel_aabb_gap_m()
        compute_ms = (time.perf_counter_ns() - started) / 1_000_000
        self._aabb_guard_last_gap_m = gap_m
        self._aabb_guard_last_compute_ms = compute_ms
        self._aabb_guard_compute_ms_total += compute_ms
        self._aabb_guard_samples += 1

        current = self._flat_tuple(self.end_effector.get_pos())
        parcel = self._flat_tuple(self.parcel.get_pos())
        horizontal_distance = math.hypot(current[0] - parcel[0], current[1] - parcel[1])
        target_horizontal_distance = math.hypot(
            action.target_position[0] - parcel[0],
            action.target_position[1] - parcel[1],
        )
        nominal_step_m = self._distance(current, action.target_position)
        outside_descent_window = horizontal_distance > self.config.task.position_tolerance_m
        moving_toward_parcel = target_horizontal_distance < horizontal_distance - 1e-9
        if not (
            gap_m <= threshold
            and outside_descent_window
            and moving_toward_parcel
            and nominal_step_m > 1e-9
        ):
            self._aabb_guard_active_steps = 0
            return action

        transit_z = parcel[2] + self.expert.approach_clearance_m()
        if current[2] < transit_z - self.config.task.position_tolerance_m:
            guard_target = (
                current[0],
                current[1],
                min(transit_z, current[2] + nominal_step_m),
            )
            reason = "raise_to_transit"
        else:
            dx = current[0] - parcel[0]
            dy = current[1] - parcel[1]
            if horizontal_distance <= 1e-9:
                guard_target = (current[0], current[1], current[2] + nominal_step_m)
                reason = "raise_from_centerline"
            else:
                guard_target = (
                    current[0] + nominal_step_m * dx / horizontal_distance,
                    current[1] + nominal_step_m * dy / horizontal_distance,
                    current[2],
                )
                reason = "retreat_from_parcel"

        self._aabb_guard_filter_count += 1
        self._aabb_guard_active_steps += 1
        self._aabb_guard_max_active_steps = max(
            self._aabb_guard_max_active_steps,
            self._aabb_guard_active_steps,
        )
        self._aabb_guard_last_triggered = True
        self._aabb_guard_last_reason = reason
        self._aabb_guard_last_nominal_target_m = action.target_position
        self._aabb_guard_last_filtered_target_m = guard_target
        return CartesianAction(
            target_position=guard_target,
            target_quaternion=action.target_quaternion,
            gripper=action.gripper,
            command=action.command,
        )

    def _finger_parcel_aabb_gap_m(self) -> float:
        """Compute the closest finger-to-parcel AABB gap on the ROCm device."""
        parcel_aabb = self.parcel.get_AABB()
        finger_gaps = []
        for finger in (self.left_finger, self.right_finger):
            finger_aabb = finger.get_AABB()
            axis_gap = self.torch.clamp(
                self.torch.maximum(
                    finger_aabb[0] - parcel_aabb[1],
                    parcel_aabb[0] - finger_aabb[1],
                ),
                min=0.0,
            )
            finger_gaps.append(self.torch.linalg.vector_norm(axis_gap))
        return float(self.torch.stack(finger_gaps).min().item())

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
