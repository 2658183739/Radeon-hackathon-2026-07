#!/usr/bin/env bash
# Run the hidden-input three-mode screen for one or more PI0.5 checkpoints.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ROOT="${1:?usage: $0 RUN_ROOT DATASET_ROOT OUTPUT_DIR RUN_NAME [STEP ...]}"
DATASET_ROOT="${2:?usage: $0 RUN_ROOT DATASET_ROOT OUTPUT_DIR RUN_NAME [STEP ...]}"
OUTPUT_DIR="${3:?usage: $0 RUN_ROOT DATASET_ROOT OUTPUT_DIR RUN_NAME [STEP ...]}"
RUN_NAME="${4:?usage: $0 RUN_ROOT DATASET_ROOT OUTPUT_DIR RUN_NAME [STEP ...]}"
shift 4
if [[ "$#" -eq 0 ]]; then
  STEPS=(1000 2000 3000)
else
  STEPS=("$@")
fi

export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export TOKENIZERS_PARALLELISM=false
REQUIRE_ACTION_FIDELITY="${MOBILE_PI05_REQUIRE_ACTION_FIDELITY:-0}"
REQUIRE_FULL_ACTION_PROJECTIONS="${MOBILE_PI05_REQUIRE_FULL_ACTION_PROJECTIONS:-0}"
EXPECTED_STAGE_LOSS_WEIGHTS="${MOBILE_PI05_EXPECTED_STAGE_LOSS_WEIGHTS:-}"
if [[ "${REQUIRE_ACTION_FIDELITY}" != "0" && "${REQUIRE_ACTION_FIDELITY}" != "1" ]]; then
  echo "ERROR: MOBILE_PI05_REQUIRE_ACTION_FIDELITY must be 0 or 1" >&2
  exit 2
fi
if [[ "${REQUIRE_FULL_ACTION_PROJECTIONS}" != "0" && "${REQUIRE_FULL_ACTION_PROJECTIONS}" != "1" ]]; then
  echo "ERROR: MOBILE_PI05_REQUIRE_FULL_ACTION_PROJECTIONS must be 0 or 1" >&2
  exit 2
fi

cd "${ROOT_DIR}"
source scripts/activate_radeon_env.sh
mkdir -p "${OUTPUT_DIR}"

status=0
for step in "${STEPS[@]}"; do
  printf -v checkpoint_step "%06d" "${step}"
  checkpoint="${RUN_ROOT}/checkpoints/${checkpoint_step}/pretrained_model"
  probe="${OUTPUT_DIR}/${RUN_NAME}-step${step}-six-observation-probes.json"
  screen="${OUTPUT_DIR}/${RUN_NAME}-step${step}-six-observation-screen.json"
  audit="${OUTPUT_DIR}/${RUN_NAME}-step${step}-checkpoint-audit.json"
  log="${OUTPUT_DIR}/${RUN_NAME}-step${step}-six-observation-probes.log"

  if [[ ! -f "${checkpoint}/adapter_model.safetensors" ]]; then
    echo "ERROR: missing PI0.5 adapter: ${checkpoint}" >&2
    status=3
    continue
  fi

  audit_args=()
  if [[ "${REQUIRE_FULL_ACTION_PROJECTIONS}" == "1" ]]; then
    audit_args+=(--require-full-action-projections)
  fi
  if [[ -n "${EXPECTED_STAGE_LOSS_WEIGHTS}" ]]; then
    audit_args+=(--expected-stage-loss-weights "${EXPECTED_STAGE_LOSS_WEIGHTS}")
  fi
  if ! python scripts/audit_mobile_pi05_checkpoint.py \
    "${checkpoint}" \
    --require-contract \
    "${audit_args[@]}" \
    --output "${audit}"; then
    echo "ERROR: PI0.5 checkpoint audit failed: ${checkpoint}" >&2
    status=4
    continue
  fi

  python scripts/probe_mobile_pi05_checkpoint_rocm.py \
    "${checkpoint}" \
    "${DATASET_ROOT}" \
    --index 0 \
    --index 644 \
    --index 1286 \
    --index 3636 \
    --index 4699 \
    --index 5285 \
    --samples 3 \
    --output "${probe}" 2>&1 | tee "${log}"

  summary_args=()
  if [[ "${REQUIRE_ACTION_FIDELITY}" == "1" ]]; then
    summary_args+=(--require-action-fidelity)
  fi
  if ! python scripts/summarize_mobile_pi05_mode_screen.py \
    --probe "${probe}" \
    --output "${screen}" \
    "${summary_args[@]}" \
    --min-probes-per-mode 2; then
    status=2
  fi
done

exit "${status}"
