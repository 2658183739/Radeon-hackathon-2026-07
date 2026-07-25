#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_PATH="${1:-${ROOT_DIR}/configs/catalog_v2.toml}"
OUTPUT_ROOT="${2:-${ROOT_DIR}/outputs/radeon-reset-ab-v1}"
EPISODES="${RESET_AB_EPISODES:-20}"
PROFILE="large_narrow_carton"

export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

cd "${ROOT_DIR}"
source scripts/activate_radeon_env.sh
bash scripts/preflight_radeon.sh

if [[ -e "${OUTPUT_ROOT}" ]]; then
  echo "ERROR: output root already exists; choose a new path: ${OUTPUT_ROOT}" >&2
  exit 2
fi
if [[ ! -f "${CONFIG_PATH}" ]]; then
  echo "ERROR: config not found: ${CONFIG_PATH}" >&2
  exit 3
fi
if [[ "${EPISODES}" != "20" ]]; then
  echo "ERROR: the audited reset-pose protocol requires exactly 20 episodes" >&2
  exit 4
fi

BASELINE_ROOT="${OUTPUT_ROOT}/baseline"
CANDIDATE_ROOT="${OUTPUT_ROOT}/candidate-c"
CANDIDATE_QPOS=(-1.0124 1.0 1.4 -1.6878 -1.5799 1.7757 1.4602 0.04 0.04)

python scripts/run_expert.py \
  --config "${CONFIG_PATH}" \
  --backend rocm \
  --episodes "${EPISODES}" \
  --start-episode 0 \
  --profile "${PROFILE}" \
  --output "${BASELINE_ROOT}"

python scripts/run_expert.py \
  --config "${CONFIG_PATH}" \
  --backend rocm \
  --episodes "${EPISODES}" \
  --start-episode 0 \
  --profile "${PROFILE}" \
  --reset-qpos "${CANDIDATE_QPOS[@]}" \
  --output "${CANDIDATE_ROOT}"

python scripts/compare_expert_runs.py \
  --baseline "${BASELINE_ROOT}/expert/summary.json" \
  --candidate "${CANDIDATE_ROOT}/expert/summary.json" \
  --output "${OUTPUT_ROOT}/comparison.json"

sha256sum \
  "${BASELINE_ROOT}/expert/summary.json" \
  "${CANDIDATE_ROOT}/expert/summary.json" \
  "${OUTPUT_ROOT}/comparison.json" > "${OUTPUT_ROOT}/SHA256SUMS"

echo "Reset-pose A/B completed: ${OUTPUT_ROOT}"
