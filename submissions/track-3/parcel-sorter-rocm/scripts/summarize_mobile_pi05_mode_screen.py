#!/usr/bin/env python3
"""Gate PI0.5 top, side, and cooperative-cradle checkpoint probes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any

from parcel_sorter.mobile_pi05_contract import PI05_GRASP_MODES
from parcel_sorter.mobile_pi05_action_fidelity import action_fidelity_gate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--min-probes-per-mode", type=int, default=1)
    parser.add_argument("--require-action-fidelity", action="store_true")
    args = parser.parse_args()
    probes = []
    for path in args.probe:
        payload = json.loads(path.read_text(encoding="utf-8"))
        probes.extend(payload["screens"] if "screens" in payload else [payload])
    payload = summarize_mode_screen(
        probes,
        min_probes_per_mode=args.min_probes_per_mode,
        require_action_fidelity=args.require_action_fidelity,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["status"] == "passed" else 2


def summarize_mode_screen(
    probes: list[dict[str, Any]],
    *,
    min_probes_per_mode: int = 1,
    require_action_fidelity: bool = False,
) -> dict[str, Any]:
    if min_probes_per_mode < 1:
        raise ValueError("min_probes_per_mode must be positive")
    errors = []
    expected_modes = [str(probe.get("expected_grasp_mode")) for probe in probes]
    mode_counts = Counter(expected_modes)
    for mode in PI05_GRASP_MODES:
        if mode_counts[mode] < min_probes_per_mode:
            errors.append(f"{mode}:insufficient_probe_coverage")
    checkpoints = {str(probe.get("checkpoint")) for probe in probes}
    datasets = {str(probe.get("dataset")) for probe in probes}
    panel_roles = {
        str(probe.get("observation_panel_role", "legacy_unspecified"))
        for probe in probes
    }
    if len(checkpoints) != 1:
        errors.append("checkpoint_mismatch")
    if len(datasets) != 1:
        errors.append("dataset_mismatch")
    if len(panel_roles) != 1:
        errors.append("observation_panel_role_mismatch")
    action_contracts = {
        str(probe.get("action_contract", "pi05_residual_v1")) for probe in probes
    }
    if len(action_contracts) != 1:
        errors.append("action_contract_mismatch")
    absolute_contract = action_contracts == {"pi05_absolute_v1"}
    seed_panels = [probe.get("sample_seeds") for probe in probes]
    sampling_seed_protocol = None
    if any(panel is not None for panel in seed_panels):
        if any(panel is None for panel in seed_panels):
            errors.append("sampling_seed_panel_missing")
        normalized_panels = {
            tuple(int(seed) for seed in panel)
            for panel in seed_panels
            if panel is not None
        }
        if len(normalized_panels) != 1:
            errors.append("sampling_seed_panel_mismatch")
        protocols = {
            str(probe.get("sampling_seed_protocol"))
            for probe in probes
            if probe.get("sampling_seed_protocol") is not None
        }
        if protocols != {"common-random-numbers-per-observation-v1"}:
            errors.append("sampling_seed_protocol_mismatch")
        else:
            sampling_seed_protocol = next(iter(protocols))
    rows = []
    for probe in probes:
        mode = str(probe.get("expected_grasp_mode"))
        action_fidelity = probe.get("action_fidelity")
        action_fidelity_requirements = (
            action_fidelity_gate(action_fidelity)
            if isinstance(action_fidelity, dict)
            else {}
        )
        requirements = {
            "mode_input_hidden": probe.get("grasp_mode_conditioned") is False,
            "three_or_more_samples": int(probe.get("sample_count", 0)) >= 3,
            "mode_correct": probe.get("grasp_mode_correct") is True,
            "finite": probe.get("finite") is True,
            "material_action": (
                probe.get("material_action") is True
                if absolute_contract
                else probe.get("material_residual") is True
            ),
            "no_expert_fallback": probe.get("fallback_to_expert") is False,
            "no_expert_reference": (
                probe.get("expert_reference_used") is False
                if absolute_contract
                else True
            ),
            "full_absolute_authority": (
                probe.get("pure_vla_qualified") is True
                and probe.get("selected_scale_min") == 1.0
                if absolute_contract
                else True
            ),
            "pi05_policy": probe.get("policy_type") == "pi05",
        }
        if absolute_contract and require_action_fidelity:
            requirements["action_fidelity_available"] = bool(
                action_fidelity_requirements
            )
            requirements.update(
                {
                    f"action_fidelity_{name}": passed
                    for name, passed in action_fidelity_requirements.items()
                }
            )
        failed = [name for name, passed in requirements.items() if not passed]
        errors.extend(f"{mode}:{name}" for name in failed)
        rows.append(
            {
                "expected_mode": mode,
                "dataset_index": probe.get("dataset_index"),
                "stage": probe.get("stage"),
                "observable_object_context": probe.get("observable_object_context"),
                "predicted_mode": probe.get("predicted_grasp_mode"),
                "mode_vote_counts": probe.get("mode_vote_counts"),
                "consensus_fraction": probe.get("mode_consensus_fraction"),
                "maximum_residual_norm": probe.get("maximum_residual_norm"),
                "maximum_absolute_motion": probe.get("maximum_absolute_motion"),
                "mean_latency_ms": probe.get("mean_latency_ms"),
                "action_fidelity": action_fidelity,
                "action_fidelity_requirements": action_fidelity_requirements,
                "requirements": requirements,
            }
        )
    per_mode = {}
    for mode in PI05_GRASP_MODES:
        selected = [probe for probe in probes if probe.get("expected_grasp_mode") == mode]
        correct = sum(probe.get("grasp_mode_correct") is True for probe in selected)
        aggregate_votes = Counter()
        for probe in selected:
            aggregate_votes.update(probe.get("mode_vote_counts") or {})
        per_mode[mode] = {
            "probes": len(selected),
            "correct_probes": correct,
            "probe_accuracy": correct / len(selected) if selected else None,
            "aggregate_sample_votes": dict(aggregate_votes),
        }
    valid_mode_accuracies = [
        item["probe_accuracy"]
        for item in per_mode.values()
        if item["probe_accuracy"] is not None
    ]
    correct_probes = sum(probe.get("grasp_mode_correct") is True for probe in probes)
    return {
        "schema_version": 1,
        "protocol": "pi05-three-mode-hidden-input-screen-v2",
        "status": "passed" if not errors else "failed",
        "checkpoint": next(iter(checkpoints)) if len(checkpoints) == 1 else None,
        "dataset": next(iter(datasets)) if len(datasets) == 1 else None,
        "action_contract": (
            next(iter(action_contracts)) if len(action_contracts) == 1 else None
        ),
        "observation_panel_role": (
            next(iter(panel_roles)) if len(panel_roles) == 1 else None
        ),
        "sample_seeds": (
            list(next(iter(normalized_panels)))
            if any(panel is not None for panel in seed_panels)
            and len(normalized_panels) == 1
            else None
        ),
        "sampling_seed_protocol": sampling_seed_protocol,
        "errors": errors,
        "error_count": len(errors),
        "minimum_probes_per_mode": min_probes_per_mode,
        "action_fidelity_required": require_action_fidelity,
        "probe_counts_by_mode": dict(mode_counts),
        "metrics": {
            "probes": len(probes),
            "correct_probes": correct_probes,
            "probe_accuracy": correct_probes / len(probes) if probes else None,
            "macro_mode_accuracy": (
                sum(valid_mode_accuracies) / len(valid_mode_accuracies)
                if valid_mode_accuracies
                else None
            ),
            "per_mode": per_mode,
        },
        "modes": rows,
        "claim_boundary": (
            "Offline three-mode routing and action screen only. A training-distribution "
            "panel is a development gate, not generalization evidence; closed-loop task "
            "success is evaluated separately."
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
