# Operations Guide

This document defines operational boundaries for the `Practice Manager` repository.

## What This Repo Contains

- Source code: `src/`
- Tests: `tests/`
- Human-facing documentation: `docs/`
- Deployment assets: `deploy/`
- Entrypoints: `run.py` (desktop), `run_web.py` (web)

## Runtime State Boundaries

Runtime data for practice tracking does not live in this repository.

- Practice status is stored in the OTPD Scores library:
  `OTPD Scores/#Script Resources/data/practice_status.json`
- Data directory is resolved by config discovery in `src/practice_manager/core/config.py`

## Local Machine Config

- Use `tracker-config.example.json` as a template
- Create `tracker-config.json` locally for machine-specific paths
- `tracker-config.json` is gitignored and should remain local

## Safe to Ignore (Generated/Transient)

These are local artifacts and are safe to ignore in version control:

- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `*.egg-info/`
- root containment zones if created: `logs/`, `tmp/`, `runtime/`, `generated/`, `backup/`
- common residue patterns: `*.log`, `*.tmp`, `*.bak`, `*.old`

## Launch and Operation

- Desktop app: `python run.py`
- Web app: `python run_web.py`
- Canonical launch wrappers: `scripts/launch/`
- Root launcher files are compatibility wrappers that forward to `scripts/launch/`
- Environment diagnostics script: `scripts/env/check_env.sh`
- Standardized test runner: `scripts/env/run_tests.sh`
- Script boundary map: `scripts/README.md`
- Shared environment repair steps: `docs/ENV_REPAIR_CHECKLIST.md`

## Maintenance Rules

- Keep active source under `src/`
- Keep docs under `docs/`
- Keep deployment assets under `deploy/`
- Avoid adding runtime output, logs, caches, or temporary files to the repo root
