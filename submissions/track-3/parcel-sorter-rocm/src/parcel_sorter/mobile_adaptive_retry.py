"""Auditable episodic strategy memory for bounded mobile-task retries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class RetryStrategy:
    name: str
    policy_mode: str
    force_memory: bool
    learned_arm_authority: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PASH_ARM = RetryStrategy("pash_arm", "base_arm_residual", True, True)
PASH_BASE = RetryStrategy("pash_base", "base_residual", True, False)
EXPERT_RECOVERY = RetryStrategy("expert_recovery", "shadow", False, False)
DEFAULT_STRATEGIES = (PASH_ARM, PASH_BASE, EXPERT_RECOVERY)


def classify_mobile_failure(summary: dict[str, Any]) -> str | None:
    """Return the first failed closed-loop gate, or None for a valid success."""

    if bool(summary.get("success")):
        return None
    suction = summary.get("suction") or {}
    cradle = (summary.get("cradle") or {}).get("physical") or {}
    peak_force = max(
        float(suction.get("max_contact_force_n") or 0.0),
        float(suction.get("max_suction_force_n") or 0.0),
        float(cradle.get("max_contact_force_n") or 0.0),
    )
    if peak_force >= 35.0:
        return "force_safety_abort"
    ordered_gates = (
        ("scene_stable", "scene_stability"),
        ("latched", "suction_latch"),
        ("lift_success", "lift_success"),
        ("transport_success", "transport_success"),
        ("placed_before_release", "placement_success"),
        ("released", "release_success"),
    )
    for field, stage in ordered_gates:
        if not bool(summary.get(field)):
            return stage
    return "unclassified"


def strategy_context(
    *, profile: str, mass_kg: float, previous_failure: str | None
) -> str:
    if not profile.strip():
        raise ValueError("profile must be non-empty")
    if not math.isfinite(mass_kg) or mass_kg <= 0.0:
        raise ValueError("mass_kg must be finite and positive")
    mass_band = "light" if mass_kg < 0.40 else "medium" if mass_kg < 0.65 else "heavy"
    return f"{profile}:{mass_band}:{previous_failure or 'initial'}"


class EpisodicStrategyMemory:
    """Small persisted bandit memory; it selects strategies, not robot actions."""

    def __init__(self, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        if payload and payload.get("protocol") != "pash-episodic-strategy-memory-v1":
            raise ValueError("unsupported episodic strategy-memory protocol")
        contexts = payload.get("contexts") or {}
        if not isinstance(contexts, dict):
            raise ValueError("strategy-memory contexts must be an object")
        self.contexts: dict[str, dict[str, dict[str, int]]] = contexts

    @classmethod
    def load(cls, path: Path) -> "EpisodicStrategyMemory":
        if not path.exists():
            return cls()
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "protocol": "pash-episodic-strategy-memory-v1",
            "contexts": self.contexts,
            "claim_boundary": (
                "episode-level strategy selection only; model weights never change during "
                "an active rollout and retry success is reported separately from first-attempt success"
            ),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.parent / f".{path.name}.tmp"
        temporary.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        temporary.replace(path)

    def record(
        self,
        *,
        context: str,
        strategy: RetryStrategy,
        success: bool,
        force_abort: bool,
    ) -> None:
        if not context:
            raise ValueError("context must be non-empty")
        for key in (context, _global_context(context)):
            stats = self.contexts.setdefault(key, {}).setdefault(
                strategy.name,
                {"attempts": 0, "successes": 0, "force_aborts": 0},
            )
            stats["attempts"] = int(stats.get("attempts") or 0) + 1
            stats["successes"] = int(stats.get("successes") or 0) + int(success)
            stats["force_aborts"] = int(stats.get("force_aborts") or 0) + int(force_abort)

    def score(self, *, context: str, strategy: RetryStrategy) -> float:
        task_score = self._score_one(context=context, strategy=strategy)
        global_key = _global_context(context)
        global_stats = self.contexts.get(global_key, {}).get(strategy.name, {})
        if int(global_stats.get("attempts") or 0) == 0:
            return task_score
        return 0.75 * task_score + 0.25 * self._score_one(
            context=global_key, strategy=strategy
        )

    def _score_one(self, *, context: str, strategy: RetryStrategy) -> float:
        context_stats = self.contexts.get(context, {})
        stats = context_stats.get(strategy.name, {})
        attempts = int(stats.get("attempts") or 0)
        successes = int(stats.get("successes") or 0)
        force_aborts = int(stats.get("force_aborts") or 0)
        total_attempts = sum(
            int(item.get("attempts") or 0) for item in context_stats.values()
        )
        posterior_mean = (successes + 1.0) / (attempts + 2.0)
        exploration = math.sqrt(2.0 * math.log(total_attempts + 2.0) / (attempts + 1.0))
        force_penalty = 2.0 * force_aborts / (attempts + 1.0)
        return posterior_mean + 0.15 * exploration - force_penalty


def choose_retry_strategy(
    *,
    memory: EpisodicStrategyMemory,
    context: str,
    previous_failure: str | None,
    attempted_strategy_names: Iterable[str] = (),
    cooperative_cradle: bool = False,
    strategies: Iterable[RetryStrategy] = DEFAULT_STRATEGIES,
) -> RetryStrategy:
    """Choose the highest-scoring strategy allowed by failure-specific safety rules."""

    attempted = set(attempted_strategy_names)
    candidates = list(strategies)
    if cooperative_cradle:
        candidates = [item for item in candidates if not item.learned_arm_authority]
    if previous_failure == "force_safety_abort":
        candidates = [item for item in candidates if item.name == EXPERT_RECOVERY.name]
    elif previous_failure in {
        "suction_latch",
        "lift_success",
        "placement_success",
        "release_success",
    }:
        candidates = [item for item in candidates if not item.learned_arm_authority]
    if not candidates:
        raise ValueError("no retry strategy satisfies the safety constraints")
    untried = [item for item in candidates if item.name not in attempted]
    if untried:
        candidates = untried
    preference = {PASH_ARM.name: 2, PASH_BASE.name: 1, EXPERT_RECOVERY.name: 0}
    return max(
        candidates,
        key=lambda item: (memory.score(context=context, strategy=item), preference[item.name]),
    )


def summarize_adaptive_attempts(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    if not attempts:
        raise ValueError("adaptive retry summary requires at least one attempt")
    valid = [item for item in attempts if item.get("summary_available")]
    successes = [item for item in valid if item.get("success")]
    force_aborts = sum(item.get("failure_stage") == "force_safety_abort" for item in valid)
    first_success_index = next(
        (int(item["attempt_index"]) for item in valid if item.get("success")), None
    )
    return {
        "schema_version": 1,
        "protocol": "pash-adaptive-retry-v1",
        "attempts_requested": len(attempts),
        "attempts_with_summary": len(valid),
        "first_attempt_success": bool(valid and valid[0].get("success")),
        "eventual_success": bool(successes),
        "attempts_to_success": first_success_index + 1 if first_success_index is not None else None,
        "force_abort_count": force_aborts,
        "primitive_gaps": [
            str(item["failure_stage"])
            for item in valid
            if item.get("failure_stage") is not None
        ],
        "strategies_attempted": [str(item["strategy"]["name"]) for item in attempts],
        "attempts": attempts,
        "claim_boundary": (
            "eventual success includes bounded retries and must not be reported as first-attempt "
            "success; this loop adapts strategy authority while weight updates remain near-line"
        ),
    }


def build_primitive_acquisition_manifest(
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Convert retry outcomes into an InSight-style primitive-gap writeback manifest."""

    if not attempts:
        raise ValueError("primitive acquisition requires at least one attempt")
    gaps = []
    acquisitions = []
    pending_gap: dict[str, Any] | None = None
    for attempt in attempts:
        if not attempt.get("summary_available"):
            continue
        failure_stage = attempt.get("failure_stage")
        if failure_stage:
            pending_gap = {
                "source_attempt_index": int(attempt["attempt_index"]),
                "primitive": str(failure_stage),
                "source_strategy": str(attempt["strategy"]["name"]),
                "source_summary": attempt.get("summary"),
            }
            gaps.append(dict(pending_gap))
            continue
        if attempt.get("success") and pending_gap is not None:
            acquisitions.append(
                {
                    **pending_gap,
                    "recovery_attempt_index": int(attempt["attempt_index"]),
                    "recovery_strategy": str(attempt["strategy"]["name"]),
                    "successful_summary": attempt.get("summary"),
                    "writeback_status": "eligible_after_dataset_audit",
                    "primitive_task_text": (
                        f"Recover the {pending_gap['primitive']} primitive while preserving "
                        "the 35 N force limit and complete the parcel task."
                    ),
                }
            )
            pending_gap = None
    return {
        "schema_version": 1,
        "protocol": "pash-primitive-acquisition-v1",
        "primitive_gaps": gaps,
        "successful_acquisitions": acquisitions,
        "retraining_candidate_count": len(acquisitions),
        "claim_boundary": (
            "successful recovery summaries are candidates for audited primitive-level data "
            "extraction; they are not training data until sensor/action frames pass dataset audit"
        ),
    }


def _global_context(context: str) -> str:
    parts = context.split(":", 2)
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("strategy context must be profile:mass_band:primitive")
    return f"*:{parts[1]}:{parts[2]}"
