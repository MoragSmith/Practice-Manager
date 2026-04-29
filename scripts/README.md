# Scripts Overview

This directory is an operational boundary for helper scripts.

## Subdirectories

- `launch/` - canonical app launch wrappers (desktop-focused)
- `env/` - environment diagnostics and validation helpers

## Operator Quickstart

From project root:

1. Check environment health:
   ```bash
   bash scripts/env/check_env.sh
   ```
2. Run tests through the standardized wrapper:
   ```bash
   bash scripts/env/run_tests.sh
   ```
3. Launch desktop app (wrapper path):
   ```bash
   bash scripts/launch/launch_practice_manager.sh
   ```

## Compatibility

- Root launcher files (`launch_practice_manager.sh`, `Launch_Practice_Manager.command`, `launch_practice_manager.bat`) remain compatibility wrappers.
- Canonical launcher implementations live under `scripts/launch/`.
