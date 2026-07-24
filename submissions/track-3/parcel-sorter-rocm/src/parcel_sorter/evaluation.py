from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import statistics
from typing import Any, Iterable


@dataclass(frozen=True)
class CheckpointAggregate:
    checkpoint: str
    episode_indices: tuple[int, ...]
    success_rate: float
    first_attempt_success_rate: float
    recovery_success_rate: float
    drop_rate: float
    mean_duration_seconds: float
    successful_parcels_per_hour: float
    mean_inference_latency_ms: float
    p95_inference_latency_ms: float
    max_contact_force_n: float
    source_files: tuple[str, ...]

    @property
    def episodes(self) -> int:
        return len(self.episode_indices)

    def to_dict(self) -> dict[str, Any]:
        return {"episodes": self.episodes, **asdict(self)}


def aggregate_checkpoint_evaluations(
    records: Iterable[tuple[str, dict[str, Any]]],
) -> list[CheckpointAggregate]:
    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for source, payload in records:
        checkpoint = str(payload.get("checkpoint", "")).strip()
        episodes = payload.get("episodes")
        if not checkpoint or not isinstance(episodes, list):
            raise ValueError(f"{source} is not an ACT evaluation summary")
        grouped.setdefault(checkpoint, []).append((source, payload))

    aggregates = [
        _aggregate_checkpoint(checkpoint, payloads)
        for checkpoint, payloads in grouped.items()
    ]
    return sorted(
        aggregates,
        key=lambda item: (
            -item.success_rate,
            item.drop_rate,
            item.p95_inference_latency_ms,
            item.max_contact_force_n,
            item.checkpoint,
        ),
    )


def _aggregate_checkpoint(
    checkpoint: str,
    payloads: list[tuple[str, dict[str, Any]]],
) -> CheckpointAggregate:
    seen: set[int] = set()
    results: list[dict[str, Any]] = []
    sources: list[str] = []

    for source, payload in payloads:
        sources.append(source)
        for episode in payload["episodes"]:
            episode_index = int(episode["episode_index"])
            if episode_index in seen:
                raise ValueError(
                    f"checkpoint {checkpoint} repeats episode {episode_index} in {source}"
                )
            seen.add(episode_index)
            results.append(episode["result"])

    if not results:
        raise ValueError(f"checkpoint {checkpoint} has no episodes")

    count = len(results)
    successes = sum(bool(result["success"]) for result in results)
    first_attempt = sum(
        bool(result["success"]) and int(result["retries"]) == 0
        for result in results
    )
    retry_results = [result for result in results if int(result["retries"]) > 0]
    recovered = sum(bool(result["success"]) for result in retry_results)
    dropped = sum(bool(result.get("dropped", False)) for result in results)
    duration = sum(float(result["duration_seconds"]) for result in results)
    latencies = sorted(
        float(latency)
        for result in results
        for latency in result.get("inference_latency_ms", ())
    )
    p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1) if latencies else 0

    return CheckpointAggregate(
        checkpoint=checkpoint,
        episode_indices=tuple(sorted(seen)),
        success_rate=successes / count,
        first_attempt_success_rate=first_attempt / count,
        recovery_success_rate=(
            recovered / len(retry_results) if retry_results else 0.0
        ),
        drop_rate=dropped / count,
        mean_duration_seconds=duration / count,
        successful_parcels_per_hour=(successes / duration * 3600 if duration else 0.0),
        mean_inference_latency_ms=(statistics.fmean(latencies) if latencies else 0.0),
        p95_inference_latency_ms=(latencies[p95_index] if latencies else 0.0),
        max_contact_force_n=max(
            float(result.get("max_contact_force_n", 0.0)) for result in results
        ),
        source_files=tuple(sorted(sources)),
    )
