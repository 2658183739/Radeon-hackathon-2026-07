#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THIRD_PARTY_DIR="${ROOT_DIR}/third_party"
VENV_DIR="${ROOT_DIR}/.venv-cuda"

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
bash "${ROOT_DIR}/scripts/preflight_cuda.sh"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv --system-site-packages "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e "${THIRD_PARTY_DIR}/genesis-world"
python -m pip install -e "${ROOT_DIR}"
python "${ROOT_DIR}/scripts/smoke_genesis.py" --backend cuda --steps 80
python -m unittest discover -s "${ROOT_DIR}/tests" -v

if [[ "${INSTALL_LEROBOT:-0}" == "1" ]]; then
  python -m pip install -e "${THIRD_PARTY_DIR}/lerobot"
fi

echo "CUDA bootstrap completed. Run: bash scripts/run_pipeline_cuda.sh"
