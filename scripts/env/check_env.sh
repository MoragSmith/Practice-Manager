#!/bin/bash
# Environment diagnostics for Practice Manager launch/test tooling.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SHARED_ENV="$PROJECT_ROOT/../shared-dev-env"
PYTHON_BIN="$SHARED_ENV/bin/python"
PYTEST_BIN="$SHARED_ENV/bin/pytest"
ACTIVATE_SCRIPT="$PROJECT_ROOT/../activate_shared_dev.sh"

echo "Practice Manager environment diagnostics"
echo "project_root: $PROJECT_ROOT"
echo "shared_env:   $SHARED_ENV"
echo

if [ -x "$PYTHON_BIN" ]; then
  echo "[ok] shared python exists: $PYTHON_BIN"
  "$PYTHON_BIN" --version || true
else
  echo "[warn] shared python missing/not executable: $PYTHON_BIN"
fi

if [ -x "$PYTEST_BIN" ]; then
  echo "[ok] shared pytest exists: $PYTEST_BIN"
else
  echo "[warn] shared pytest missing/not executable: $PYTEST_BIN"
fi

if [ -f "$ACTIVATE_SCRIPT" ]; then
  echo "[ok] activate script found: $ACTIVATE_SCRIPT"
else
  echo "[warn] activate script not found: $ACTIVATE_SCRIPT"
fi

echo
echo "PATH python resolution:"
command -v python || true
command -v python3 || true
command -v pytest || true
