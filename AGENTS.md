# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Practice Manager is a PySide6 (Qt 6) desktop GUI application for tracking musical practice mastery. It is a single Python package (`src/practice_manager/`) with no database — all data is stored in JSON files on disk.

### Running tests

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -v
```

All unit tests use `tmp_path` fixtures and run without external services. The integration test (`tests/integration/test_ensemble_parts.py`) requires `ENSEMBLE_USERNAME`/`ENSEMBLE_PASSWORD` env vars and a configured library root; it is auto-skipped otherwise.

See `README.md` for full test descriptions.

### Running the application

The app requires a configured OTPD Scores library. To run with a mock library:

```bash
mkdir -p /tmp/otpd-scores/"Section 1 - Competition"/"Competition 01 - Highland Laddie"/Parts
mkdir -p /tmp/otpd-scores/"#Script Resources/data"
echo '{"library_root": "/tmp/otpd-scores"}' > tracker-config.json
python3 run.py
```

Clean up `tracker-config.json` after testing (it is gitignored).

### Qt system dependencies

PySide6 requires these system packages on headless Linux: `libegl1`, `libgl1`, `libopengl0`, `libxkbcommon0`, `libfontconfig1`, `libdbus-1-3`, `libxcb-cursor0`, `libxkbcommon-x11-0`, `libxcb-icccm4`, `libxcb-keysyms1`, `libxcb-xkb1`. These are pre-installed in the VM snapshot.

### Gotchas

- `python` is not on PATH; always use `python3`.
- pip installs to `~/.local/bin` by default; ensure `PATH` includes `$HOME/.local/bin`.
- Playwright Chromium must be installed separately (`playwright install chromium`) after pip install.
- The `Download Parts` feature requires Ensemble credentials (`ENSEMBLE_USERNAME`/`ENSEMBLE_PASSWORD`).
