from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any


@dataclass(frozen=True)
class SimulationConfig:
    backend: str
    device: str
    num_envs: int
    physics_hz: int
    control_hz: int
    camera_hz: int
    headless: bool

    def validate(self) -> None:
        if self.backend != "rocm":
            raise ValueError("The competition baseline must use the ROCm backend")
        if self.device != "cuda:0":
            raise ValueError("PyTorch exposes ROCm devices through cuda:0")
        if self.num_envs < 1:
            raise ValueError("num_envs must be positive")
        if self.physics_hz % self.control_hz != 0:
            raise ValueError("physics_hz must be divisible by control_hz")
        if self.control_hz % self.camera_hz != 0:
            raise ValueError("control_hz must be divisible by camera_hz")


@dataclass(frozen=True)
class TaskConfig:
    max_grasp_retries: int
    lift_height_m: float
    max_contact_force_n: float
    episode_seconds: float
    parcel_base_size_m: tuple[float, float, float]
    left_bin_center_m: tuple[float, float, float]
    right_bin_center_m: tuple[float, float, float]
    bin_half_extent_m: tuple[float, float]
    approach_clearance_m: float
    grasp_hand_clearance_m: float
    drop_hand_height_m: float
    position_tolerance_m: float
    release_settle_steps: int
    grasp_settle_steps: int

    def validate(self) -> None:
        if self.max_grasp_retries < 0:
            raise ValueError("max_grasp_retries cannot be negative")
        if self.lift_height_m <= 0:
            raise ValueError("lift_height_m must be positive")
        if self.max_contact_force_n <= 0:
            raise ValueError("max_contact_force_n must be positive")
        if self.episode_seconds <= 0:
            raise ValueError("episode_seconds must be positive")
        if len(self.parcel_base_size_m) != 3 or any(value <= 0 for value in self.parcel_base_size_m):
            raise ValueError("parcel_base_size_m must contain three positive values")
        for label, value in (
            ("left_bin_center_m", self.left_bin_center_m),
            ("right_bin_center_m", self.right_bin_center_m),
        ):
            if len(value) != 3:
                raise ValueError(f"{label} must contain three values")
        if len(self.bin_half_extent_m) != 2 or any(value <= 0 for value in self.bin_half_extent_m):
            raise ValueError("bin_half_extent_m must contain two positive values")
        if min(
            self.approach_clearance_m,
            self.grasp_hand_clearance_m,
            self.drop_hand_height_m,
        ) <= 0:
            raise ValueError("approach, grasp, and drop heights must be positive")
        if self.approach_clearance_m <= self.grasp_hand_clearance_m:
            raise ValueError("approach clearance must exceed grasp clearance")
        if self.position_tolerance_m <= 0 or min(self.release_settle_steps, self.grasp_settle_steps) < 0:
            raise ValueError("position tolerance must be positive and settle steps cannot be negative")


@dataclass(frozen=True)
class ControlConfig:
    arm_kp: tuple[float, ...]
    arm_kv: tuple[float, ...]
    finger_kp: float
    finger_kv: float
    open_width_m: float
    close_force_n: float
    close_force_ramp_n_per_step: float
    max_ee_step_m: float
    final_approach_step_m: float

    def validate(self) -> None:
        if len(self.arm_kp) != 7 or len(self.arm_kv) != 7:
            raise ValueError("arm gains must contain seven values")
        if any(value <= 0 for value in (*self.arm_kp, *self.arm_kv)):
            raise ValueError("arm gains must be positive")
        if min(
            self.finger_kp,
            self.finger_kv,
            self.open_width_m,
            self.close_force_n,
            self.close_force_ramp_n_per_step,
        ) <= 0:
            raise ValueError("finger gains, width, force, and force ramp must be positive")
        if self.max_ee_step_m <= 0 or self.final_approach_step_m <= 0:
            raise ValueError("Cartesian step limits must be positive")
        if self.final_approach_step_m > self.max_ee_step_m:
            raise ValueError("final_approach_step_m cannot exceed max_ee_step_m")


