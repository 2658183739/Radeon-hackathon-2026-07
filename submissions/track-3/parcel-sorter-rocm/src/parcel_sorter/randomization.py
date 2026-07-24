from __future__ import annotations

from dataclasses import asdict, dataclass
import random

from .config import RandomizationConfig


@dataclass(frozen=True)
class ParcelSample:
    episode_index: int
    size_scale_xyz: tuple[float, float, float]
    mass_kg: float
    friction: float
    position_xy: tuple[float, float]
    yaw_rad: float
    camera_noise_xyz_m: tuple[float, float, float]
    action_delay_steps: int
    destination: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class DomainRandomizer:
    """Produces reproducible, per-episode parcel and sensor parameters."""

    def __init__(self, config: RandomizationConfig, seed: int) -> None:
        self.config = config
        self.seed = seed

    def sample(self, episode_index: int) -> ParcelSample:
        if episode_index < 0:
            raise ValueError("episode_index cannot be negative")
        rng = random.Random(self.seed + episode_index * 1_000_003)
        cfg = self.config

        if not cfg.enabled:
            return ParcelSample(
                episode_index=episode_index,
                size_scale_xyz=(1.0, 1.0, 1.0),
                mass_kg=(cfg.parcel_mass_kg_min + cfg.parcel_mass_kg_max) / 2,
                friction=(cfg.friction_min + cfg.friction_max) / 2,
                position_xy=(
                    (cfg.parcel_position_x_min + cfg.parcel_position_x_max) / 2,
                    (cfg.parcel_position_y_min + cfg.parcel_position_y_max) / 2,
                ),
                yaw_rad=0.0,
                camera_noise_xyz_m=(0.0, 0.0, 0.0),
                action_delay_steps=0,
                destination="left" if episode_index % 2 == 0 else "right",
            )

        uniform = rng.uniform
        size = tuple(
            uniform(cfg.parcel_size_scale_min, cfg.parcel_size_scale_max)
            for _ in range(3)
        )
        camera_noise = tuple(
            uniform(-cfg.camera_position_noise_m, cfg.camera_position_noise_m)
            for _ in range(3)
        )
        return ParcelSample(
            episode_index=episode_index,
            size_scale_xyz=size,
            mass_kg=uniform(cfg.parcel_mass_kg_min, cfg.parcel_mass_kg_max),
            friction=uniform(cfg.friction_min, cfg.friction_max),
            position_xy=(
                uniform(cfg.parcel_position_x_min, cfg.parcel_position_x_max),
                uniform(cfg.parcel_position_y_min, cfg.parcel_position_y_max),
            ),
            yaw_rad=uniform(cfg.parcel_yaw_rad_min, cfg.parcel_yaw_rad_max),
            camera_noise_xyz_m=camera_noise,
            action_delay_steps=rng.randint(0, cfg.action_delay_steps_max),
            destination="left" if rng.random() < 0.5 else "right",
        )
