#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:-${ROOT_DIR}/outputs/goal-marker-primitive-v2}"
OUTPUT_DIR="${2:-/root/pi05-runs/mobile-pi05-goal-marker-lora}"
DEFAULT_BASE_MODEL=lerobot/pi05_base
if [[ -f /root/pi05-assets/pi05-base-local/model.safetensors ]]; then
  DEFAULT_BASE_MODEL=/root/pi05-assets/pi05-base-local
fi
BASE_MODEL="${PI05_BASE_MODEL:-${DEFAULT_BASE_MODEL}}"
BASE_REVISION="${PI05_BASE_REVISION:-7de663972b7817d2c4cf2d84c821153dfea772e9}"
STEPS="${MOBILE_PI05_STEPS:-10}"
BATCH_SIZE="${MOBILE_PI05_BATCH_SIZE:-1}"
NUM_WORKERS="${MOBILE_PI05_NUM_WORKERS:-0}"
LORA_R="${MOBILE_PI05_LORA_R:-8}"
LORA_ALPHA="${MOBILE_PI05_LORA_ALPHA:-16}"

export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export HF_HOME="${HF_HOME:-/root/.cache/huggingface}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HUB_DISABLE_XET="${HF_HUB_DISABLE_XET:-1}"
export TOKENIZERS_PARALLELISM=false

cd "${ROOT_DIR}"
source scripts/activate_radeon_env.sh
bash scripts/preflight_radeon.sh
bash scripts/cleanup_old_checkpoints_rocm.sh
python -c "import peft" 2>/dev/null || {
  echo "ERROR: PI0.5 LoRA requires peft>=0.18.0,<1.0.0" >&2
  exit 3
}

test -f "${DATASET_ROOT}/meta/info.json" || {
  echo "ERROR: PI0.5 LeRobotDataset not found: ${DATASET_ROOT}" >&2
  exit 4
}

# The current primitive dataset contains a 43-D mobile state, RGB observation,
# and a 20-D action (19 controls plus primitive progress). The base checkpoint
# is pinned so the experiment remains reproducible even if the Hub tag moves.
POLICY_INPUT_FEATURES='{observation.state: {type: STATE, shape: [43]}, observation.images.overhead_rgb: {type: VISUAL, shape: [3, 224, 224]}}'
POLICY_OUTPUT_FEATURES='{action: {type: ACTION, shape: [20]}}'

lerobot-train \
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
  --policy.max_state_dim 48 \
  --policy.max_action_dim 32 \
  --policy.chunk_size 30 \
  --policy.n_action_steps 10 \
  --policy.gradient_checkpointing true \
  --policy.freeze_vision_encoder true \
  --peft.method_type LORA \
  --peft.r "${LORA_R}" \
  --peft.lora_alpha "${LORA_ALPHA}" \
  --output_dir "${OUTPUT_DIR}" \
  --job_name mobile-bimanual-pi05-rgb-action20-lora-rocm \
  --batch_size "${BATCH_SIZE}" \
  --num_workers "${NUM_WORKERS}" \
  --steps "${STEPS}" \
  --seed 11 \
  --log_freq 1 \
  --save_checkpoint true \
  --save_freq "${STEPS}" \
  --wandb.enable false \
  --env_eval_freq 0 \
  --eval_steps 0
