#!/bin/bash
# Backward-compatible wrapper. Canonical launcher lives in scripts/launch/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/scripts/launch/Launch_Practice_Manager.command"
