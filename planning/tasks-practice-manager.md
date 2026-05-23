# Practice Manager - Task List

## Completed
- [x] Extract shared `core` package from desktop-only code
- [x] Keep desktop runtime working on shared core modules
- [x] Add FastAPI backend for library, status, practice, and assets
- [x] Add browser UI for library browsing and practice sessions
- [x] Add recall mode to web practice flow
- [x] Add optional HTTP Basic Auth
- [x] Add deployment documentation and service assets
- [x] Standardize launch/test/environment helper scripts

## In Progress / Near-Term
- [x] Repair shared development environment so tests can run again
- [x] Run full automated suite after environment repair
- [x] Smoke-test desktop read/init flow headlessly against configured real library
- [x] Smoke-test web read/static/library/status/asset flow against configured real library
- [x] Smoke-test write flows with explicit backup/restore: start session, success/fail, reset part
- [x] Add focused web/API tests for library/status/assets/practice flow
- [x] Refresh README, operations docs, planning status, and web API comments
- [x] Implement automatic missing-item detection and surface set-level missing counts
- [x] Remove unused `gui/widgets.py` placeholder
- [x] Clarify deployment/auth posture for internet-facing use
- [ ] Decide merge readiness for `feature/operational-legibility-web-runtime`

## Recommended Next Slice
- [x] Add API tests for `/api/library`, `/api/status`, `/api/practice`, and `/api/assets`
- [x] Implement automatic missing-item detection
- [x] Clarify deployment/auth posture for real-world use

## Later
- [ ] Revisit deployment options beyond VM + rclone if serverless hosting becomes desirable

## Blockers
- [x] Shared environment pointed to a non-executable Python binary, blocking the standardized test runner

## Notes
- The previous planning files described a different project, Script Manager, and were replaced on 2026-05-17 so the planning layer matches this repository.
- Shared environment repair completed on 2026-05-17: Python symlink repointed, corrupted PySide6/shiboken install cleaned and reinstalled, `bash scripts/env/run_tests.sh` now passes.
- 2026-05-21 verification: configured library resolves to Google Drive OTPD Scores; discovery sees 98 sets and 264 tracked items. Standard tests pass (`61 passed, 1 skipped`). Web read smoke passes for `/`, `/api/status`, `/api/library`, `/api/library/sets/{set_id}`, and `/api/assets/pdf`. Reversible web write smoke passes for `/api/practice/start`, `/api/practice/success`, `/api/practice/fail`, and `/api/practice/reset`; original `practice_status.json` bytes were restored and smoke-generated backup was removed. Desktop headless initialization passes.
- 2026-05-21 regression update: added isolated `tests/test_web_api.py`; full suite now passes with `64 passed, 1 skipped`.
- 2026-05-23 documentation/comment pass: README and operations docs now describe current verification baseline; web API tests and path/session helpers include clarifying comments/docstrings.
- 2026-05-23 hardening pass: missing-item reconciliation implemented and covered; unused `gui/widgets.py` removed; Basic Auth compare hardened and deployment auth docs clarified. Full suite now passes with `68 passed, 1 skipped`.
