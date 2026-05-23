#!/bin/bash
# Canonical macOS double-click launcher for Practice Manager.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/launch_practice_manager.sh"
