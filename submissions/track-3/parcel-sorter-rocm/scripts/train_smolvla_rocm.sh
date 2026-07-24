#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/radeon-dataset/expert/lerobot_dataset}"
OUTPUT_DIR="${2:-${ROOT_DIR}/outputs/train/smolvla-rocm}"
POLICY_PATH="${SMOLVLA_POLICY_PATH:-}"
STEPS="${SMOLVLA_STEPS:-4000}"
BATCH_SIZE="${SMOLVLA_BATCH_SIZE:-4}"
NUM_WORKERS="${SMOLVLA_NUM_WORKERS:-4}"
SAVE_FREQ="${SMOLVLA_SAVE_FREQ:-1000}"
FREEZE_VISION="${SMOLVLA_FREEZE_VISION_ENCODER:-true}"
TRAIN_EXPERT_ONLY="${SMOLVLA_TRAIN_EXPERT_ONLY:-true}"
EVAL_SPLIT="${SMOLVLA_EVAL_SPLIT:-0.1}"
EVAL_STEPS="${SMOLVLA_EVAL_STEPS:-500}"

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
if ! python -c "import transformers, num2words" >/dev/null 2>&1; then
  echo "ERROR: LeRobot SmolVLA dependencies are missing." >&2
  echo "Run: INSTALL_LEROBOT=1 bash scripts/bootstrap_radeon.sh" >&2
  exit 4
fi
if [[ -z "${POLICY_PATH}" ]]; then
  echo "ERROR: SMOLVLA_POLICY_PATH is required." >&2
  echo "Point it to a local open SmolVLA checkpoint, or to lerobot/smolvla_base when Hugging Face is reachable." >&2
  exit 5
fi
if [[ "${POLICY_PATH}" == */* && ! -e "${POLICY_PATH}" ]]; then
  echo "INFO: ${POLICY_PATH} is not local; LeRobot will try to download it." >&2
fi

# SmolVLA receives the natural-language task stored in every dataset frame, RGB,
# and the non-privileged 20-D state. The 7-D simulator parcel pose is excluded.
POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [20]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}}'
POLICY_OUTPUT_FEATURES='{action: {type: ACTION, shape: [8]}}'
EXTRA_ARGS=()
if [[ -n "${SMOLVLA_EXTRA_ARGS:-}" ]]; then
  read -r -a EXTRA_ARGS <<< "${SMOLVLA_EXTRA_ARGS}"
fi

lerobot-train \
  --dataset.repo_id local/parcel-sorter-expert \
  --dataset.root "${DATASET_ROOT}" \
  --dataset.depth_output_unit m \
  --dataset.eval_split "${EVAL_SPLIT}" \
  --dataset.image_transforms.enable false \
  --policy.path "${POLICY_PATH}" \
  --policy.device cuda \
  --policy.push_to_hub false \
  --policy.use_amp true \
  --policy.input_features "${POLICY_INPUT_FEATURES}" \
  --policy.output_features "${POLICY_OUTPUT_FEATURES}" \
  --policy.freeze_vision_encoder "${FREEZE_VISION}" \
  --policy.train_expert_only "${TRAIN_EXPERT_ONLY}" \
  --policy.chunk_size 30 \
  --policy.n_action_steps 10 \
  --output_dir "${OUTPUT_DIR}" \
  --job_name parcel-sorter-smolvla-rocm \
  --batch_size "${BATCH_SIZE}" \
  --num_workers "${NUM_WORKERS}" \
  --steps "${STEPS}" \
  --log_freq 50 \
  --save_checkpoint true \
  --save_freq "${SAVE_FREQ}" \
  --wandb.enable false \
  --env_eval_freq 0 \
  --eval_steps "${EVAL_STEPS}" \
  "${EXTRA_ARGS[@]}"
