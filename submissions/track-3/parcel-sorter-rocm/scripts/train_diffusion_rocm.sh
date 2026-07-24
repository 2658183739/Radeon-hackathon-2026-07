#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/radeon-dataset/expert/lerobot_dataset}"
OUTPUT_DIR="${2:-${ROOT_DIR}/outputs/train/diffusion-rocm}"
STEPS="${DIFFUSION_STEPS:-30000}"
SEED="${DIFFUSION_SEED:-42}"
BATCH_SIZE="${DIFFUSION_BATCH_SIZE:-32}"
NUM_WORKERS="${DIFFUSION_NUM_WORKERS:-4}"
SAVE_FREQ="${DIFFUSION_SAVE_FREQ:-5000}"
USE_AMP="${DIFFUSION_USE_AMP:-true}"
IMAGE_TRANSFORMS="${DIFFUSION_IMAGE_TRANSFORMS:-false}"
EVAL_SPLIT="${DIFFUSION_EVAL_SPLIT:-0.1}"
EVAL_STEPS="${DIFFUSION_EVAL_STEPS:-1000}"
HORIZON="${DIFFUSION_HORIZON:-32}"
N_OBS_STEPS="${DIFFUSION_N_OBS_STEPS:-2}"
N_ACTION_STEPS="${DIFFUSION_N_ACTION_STEPS:-8}"
DOWN_DIMS_TEXT="${DIFFUSION_DOWN_DIMS:-512,1024,2048}"
INFERENCE_STEPS="${DIFFUSION_INFERENCE_STEPS:-10}"
NOISE_SCHEDULER="${DIFFUSION_NOISE_SCHEDULER:-DDPM}"
COMPILE_MODEL="${DIFFUSION_COMPILE_MODEL:-false}"

IFS=',' read -r -a DOWN_DIMS <<< "${DOWN_DIMS_TEXT}"
if [[ "${#DOWN_DIMS[@]}" -lt 1 ]]; then
  echo "ERROR: DIFFUSION_DOWN_DIMS must contain at least one comma-separated width" >&2
  exit 5
fi
downsample_factor=1
for _ in "${DOWN_DIMS[@]}"; do
  downsample_factor=$((downsample_factor * 2))
done
if (( HORIZON % downsample_factor != 0 )); then
  echo "ERROR: DIFFUSION_HORIZON=${HORIZON} is not divisible by ${downsample_factor} for ${DOWN_DIMS_TEXT}" >&2
  exit 6
fi

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
  --policy.horizon "${HORIZON}"
  --policy.n_obs_steps "${N_OBS_STEPS}"
  --policy.n_action_steps "${N_ACTION_STEPS}"
  --policy.down_dims "[${DOWN_DIMS_TEXT}]"
  --policy.num_inference_steps "${INFERENCE_STEPS}"
  --policy.noise_scheduler_type "${NOISE_SCHEDULER}"
  --policy.compile_model "${COMPILE_MODEL}"
  --seed "${SEED}"
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
