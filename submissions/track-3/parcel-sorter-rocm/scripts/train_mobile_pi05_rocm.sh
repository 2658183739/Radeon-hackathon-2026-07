#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/mobile-pi05-residual-seed-v1}"
OUTPUT_DIR="${2:-/root/pi05-runs/mobile-pi05-residual-lora-v1}"
DEFAULT_BASE_MODEL=lerobot/pi05_base
if [[ -f /root/pi05-assets/pi05-base-local/model.safetensors ]]; then
  DEFAULT_BASE_MODEL=/root/pi05-assets/pi05-base-local
fi
BASE_MODEL="${PI05_BASE_MODEL:-${DEFAULT_BASE_MODEL}}"
BASE_REVISION="${PI05_BASE_REVISION:-7de663972b7817d2c4cf2d84c821153dfea772e9}"
STEPS="${MOBILE_PI05_STEPS:-1000}"
BATCH_SIZE="${MOBILE_PI05_BATCH_SIZE:-1}"
NUM_WORKERS="${MOBILE_PI05_NUM_WORKERS:-0}"
LORA_R="${MOBILE_PI05_LORA_R:-16}"
LORA_ALPHA="${MOBILE_PI05_LORA_ALPHA:-32}"
SAVE_FREQ="${MOBILE_PI05_SAVE_FREQ:-${STEPS}}"
CHUNK_SIZE="${MOBILE_PI05_CHUNK_SIZE:-30}"
N_ACTION_STEPS="${MOBILE_PI05_N_ACTION_STEPS:-10}"
RESUME_CONFIG="${MOBILE_PI05_RESUME_CONFIG:-}"
RESUME_DECAY_STEPS="${MOBILE_PI05_RESUME_DECAY_STEPS:-}"
RESUME_WARMUP_STEPS="${MOBILE_PI05_RESUME_WARMUP_STEPS:-}"
MODE_LOSS_WEIGHT="${MOBILE_PI05_MODE_LOSS_WEIGHT:-1}"
MODE_CE_WEIGHT="${MOBILE_PI05_MODE_CE_WEIGHT:-0}"
STATE_TOKEN="${MOBILE_PI05_STATE_TOKEN:-0}"
MODE_HEAD="${MOBILE_PI05_MODE_HEAD:-0}"
MODE_HEAD_POOLING="${MOBILE_PI05_MODE_HEAD_POOLING:-masked_mean}"
MODE_HEAD_CE_WEIGHT="${MOBILE_PI05_MODE_HEAD_CE_WEIGHT:-0}"
MODE_HEAD_CLASS_WEIGHTS="${MOBILE_PI05_MODE_HEAD_CLASS_WEIGHTS:-}"
STAGE_LOSS_WEIGHTS="${MOBILE_PI05_STAGE_LOSS_WEIGHTS:-}"
WRIST_RGBD="${MOBILE_PI05_WRIST_RGBD:-0}"
ACTION_CONTRACT="${MOBILE_PI05_ACTION_CONTRACT:-residual_v1}"
FULL_ACTION_PROJECTIONS="${MOBILE_PI05_FULL_ACTION_PROJECTIONS:-0}"
if [[ "${ACTION_CONTRACT}" != "residual_v1" && "${ACTION_CONTRACT}" != "absolute_v1" ]]; then
  echo "ERROR: MOBILE_PI05_ACTION_CONTRACT must be residual_v1 or absolute_v1" >&2
  exit 2
fi
if [[ "${WRIST_RGBD}" != "0" && "${WRIST_RGBD}" != "1" ]]; then
  echo "ERROR: MOBILE_PI05_WRIST_RGBD must be 0 or 1" >&2
  exit 2
fi
if [[ "${FULL_ACTION_PROJECTIONS}" != "0" && "${FULL_ACTION_PROJECTIONS}" != "1" ]]; then
  echo "ERROR: MOBILE_PI05_FULL_ACTION_PROJECTIONS must be 0 or 1" >&2
  exit 2
fi

export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export HF_HOME="${HF_HOME:-/root/.cache/huggingface}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export TOKENIZERS_PARALLELISM=false
export MOBILE_PI05_ACTION_CONTRACT="${ACTION_CONTRACT}"

