#!/bin/bash
# Run Practice Manager tests with clear environment diagnostics.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SHARED_PYTHON="$PROJECT_ROOT/../shared-dev-env/bin/python"

cd "$PROJECT_ROOT"

if [ ! -x "$SHARED_PYTHON" ]; then
  echo "Shared environment python is not executable: $SHARED_PYTHON" >&2
  echo "Run: bash scripts/env/check_env.sh" >&2
  echo "Then follow: docs/ENV_REPAIR_CHECKLIST.md" >&2
  exit 1
fi

exec "$SHARED_PYTHON" -m pytest tests/ -v
