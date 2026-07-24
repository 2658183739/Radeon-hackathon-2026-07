"""Deterministic episode planning for balanced catalog collection and evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .config import ParcelProfileConfig


CATALOG_EPISODE_STRIDE = 1_000_000


@dataclass(frozen=True)
class EpisodeSpec:
    """One reproducible run and the profile it should sample, if any."""

    episode_index: int
    local_index: int
    profile_id: str | None = None


def catalog_episode_index(profile_index: int, local_index: int) -> int:
    """Map a profile/local pair to a collision-resistant episode namespace."""
    if profile_index < 0 or local_index < 0:
        raise ValueError("profile_index and local_index cannot be negative")
    if local_index >= CATALOG_EPISODE_STRIDE:
        raise ValueError("local_index exceeds catalog episode namespace")
    return profile_index * CATALOG_EPISODE_STRIDE + local_index


def build_episode_plan(
    profiles: tuple[ParcelProfileConfig, ...],
    episodes: int,
    start_episode: int,
    selected_profile_ids: tuple[str, ...] = (),
    *,
    allow_evaluation_only: bool = True,
) -> tuple[EpisodeSpec, ...]:
    """Build a stable plan without relying on loop order or global RNG state.

    With no profile filter this preserves the legacy contiguous episode range.
    With a filter, ``episodes`` is the number of episodes per selected profile;
    each profile receives its own namespace so two profiles cannot overwrite an
    audit trace with the same local index.
    """
    if episodes < 1 or start_episode < 0:
        raise ValueError("episodes must be positive and start_episode cannot be negative")
    if not selected_profile_ids:
        return tuple(
            EpisodeSpec(start_episode + offset, start_episode + offset)
            for offset in range(episodes)
        )

    if len(selected_profile_ids) != len(set(selected_profile_ids)):
        raise ValueError("selected profile ids must be unique")
    by_id = {profile.profile_id: (index, profile) for index, profile in enumerate(profiles)}
    unknown = sorted(set(selected_profile_ids) - set(by_id))
    if unknown:
        raise ValueError(f"unknown parcel profile(s): {', '.join(unknown)}")

    plan: list[EpisodeSpec] = []
    for profile_id in selected_profile_ids:
        profile_index, profile = by_id[profile_id]
        if profile.evaluation_only and not allow_evaluation_only:
            raise ValueError(f"evaluation-only parcel profile cannot be collected: {profile_id}")
        for local_index in range(start_episode, start_episode + episodes):
            plan.append(
                EpisodeSpec(
                    episode_index=catalog_episode_index(profile_index, local_index),
                    local_index=local_index,
                    profile_id=profile_id,
                )
            )
    return tuple(plan)