cd "${ROOT_DIR}"
source scripts/activate_radeon_env.sh
bash scripts/preflight_radeon.sh
if [[ "${MOBILE_PI05_ALLOW_CHECKPOINT_CLEANUP:-0}" == "1" ]]; then
  bash scripts/cleanup_old_checkpoints_rocm.sh
else
  echo "checkpoint_cleanup=skipped (set MOBILE_PI05_ALLOW_CHECKPOINT_CLEANUP=1 to opt in)"
fi
python -c "import peft" 2>/dev/null || {
  echo "ERROR: PI0.5 LoRA requires peft>=0.18.0,<1.0.0" >&2
  exit 3
}

test -f "${DATASET_ROOT}/meta/info.json" || {
  echo "ERROR: PI0.5 LeRobotDataset not found: ${DATASET_ROOT}" >&2
  exit 4
}

MOBILE_PI05_MIN_RECOVERY_EPISODES="${MOBILE_PI05_MIN_RECOVERY_EPISODES:-6}"
MOBILE_PI05_MIN_NONZERO_FRAMES="${MOBILE_PI05_MIN_NONZERO_FRAMES:-60}"
MOBILE_PI05_MIN_EPISODES_PER_MODE="${MOBILE_PI05_MIN_EPISODES_PER_MODE:-2}"
python - "${DATASET_ROOT}" "${MOBILE_PI05_MIN_RECOVERY_EPISODES}" \
  "${MOBILE_PI05_MIN_NONZERO_FRAMES}" "${MOBILE_PI05_MIN_EPISODES_PER_MODE}" \
  "${MOBILE_PI05_ALLOW_ZERO_SEED:-0}" "${WRIST_RGBD}" "${ACTION_CONTRACT}" <<'PY'
import json
from pathlib import Path
import sys

from parcel_sorter.mobile_pi05_contract import (
    MOBILE_PI05_ABSOLUTE_ACTION_NAMES,
    MOBILE_PI05_ABSOLUTE_STATE_NAMES,
    MOBILE_PI05_RESIDUAL_ACTION_NAMES,
    MOBILE_PI05_STATE_NAMES,
)
from parcel_sorter.mobile_pi05_normalization import unsafe_quantile_dimensions
from parcel_sorter.mobile_dataset import (
    infer_mobile_policy_modality,
    mobile_policy_visual_keys,
)

root = Path(sys.argv[1])
minimum_episodes = int(sys.argv[2])
minimum_frames = int(sys.argv[3])
minimum_per_mode = int(sys.argv[4])
allow_zero_seed = sys.argv[5] == "1"
wrist_rgbd = sys.argv[6] == "1"
action_contract = sys.argv[7]
absolute_contract = action_contract == "absolute_v1"
state_names = (
    MOBILE_PI05_ABSOLUTE_STATE_NAMES if absolute_contract else MOBILE_PI05_STATE_NAMES
)
action_names = (
    MOBILE_PI05_ABSOLUTE_ACTION_NAMES
    if absolute_contract
    else MOBILE_PI05_RESIDUAL_ACTION_NAMES
)
manifest_path = root / (
    "PI05_ABSOLUTE_DATASET_MANIFEST.json"
    if absolute_contract
    else "PI05_RESIDUAL_DATASET_MANIFEST.json"
)
if not manifest_path.is_file():
    raise SystemExit("ERROR: PI0.5 dataset manifest is missing for the action contract")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
info = json.loads((root / "meta/info.json").read_text(encoding="utf-8"))
observed_visual_modality = infer_mobile_policy_modality(info.get("features", {}))
required_visual_modality = "rgbd_wrist" if wrist_rgbd else "rgbd"
if observed_visual_modality != required_visual_modality:
    raise SystemExit(
        "ERROR: PI0.5 dataset visual contract mismatch: "
        f"observed={observed_visual_modality}, required={required_visual_modality}"
    )
