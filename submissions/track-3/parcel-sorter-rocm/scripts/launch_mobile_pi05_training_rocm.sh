#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_ROOT="${1:?dataset root is required}"
OUTPUT_DIR="${2:?output directory is required}"
LOG_PATH="${3:?log path is required}"
STEPS="${4:-3000}"

if [[ ! -f "${DATASET_ROOT}/meta/info.json" ]]; then
  echo "ERROR: dataset not found: ${DATASET_ROOT}" >&2
  exit 2
fi
if [[ -e "${OUTPUT_DIR}" ]]; then
  echo "ERROR: output directory already exists: ${OUTPUT_DIR}" >&2
  exit 3
fi
if [[ -e "${LOG_PATH}" || -e "${LOG_PATH}.pid" ]]; then
  echo "ERROR: log or PID file already exists: ${LOG_PATH}" >&2
  exit 4
fi

mkdir -p "$(dirname "${LOG_PATH}")"
nohup env MOBILE_PI05_STEPS="${STEPS}" \
  PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
  bash "${ROOT_DIR}/scripts/train_mobile_pi05_rocm.sh" \
  "${DATASET_ROOT}" "${OUTPUT_DIR}" \
  >"${LOG_PATH}" 2>&1 </dev/null &
pid=$!
printf '%s\n' "${pid}" >"${LOG_PATH}.pid"

sleep 1
if ! kill -0 "${pid}" 2>/dev/null; then
  echo "ERROR: training process exited during launch" >&2
  tail -n 40 "${LOG_PATH}" >&2 || true
  exit 5
fi

printf '{"pid":%s,"steps":%s,"dataset":"%s","output":"%s","log":"%s"}\n' \
  "${pid}" "${STEPS}" "${DATASET_ROOT}" "${OUTPUT_DIR}" "${LOG_PATH}"