@dataclass(frozen=True)
class OutputConfig:
    root_dir: str
    task_instruction: str
    record_first_episode: bool
    save_sensor_frames: bool

    def validate(self) -> None:
        if not self.root_dir.strip():
            raise ValueError("output root_dir is required")
        if not self.task_instruction.strip():
            raise ValueError("task_instruction is required")


@dataclass(frozen=True)
class SensorsConfig:
    rgb: bool
    depth: bool
    proprioception: bool
    contact_force: bool
    image_width: int
    image_height: int

    def validate(self) -> None:
        if not any((self.rgb, self.depth, self.proprioception, self.contact_force)):
            raise ValueError("at least one observation modality must be enabled")
        if self.image_width < 32 or self.image_height < 32:
            raise ValueError("camera resolution must be at least 32x32")


@dataclass(frozen=True)
class RandomizationConfig:
    enabled: bool
    parcel_size_scale_min: float
    parcel_size_scale_max: float
    parcel_mass_kg_min: float
    parcel_mass_kg_max: float
    friction_min: float
    friction_max: float
    camera_position_noise_m: float
    action_delay_steps_max: int
    parcel_position_x_min: float
    parcel_position_x_max: float
    parcel_position_y_min: float
    parcel_position_y_max: float
    parcel_yaw_rad_min: float
    parcel_yaw_rad_max: float

    def validate(self) -> None:
        ranges = (
            ("parcel size", self.parcel_size_scale_min, self.parcel_size_scale_max),
            ("parcel mass", self.parcel_mass_kg_min, self.parcel_mass_kg_max),
            ("friction", self.friction_min, self.friction_max),
            ("parcel x", self.parcel_position_x_min, self.parcel_position_x_max),
            ("parcel y", self.parcel_position_y_min, self.parcel_position_y_max),
            ("parcel yaw", self.parcel_yaw_rad_min, self.parcel_yaw_rad_max),
        )
        for label, lower, upper in ranges:
            if lower > upper:
                raise ValueError(f"{label} minimum cannot exceed maximum")
        if self.parcel_size_scale_min <= 0 or self.parcel_mass_kg_min <= 0:
            raise ValueError("parcel size and mass must remain positive")
        if self.friction_min <= 0:
            raise ValueError("friction must remain positive")
        if self.camera_position_noise_m < 0 or self.action_delay_steps_max < 0:
            raise ValueError("noise and delay cannot be negative")


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    seed: int
    simulation: SimulationConfig
    sensors: SensorsConfig
    task: TaskConfig
    control: ControlConfig
    output: OutputConfig
    randomization: RandomizationConfig

    def validate(self) -> None:
        if not self.name:
            raise ValueError("project name is required")
        self.simulation.validate()
        self.sensors.validate()
        self.task.validate()
        self.control.validate()
        self.output.validate()
        self.randomization.validate()


def _tuple_values(raw: dict[str, Any], *keys: str) -> dict[str, Any]:
    converted = dict(raw)
    for key in keys:
        converted[key] = tuple(float(value) for value in converted[key])
    return converted


def load_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("rb") as handle:
        raw = tomllib.load(handle)

    config = ExperimentConfig(
        name=str(raw["project"]["name"]),
        seed=int(raw["project"]["seed"]),
        simulation=SimulationConfig(**raw["simulation"]),
        sensors=SensorsConfig(**raw["sensors"]),
        task=TaskConfig(
            **_tuple_values(
                raw["task"],
                "parcel_base_size_m",
                "left_bin_center_m",
                "right_bin_center_m",
                "bin_half_extent_m",
            )
        ),
        control=ControlConfig(**_tuple_values(raw["control"], "arm_kp", "arm_kv")),
        output=OutputConfig(**raw["output"]),
        randomization=RandomizationConfig(**raw["randomization"]),
    )
    config.validate()
    return config