required_visual_keys = list(mobile_policy_visual_keys(required_visual_modality))
if manifest.get("policy_visual_keys") not in (None, required_visual_keys):
    raise SystemExit("ERROR: PI0.5 residual manifest visual keys mismatch")
stats_path = root / "meta/stats.json"
if not stats_path.is_file():
    raise SystemExit("ERROR: PI0.5 dataset normalization stats are missing")
stats = json.loads(stats_path.read_text(encoding="utf-8"))
unsafe_stats = {
    feature: list(unsafe_quantile_dimensions(stats.get(feature, {}), names))
    for feature, names in (
        ("observation.state", state_names),
        ("action", action_names),
    )
}
if any(unsafe_stats.values()):
    raise SystemExit(
        "ERROR: PI0.5 quantile normalization would amplify variable channels: "
        f"{unsafe_stats}"
    )
nonzero_frames = int(
    manifest.get(
        "nonzero_base_command_frames"
        if absolute_contract
        else "nonzero_contact_residual_frames",
        0,
    )
)
recovery_entries = [
    item
    for item in manifest.get("episode_manifests", ())
    if item.get("seed_role")
    == (
        "verified_successful_absolute_action_supervision"
        if absolute_contract
        else "verified_successful_recovery_supervision"
    )
]
independent_recovery_ids = {
    (
        item.get("source_dataset"),
        item.get("source_episode_index"),
        item.get("source_episode_id") or item.get("episode_id"),
    )
    for item in recovery_entries
}
recovery_episodes = len(independent_recovery_ids)
replayed_training_episodes = len(recovery_entries) - recovery_episodes
mode_names = ("top_suction", "side_suction", "cooperative_cradle")
mode_episode_counts = {
    mode: int((manifest.get("mode_episode_counts") or {}).get(mode, 0))
    for mode in mode_names
}
if not any(mode_episode_counts.values()):
    for item in recovery_entries:
        for mode in item.get("grasp_modes", ()):
            if mode in mode_episode_counts:
                mode_episode_counts[mode] += 1
missing_modes = {
    mode: count
    for mode, count in mode_episode_counts.items()
    if count < minimum_per_mode
}
verified_summary = manifest.get("verified_recovery_summary") or manifest.get(
    "verified_recovery_summaries"
)
mode_conditioning_policy = manifest.get("mode_conditioning_policy")
lift_residual_supervision = manifest.get("lift_residual_supervision")
target_leakage_audit = manifest.get("target_leakage_audit") or {}
if not allow_zero_seed and (
    not verified_summary
    or recovery_episodes < minimum_episodes
    or nonzero_frames < minimum_frames
    or missing_modes
    or mode_conditioning_policy != "hidden_all_stages"
    or (
        not absolute_contract
        and lift_residual_supervision != "smooth_stage_progress_v2"
    )
    or (
        absolute_contract
        and (
            manifest.get("expert_reference_used") is not False
            or int(target_leakage_audit.get("action_derived_state_fields", -1)) != 0
        )
    )
):
    raise SystemExit(
        "ERROR: formal PI0.5 training requires verified, leakage-free recovery data; "
        f"episodes={recovery_episodes}/{minimum_episodes}, "
        f"frames={nonzero_frames}/{minimum_frames}, summary={verified_summary!r}, "
        f"mode_episode_counts={mode_episode_counts}, "
        f"minimum_per_mode={minimum_per_mode}, "
        f"mode_conditioning={mode_conditioning_policy!r}, "
        f"lift_supervision={lift_residual_supervision!r}"
    )
print(
    json.dumps(
        {
            "pi05_dataset_gate": "passed",
            "action_contract": action_contract,
            "verified_recovery_episodes": recovery_episodes,
            "verified_recovery_episode_instances": len(recovery_entries),
            "replayed_training_episodes": replayed_training_episodes,
            "nonzero_contact_residual_frames": nonzero_frames,
            "nonzero_supervision_kind": (
                "base_command" if absolute_contract else "contact_residual"
            ),
            "mode_episode_counts": mode_episode_counts,
            "minimum_episodes_per_mode": minimum_per_mode,
            "missing_modes": missing_modes,
            "mode_conditioning_policy": mode_conditioning_policy,
            "task_language_policy": manifest.get("task_language_policy", "source_text"),
            "lift_residual_supervision": lift_residual_supervision,
            "target_leakage_audit": target_leakage_audit,
            "zero_seed_override": allow_zero_seed,
            "normalization_stats_policy": manifest.get("normalization_stats_policy"),
            "unsafe_normalization_dimensions": unsafe_stats,
            "policy_visual_modality": required_visual_modality,
            "policy_visual_keys": required_visual_keys,
        }
    )
)
PY

