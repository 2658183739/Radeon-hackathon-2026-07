"""Auditable data and action-semantics contract for PI0.5 checkpoints."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .mobile_dataset import infer_mobile_policy_modality, mobile_policy_visual_keys
from .mobile_pi05_contract import (
    MOBILE_PI05_ABSOLUTE_ACTION_NAMES,
    MOBILE_PI05_ABSOLUTE_STATE_NAMES,
    MOBILE_PI05_INCREMENTAL_ACTION_NAMES,
    MOBILE_PI05_RESIDUAL_ACTION_NAMES,
    MOBILE_PI05_STATE_NAMES,
)
from .pi05_weighted_loss import PI05_STAGE_LOSS_WEIGHTING_SCOPE


PI05_TRAINING_CONTRACT_FILENAME = "PI05_TRAINING_CONTRACT.json"
PI05_RESIDUAL_ACTION_SEMANTICS = "bounded_expert_relative_cartesian_residual_v1"
PI05_ABSOLUTE_ACTION_SEMANTICS = "expert_independent_absolute_mobile_action_v1"
PI05_INCREMENTAL_ACTION_SEMANTICS = "expert_independent_incremental_se3_mobile_action_v1"
PI05_ACTION_SEMANTICS = PI05_RESIDUAL_ACTION_SEMANTICS
PI05_STATE_SEMANTICS = "observable_robot_contact_geometry_history_v1"
PI05_NORMALIZATION_SEMANTICS = "lerobot_quantile_q01_q99_v1"


def build_pi05_training_contract(
    dataset_root: str | Path,
    *,
    base_model: str,
    base_revision: str,
    chunk_size: int,
    n_action_steps: int,
    state_token_protocol: str | None = None,
    mode_head_protocol: str | None = None,
    mode_head_class_weights: list[float] | None = None,
    stage_loss_weights: list[float] | None = None,
    action_projection_protocol: str | None = None,
) -> dict[str, Any]:
    """Build a canonical contract tying a checkpoint to data semantics."""

    root = Path(dataset_root).resolve()
    info_path = root / "meta" / "info.json"
    stats_path = root / "meta" / "stats.json"
    manifest_paths = [
        path
        for path in (
            root / "PI05_RESIDUAL_DATASET_MANIFEST.json",
            root / "PI05_ABSOLUTE_DATASET_MANIFEST.json",
            root / "PI05_INCREMENTAL_DATASET_MANIFEST.json",
        )
        if path.is_file()
    ]
    if not info_path.is_file() or not stats_path.is_file() or len(manifest_paths) != 1:
        raise ValueError("PI0.5 dataset is missing info, stats, or provenance manifest")
    manifest_path = manifest_paths[0]
    if chunk_size <= 0 or not 1 <= n_action_steps <= chunk_size:
        raise ValueError("invalid PI0.5 action chunk contract")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    features = info.get("features", {})
    state = features.get("observation.state", {})
    action = features.get("action", {})
    state_names = tuple(state.get("names") or ())
    action_names = tuple(action.get("names") or ())
    contracts = {
        "residual_v1": (
            MOBILE_PI05_STATE_NAMES,
            MOBILE_PI05_RESIDUAL_ACTION_NAMES,
            PI05_RESIDUAL_ACTION_SEMANTICS,
        ),
        "absolute_v1": (
            MOBILE_PI05_ABSOLUTE_STATE_NAMES,
            MOBILE_PI05_ABSOLUTE_ACTION_NAMES,
            PI05_ABSOLUTE_ACTION_SEMANTICS,
        ),
        "incremental_se3_v1": (
            MOBILE_PI05_ABSOLUTE_STATE_NAMES,
            MOBILE_PI05_INCREMENTAL_ACTION_NAMES,
            PI05_INCREMENTAL_ACTION_SEMANTICS,
        ),
    }
    matches = [
        (name, expected_state, expected_action, semantics)
        for name, (expected_state, expected_action, semantics) in contracts.items()
        if state_names == tuple(expected_state) and action_names == tuple(expected_action)
    ]
    if len(matches) != 1:
        raise ValueError("PI0.5 state/action feature names do not match a supported contract")
    action_contract, expected_state_names, expected_action_names, action_semantics = matches[0]
    if state.get("shape") != [len(expected_state_names)]:
        raise ValueError("PI0.5 state feature shape does not match its named contract")
    if action.get("shape") != [len(expected_action_names)]:
        raise ValueError("PI0.5 action feature shape does not match its named contract")
    policy_visual_modality = infer_mobile_policy_modality(features)
    policy_visual_keys = list(mobile_policy_visual_keys(policy_visual_modality))
    fps = int(info.get("fps", 0))
    if fps <= 0:
        raise ValueError("PI0.5 dataset FPS must be positive")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "protocol": "parcel-pi05-training-contract-v1",
        "base_model": str(base_model),
        "base_revision": str(base_revision),
        "dataset_root": str(root),
        "dataset_fps_hz": fps,
        "state_dimension": len(expected_state_names),
        "state_names": list(expected_state_names),
        "state_semantics": PI05_STATE_SEMANTICS,
        "action_contract": action_contract,
        "action_dimension": len(expected_action_names),
        "action_names": list(expected_action_names),
        "action_semantics": action_semantics,
        "policy_visual_modality": policy_visual_modality,
        "policy_visual_keys": policy_visual_keys,
        "action_chunk_size": int(chunk_size),
        "executed_action_steps": int(n_action_steps),
        "normalization_semantics": PI05_NORMALIZATION_SEMANTICS,
        "normalization_stats_sha256": _sha256(stats_path),
        "dataset_manifest_sha256": _sha256(manifest_path),
        "normalization_stats_policy": manifest.get("normalization_stats_policy"),
        "mode_conditioning_policy": manifest.get("mode_conditioning_policy"),
        "task_language_policy": manifest.get("task_language_policy"),
        "state_token_protocol": state_token_protocol,
        "mode_head_protocol": mode_head_protocol,
        "mode_head_class_weights": mode_head_class_weights,
        "stage_loss_weights": stage_loss_weights,
        "stage_loss_weighting_scope": (
            PI05_STAGE_LOSS_WEIGHTING_SCOPE
            if stage_loss_weights is not None
            else None
        ),
        "action_projection_protocol": action_projection_protocol,
        "absolute_delta_policy": (
            {
                "base": "velocity_residual",
                "left_contact": "expert_anchor_relative_cartesian_delta_m",
                "right_contact": "expert_anchor_relative_cartesian_delta_m",
                "orientation": "deterministic_surface_normal_lock",
                "mode": "categorical_logits",
                "release": "deterministic_interlock",
            }
            if action_contract == "residual_v1"
            else {
                "base": "absolute_velocity_command",
                "left_arm": "absolute_cartesian_pose_and_tool_command",
                "right_arm": "absolute_cartesian_pose_and_tool_command",
                "mode": "categorical_logits",
                "release": "deterministic_interlock",
                "expert_reference": "forbidden",
            }
            if action_contract == "absolute_v1"
            else {
                "base": "absolute_velocity_command",
                "left_arm": "incremental_world_frame_se3_and_tool_command",
                "right_arm": "incremental_world_frame_se3_and_tool_command",
                "rotation": "shortest_rotation_vector_target_times_current_inverse",
                "mode": "categorical_logits",
                "release": "deterministic_interlock",
                "expert_reference": "forbidden",
            }
        ),
    }
    payload["contract_sha256"] = _payload_sha256(payload)
    return payload


def with_pi05_architecture_protocols(
    payload: dict[str, Any],
    *,
    state_token_protocol: str | None,
    mode_head_protocol: str | None,
    action_projection_protocol: str | None = None,
) -> dict[str, Any]:
    """Re-fingerprint a contract after explicitly fixing adapter protocols."""

    result = dict(payload)
    result.pop("contract_sha256", None)
    result["state_token_protocol"] = state_token_protocol
    result["mode_head_protocol"] = mode_head_protocol
    result["action_projection_protocol"] = action_projection_protocol
    result["contract_sha256"] = _payload_sha256(result)
    return result


def validate_pi05_training_contract(
    payload: dict[str, Any],
    *,
    state_dim: int,
    action_dim: int,
    chunk_size: int,
    required_state_token_protocol: str | None = None,
    required_mode_head_protocol: str | None = None,
    required_action_projection_protocol: str | None = None,
    required_stage_loss_weights: list[float] | tuple[float, ...] | None = None,
    required_visual_keys: list[str] | tuple[str, ...] | set[str] | None = None,
) -> str:
    """Reject a checkpoint whose stored training semantics are inconsistent."""

    claimed = str(payload.get("contract_sha256") or "")
    unsigned = {key: value for key, value in payload.items() if key != "contract_sha256"}
    if claimed != _payload_sha256(unsigned):
        raise ValueError("PI0.5 training contract fingerprint mismatch")
    action_semantics = payload.get("action_semantics")
    supported = {
        PI05_RESIDUAL_ACTION_SEMANTICS: (
            MOBILE_PI05_STATE_NAMES,
            MOBILE_PI05_RESIDUAL_ACTION_NAMES,
            "residual_v1",
        ),
        PI05_ABSOLUTE_ACTION_SEMANTICS: (
            MOBILE_PI05_ABSOLUTE_STATE_NAMES,
            MOBILE_PI05_ABSOLUTE_ACTION_NAMES,
            "absolute_v1",
        ),
        PI05_INCREMENTAL_ACTION_SEMANTICS: (
            MOBILE_PI05_ABSOLUTE_STATE_NAMES,
            MOBILE_PI05_INCREMENTAL_ACTION_NAMES,
            "incremental_se3_v1",
        ),
    }
    if action_semantics not in supported:
        raise ValueError("PI0.5 training contract mismatch: action_semantics")
    expected_state_names, expected_action_names, expected_action_contract = supported[
        action_semantics
    ]
    expected = {
        "state_dimension": state_dim,
        "action_dimension": action_dim,
        "action_chunk_size": chunk_size,
        "state_semantics": PI05_STATE_SEMANTICS,
        "action_semantics": action_semantics,
        "normalization_semantics": PI05_NORMALIZATION_SEMANTICS,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            raise ValueError(f"PI0.5 training contract mismatch: {field}")
    if payload.get("action_contract", "residual_v1") != expected_action_contract:
        raise ValueError("PI0.5 training contract action contract mismatch")
    if payload.get("state_names") != list(expected_state_names):
        raise ValueError("PI0.5 training contract state names mismatch")
    if payload.get("action_names") != list(expected_action_names):
        raise ValueError("PI0.5 training contract action names mismatch")
    if int(payload.get("dataset_fps_hz", 0)) <= 0:
        raise ValueError("PI0.5 training contract has invalid control frequency")
    if required_visual_keys is not None:
        # Contracts written before the wrist ablation pre-registration used the
        # fixed overhead RGB-D input but did not yet serialize those two keys.
        contracted_visual_keys = payload.get("policy_visual_keys")
        if contracted_visual_keys is None:
            contracted_visual_keys = list(mobile_policy_visual_keys("rgbd"))
        if set(contracted_visual_keys) != set(required_visual_keys):
            raise ValueError("PI0.5 training contract mismatch: policy_visual_keys")
    architecture = {
        "state_token_protocol": required_state_token_protocol,
        "mode_head_protocol": required_mode_head_protocol,
        "action_projection_protocol": required_action_projection_protocol,
    }
    for field, required in architecture.items():
        if required is not None and payload.get(field) != required:
            raise ValueError(f"PI0.5 training contract mismatch: {field}")
    stage_loss_weights = payload.get("stage_loss_weights")
    if stage_loss_weights is not None and (
        not isinstance(stage_loss_weights, list)
        or len(stage_loss_weights) != 6
        or any(
            not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) <= 0.0
            for value in stage_loss_weights
        )
    ):
        raise ValueError("PI0.5 training contract mismatch: stage_loss_weights")
    if stage_loss_weights is not None and payload.get(
        "stage_loss_weighting_scope"
    ) != PI05_STAGE_LOSS_WEIGHTING_SCOPE:
        raise ValueError(
            "PI0.5 training contract mismatch: stage_loss_weighting_scope"
        )
    if required_stage_loss_weights is not None:
        required_weights = [float(value) for value in required_stage_loss_weights]
        if stage_loss_weights != required_weights:
            raise ValueError("PI0.5 training contract mismatch: stage_loss_weights")
    return claimed


def find_pi05_training_contract(checkpoint: str | Path) -> Path | None:
    """Find a run-level contract from a LeRobot pretrained-model directory."""

    current = Path(checkpoint).resolve()
    for parent in (current, *current.parents[:5]):
        candidate = parent / PI05_TRAINING_CONTRACT_FILENAME
        if candidate.is_file():
            return candidate
    return None


def _payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
