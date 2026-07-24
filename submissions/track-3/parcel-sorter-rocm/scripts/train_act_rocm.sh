#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/radeon-dataset/expert/lerobot_dataset}"
OUTPUT_DIR="${2:-${ROOT_DIR}/outputs/train/act-rocm}"
STEPS="${ACT_STEPS:-100000}"
BATCH_SIZE="${ACT_BATCH_SIZE:-32}"
NUM_WORKERS="${ACT_NUM_WORKERS:-4}"
SAVE_FREQ="${ACT_SAVE_FREQ:-20000}"
SAVE_CHECKPOINT="${ACT_SAVE_CHECKPOINT:-true}"
LOG_FREQ="${ACT_LOG_FREQ:-100}"
USE_AMP="${ACT_USE_AMP:-false}"
IMAGE_TRANSFORMS="${ACT_IMAGE_TRANSFORMS:-false}"
PRETRAINED_BACKBONE="${ACT_PRETRAINED_BACKBONE:-imagenet}"
EVAL_SPLIT="${ACT_EVAL_SPLIT:-0.1}"
EVAL_STEPS="${ACT_EVAL_STEPS:-1000}"

export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

cd "${ROOT_DIR}"
source scripts/activate_radeon_env.sh
bash scripts/preflight_radeon.sh

if [[ ! -f "${DATASET_ROOT}/meta/info.json" ]]; then
  echo "ERROR: LeRobotDataset not found: ${DATASET_ROOT}" >&2
  exit 2
fi
if ! command -v lerobot-train >/dev/null 2>&1; then
  echo "ERROR: LeRobot training dependencies are missing." >&2
  echo "Run: INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh" >&2
  exit 3
fi

# Do not expose observation.privileged_state (parcel ground truth) to the policy.
# ACT uses RGB plus proprioception; metric depth remains available for later fusion models.
POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [20]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}}'
TRAIN_ARGS=(
  --dataset.repo_id local/parcel-sorter-expert
  --dataset.root "${DATASET_ROOT}"
  --dataset.depth_output_unit m
  --dataset.eval_split "${EVAL_SPLIT}"
  --dataset.image_transforms.enable "${IMAGE_TRANSFORMS}"
  --policy.type act
  --policy.device cuda
  --policy.push_to_hub false
  --policy.use_amp "${USE_AMP}"
  --policy.input_features "${POLICY_INPUT_FEATURES}"
  --policy.chunk_size 30
  --policy.n_action_steps 10
  --output_dir "${OUTPUT_DIR}"
  --job_name parcel-sorter-act-rocm
  --batch_size "${BATCH_SIZE}"
  --num_workers "${NUM_WORKERS}"
  --steps "${STEPS}"
  --log_freq "${LOG_FREQ}"
  --save_checkpoint "${SAVE_CHECKPOINT}"
  --save_freq "${SAVE_FREQ}"
  --wandb.enable false
  --env_eval_freq 0
  --eval_steps "${EVAL_STEPS}"
)

if [[ "${NUM_WORKERS}" == "0" ]]; then
  TRAIN_ARGS+=(--persistent_workers false)
fi
if [[ "${PRETRAINED_BACKBONE}" == "none" ]]; then
  TRAIN_ARGS+=(--policy.pretrained_backbone_weights null)
fi

lerobot-train "${TRAIN_ARGS[@]}"
