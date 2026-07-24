from __future__ import annotations

from dataclasses import dataclass
import math
import statistics


@dataclass(frozen=True)
class EpisodeResult:
    success: bool
    retries: int
    duration_seconds: float
    inference_latency_ms: tuple[float, ...]
    dropped: bool = False
    max_contact_force_n: float = 0.0

    def validate(self) -> None:
        if self.retries < 0:
            raise ValueError("retries cannot be negative")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if any(value < 0 for value in self.inference_latency_ms):
            raise ValueError("inference latency cannot be negative")
        if self.max_contact_force_n < 0:
            raise ValueError("max contact force cannot be negative")


class MetricsAccumulator:
    def __init__(self) -> None:
        self._episodes: list[EpisodeResult] = []

    def add(self, result: EpisodeResult) -> None:
        result.validate()
        self._episodes.append(result)

    def summary(self) -> dict[str, float | int]:
        if not self._episodes:
            raise ValueError("at least one episode is required")

        count = len(self._episodes)
        successes = sum(result.success for result in self._episodes)
        first_attempt = sum(
            result.success and result.retries == 0 for result in self._episodes
        )
        retry_episodes = [result for result in self._episodes if result.retries > 0]
        recovered = sum(result.success for result in retry_episodes)
        dropped = sum(result.dropped for result in self._episodes)
        duration = sum(result.duration_seconds for result in self._episodes)
        latencies = sorted(
            latency
            for result in self._episodes
            for latency in result.inference_latency_ms
        )
        p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1) if latencies else 0

        return {
            "episodes": count,
            "success_rate": successes / count,
            "first_attempt_success_rate": first_attempt / count,
            "recovery_success_rate": recovered / len(retry_episodes) if retry_episodes else 0.0,
            "drop_rate": dropped / count,
            "mean_duration_seconds": duration / count,
            "successful_parcels_per_hour": successes / duration * 3600,
            "mean_inference_latency_ms": statistics.fmean(latencies) if latencies else 0.0,
            "p95_inference_latency_ms": latencies[p95_index] if latencies else 0.0,
            "max_contact_force_n": max(
                result.max_contact_force_n for result in self._episodes
            ),
        }
