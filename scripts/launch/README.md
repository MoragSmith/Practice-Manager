# Launch Scripts

This directory contains canonical launcher wrappers for the desktop app.

- `launch_practice_manager.sh` - macOS/Linux shell launcher
- `Launch_Practice_Manager.command` - macOS double-click launcher
- `launch_practice_manager.bat` - Windows launcher

All launchers run `run.py` from project root using the shared environment at:

`../shared-dev-env` (relative to the project root directory).

Legacy launcher files remain at repo root as compatibility wrappers.
