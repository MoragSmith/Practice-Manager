#!/bin/bash
# Canonical desktop launcher for Practice Manager.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_BIN="$PROJECT_ROOT/../shared-dev-env/bin/python"
ACTIVATE_SCRIPT="$PROJECT_ROOT/../activate_shared_dev.sh"

cd "$PROJECT_ROOT"

if [ -x "$PYTHON_BIN" ]; then
  exec "$PYTHON_BIN" run.py
fi

if [ -f "$ACTIVATE_SCRIPT" ]; then
  # Fallback for cases where the venv executable path changed and needs reactivation.
  # shellcheck disable=SC1090
  source "$ACTIVATE_SCRIPT"
  if command -v python >/dev/null 2>&1; then
    exec python run.py
  fi
  if command -v python3 >/dev/null 2>&1; then
    exec python3 run.py
  fi
fi

echo "Unable to locate a working Python runtime for Practice Manager." >&2
echo "Checked: $PYTHON_BIN" >&2
echo "Optional activate script: $ACTIVATE_SCRIPT" >&2
echo "Run scripts/env/check_env.sh for diagnostics." >&2
exit 1