# Both contracts use observable contact/task state and an audited visual
# modality. Absolute v1 emits executable actions without an expert reference.
POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [80]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}, observation.images.overhead_depth_rgb: {type: VISUAL, shape: [3, 224, 224]}}'
if [[ "${WRIST_RGBD}" == "1" ]]; then
  POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [80]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}, observation.images.overhead_depth_rgb: {type: VISUAL, shape: [3, 224, 224]}, observation.images.left_wrist_rgb: {type: VISUAL, shape: [3, 224, 224]}, observation.images.left_wrist_depth_rgb: {type: VISUAL, shape: [3, 224, 224]}}'
fi
POLICY_OUTPUT_FEATURES='{action: {type: ACTION, shape: [14]}}'
JOB_NAME=mobile-bimanual-pi05-rgbd-residual14-lora-rocm
if [[ "${ACTION_CONTRACT}" == "absolute_v1" ]]; then
  POLICY_OUTPUT_FEATURES='{action: {type: ACTION, shape: [23]}}'
  JOB_NAME=mobile-bimanual-pi05-rgbd-absolute23-lora-rocm
fi
TRAIN_ENTRY=(lerobot-train)
if [[ "${MODE_LOSS_WEIGHT}" != "1" && "${MODE_LOSS_WEIGHT}" != "1.0" ]] || \
  [[ "${MODE_CE_WEIGHT}" != "0" && "${MODE_CE_WEIGHT}" != "0.0" ]] || \
  [[ "${STATE_TOKEN}" == "1" ]] || [[ "${MODE_HEAD}" == "1" ]] || \
  [[ "${MODE_HEAD_CE_WEIGHT}" != "0" && "${MODE_HEAD_CE_WEIGHT}" != "0.0" ]] || \
  [[ -n "${MODE_HEAD_CLASS_WEIGHTS}" ]] || \
  [[ -n "${STAGE_LOSS_WEIGHTS}" ]] || \
  [[ "${ACTION_CONTRACT}" == "absolute_v1" ]] || \
  [[ "${FULL_ACTION_PROJECTIONS}" == "1" ]]; then
  TRAIN_ENTRY=(python "${ROOT_DIR}/scripts/train_mobile_pi05_weighted_entry.py")
fi

write_training_contract() {
  local contract_output_dir="${1:-${OUTPUT_DIR}}"
  architecture_args=()
  if [[ "${STATE_TOKEN}" == "1" ]]; then
    architecture_args+=(--state-token)
  fi
  if [[ "${MODE_HEAD}" == "1" ]]; then
    architecture_args+=(--mode-head --mode-head-pooling "${MODE_HEAD_POOLING}")
  fi
  if [[ -n "${MODE_HEAD_CLASS_WEIGHTS}" ]]; then
    architecture_args+=(--mode-head-class-weights "${MODE_HEAD_CLASS_WEIGHTS}")
  fi
  if [[ -n "${STAGE_LOSS_WEIGHTS}" ]]; then
    architecture_args+=(--stage-loss-weights "${STAGE_LOSS_WEIGHTS}")
  fi
  if [[ "${FULL_ACTION_PROJECTIONS}" == "1" ]]; then
    architecture_args+=(--full-action-projections)
  fi
  python scripts/write_mobile_pi05_training_contract.py \
    --dataset-root "${DATASET_ROOT}" \
    --output-dir "${contract_output_dir}" \
    --base-model "${BASE_MODEL}" \
    --base-revision "${BASE_REVISION}" \
    --chunk-size "${CHUNK_SIZE}" \
    --n-action-steps "${N_ACTION_STEPS}" \
    "${architecture_args[@]}"
}

