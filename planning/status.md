# Status

- Reviewed for **`Practice Manager`**.
- **generated_at:** 2026-05-23
- **health:** green
- **headline:** Practice Manager core, desktop, and web runtime are implemented and merged to main. Local tests, web/API coverage, missing-item reconciliation, auth hardening, real-library smokes, desktop headless smoke, and local production-entrypoint auth smoke pass.

Suggested actions for IDEs: **`suggested-next-actions.md`** in this folder.

---

## Current state
- Track mastery of bass (and other instrument) scores for OTPD repertoire. Core, desktop, Ensemble, and web runtime code are present. Local automated verification, web/API regression coverage, missing-item detection, auth hardening, and real-library smokes pass.
- Phase: **merged**
- Health: **green**

## Local evidence
- Primary local brief: `README.md`
- Project description from local docs: Track mastery of bass (and other instrument) scores for OTPD repertoire. Content is organized by Sets ; practice and mastery apply to Tunes and Parts . Set an instrument (bass, snare, bagpipes, etc.) per set for PDF playback.
- Top-level contents: .git, .gitignore, .pytest_cache, Launch_Practice_Manager.command, README.md, deploy, docs, launch_practice_manager.bat
- Git branch: `main`
- Recent meaningful files: `tests/test_web_api.py`, `src/practice_manager/web/api/practice.py`, `src/practice_manager/web/api/assets.py`, `README.md`, `docs/OPERATIONS.md`
- Planning docs present: PRD `prd-practice-manager.md`, tasks `tasks-practice-manager.md`
- Current verification baseline: `68 passed, 1 skipped`

## Recommended next actions
1. Prove the documented VM + rclone deployment path on the actual Google Cloud target if cloud use is near-term (priority: medium; ~60 min)
1. Configure production HTTPS/auth perimeter before public exposure (priority: medium; ~30 min)

## Notes
- `.script-manager/` is treated as generated refresh output and ignored.
- Runtime practice state lives in the OTPD Scores library, not in this repository.
- PR #1 was merged to `main` on 2026-05-23.
- Local production-entrypoint smoke passed on 2026-05-23 with Basic Auth enabled: unauthenticated `/` returned `401`, authenticated `/` returned `200`, and authenticated `/api/library` read the configured Google Drive library.
