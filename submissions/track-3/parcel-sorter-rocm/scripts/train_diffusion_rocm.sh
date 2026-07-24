#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/radeon-dataset/expert/lerobot_dataset}"
OUTPUT_DIR="${2:-${ROOT_DIR}/outputs/train/diffusion-rocm}"
STEPS="${DIFFUSION_STEPS:-30000}"
BATCH_SIZE="${DIFFUSION_BATCH_SIZE:-32}"
NUM_WORKERS="${DIFFUSION_NUM_WORKERS:-4}"
SAVE_FREQ="${DIFFUSION_SAVE_FREQ:-5000}"
USE_AMP="${DIFFUSION_USE_AMP:-true}"
IMAGE_TRANSFORMS="${DIFFUSION_IMAGE_TRANSFORMS:-false}"
EVAL_SPLIT="${DIFFUSION_EVAL_SPLIT:-0.1}"
EVAL_STEPS="${DIFFUSION_EVAL_STEPS:-1000}"

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
  echo "ERROR: LeRobot is missing. Run INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh" >&2
  exit 3
fi
if ! python -c "import diffusers" >/dev/null 2>&1; then
  echo "ERROR: LeRobot Diffusion dependencies are missing." >&2
  echo "Run: INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh" >&2
  exit 4
fi

# Keep ground-truth parcel pose out of policy inputs. The policy sees RGB,
# proprioception, target position, and contact force through observation.state.
POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [20]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}}'

TRAIN_ARGS=(
  --dataset.repo_id local/parcel-sorter-expert
  --dataset.root "${DATASET_ROOT}"
  --dataset.depth_output_unit m
  --dataset.eval_split "${EVAL_SPLIT}"
  --dataset.image_transforms.enable "${IMAGE_TRANSFORMS}"
  --policy.type diffusion
  --policy.device cuda
  --policy.push_to_hub false
  --policy.use_amp "${USE_AMP}"
  --policy.input_features "${POLICY_INPUT_FEATURES}"
  --policy.horizon 32
  --policy.n_action_steps 8
  --policy.num_inference_steps 10
  --output_dir "${OUTPUT_DIR}"
  --job_name parcel-sorter-diffusion-rocm
  --batch_size "${BATCH_SIZE}"
  --num_workers "${NUM_WORKERS}"
  --steps "${STEPS}"
  --log_freq 100
  --save_checkpoint true
  --save_freq "${SAVE_FREQ}"
  --wandb.enable false
  --env_eval_freq 0
  --eval_steps "${EVAL_STEPS}"
)

if [[ "${NUM_WORKERS}" == "0" ]]; then
  TRAIN_ARGS+=(--persistent_workers false)
fi
if [[ "${DIFFUSION_PRETRAINED_BACKBONE:-imagenet}" == "none" ]]; then
  TRAIN_ARGS+=(--policy.pretrained_backbone_weights null)
fi

lerobot-train "${TRAIN_ARGS[@]}"