if [[ -n "${RESUME_CONFIG}" ]]; then
  test -f "${RESUME_CONFIG}" || {
    echo "ERROR: PI0.5 resume config not found: ${RESUME_CONFIG}" >&2
    exit 5
  }
  write_training_contract
  resume_scheduler_args=()
  if [[ -n "${RESUME_DECAY_STEPS}" ]]; then
    resume_scheduler_args+=(--scheduler.num_decay_steps "${RESUME_DECAY_STEPS}")
  fi
  if [[ -n "${RESUME_WARMUP_STEPS}" ]]; then
    resume_scheduler_args+=(--scheduler.num_warmup_steps "${RESUME_WARMUP_STEPS}")
  fi
  "${TRAIN_ENTRY[@]}" \
    --config_path="${RESUME_CONFIG}" \
    --resume true \
    --steps "${STEPS}" \
    --save_freq "${SAVE_FREQ}" \
    "${resume_scheduler_args[@]}" \
    --wandb.enable false
  exit 0
fi

# LeRobot rejects a new run when output_dir already exists. Stage the immutable
# contract beside the run, then install it as soon as the trainer creates the
# directory and before any checkpoint can be written.
if [[ -e "${OUTPUT_DIR}" ]]; then
  echo "ERROR: new PI0.5 output already exists: ${OUTPUT_DIR}" >&2
  exit 6
fi
contract_staging_dir="$(mktemp -d "${OUTPUT_DIR}.contract-staging.XXXXXX")"
write_training_contract "${contract_staging_dir}"

"${TRAIN_ENTRY[@]}" \
  --dataset.repo_id local/mobile-bimanual-parcel-expert \
  --dataset.root "${DATASET_ROOT}" \
  --dataset.image_transforms.enable false \
  --policy.type pi05 \
  --policy.pretrained_path "${BASE_MODEL}" \
  --policy.pretrained_revision "${BASE_REVISION}" \
  --policy.device cuda \
  --policy.dtype bfloat16 \
  --policy.use_amp true \
  --policy.push_to_hub false \
  --policy.input_features "${POLICY_INPUT_FEATURES}" \
  --policy.output_features "${POLICY_OUTPUT_FEATURES}" \
  --policy.max_state_dim 96 \
  --policy.max_action_dim 32 \
  --policy.chunk_size "${CHUNK_SIZE}" \
  --policy.n_action_steps "${N_ACTION_STEPS}" \
  --policy.gradient_checkpointing true \
  --policy.freeze_vision_encoder true \
  --peft.method_type LORA \
  --peft.r "${LORA_R}" \
  --peft.lora_alpha "${LORA_ALPHA}" \
  --output_dir "${OUTPUT_DIR}" \
  --job_name "${JOB_NAME}" \
  --batch_size "${BATCH_SIZE}" \
  --num_workers "${NUM_WORKERS}" \
  --steps "${STEPS}" \
  --seed 11 \
  --log_freq 1 \
  --save_checkpoint true \
  --save_freq "${SAVE_FREQ}" \
  --wandb.enable false \
  --env_eval_freq 0 \
  --eval_steps 0 &
training_pid=$!

while [[ ! -d "${OUTPUT_DIR}" ]] && kill -0 "${training_pid}" 2>/dev/null; do
  sleep 0.1
done
if [[ -d "${OUTPUT_DIR}" ]]; then
  contract_tmp="${OUTPUT_DIR}/.PI05_TRAINING_CONTRACT.json.tmp.$$"
  mv "${contract_staging_dir}/PI05_TRAINING_CONTRACT.json" "${contract_tmp}"
  mv "${contract_tmp}" "${OUTPUT_DIR}/PI05_TRAINING_CONTRACT.json"
  rmdir "${contract_staging_dir}"
  echo "training_contract=installed_before_first_checkpoint"
else
  echo "ERROR: trainer exited before creating output_dir; staged contract preserved at ${contract_staging_dir}" >&2
fi

set +e
wait "${training_pid}"
training_status=$?
set -e
exit "${training_status}"
