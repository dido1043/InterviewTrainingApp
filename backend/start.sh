#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

if [[ -x "${VENV_PYTHON}" ]]; then
  exec "${VENV_PYTHON}" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
