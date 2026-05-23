# Status

- Reviewed for **`Practice Manager`**.
- **generated_at:** 2026-05-23
- **health:** green-for-integration
- **headline:** Practice Manager core, desktop, and web-runtime slice are implemented. Local tests, web/API coverage, missing-item reconciliation, auth hardening, real-library web read/write smokes, and desktop headless smoke pass. Remaining work is integration/PR and deployment proof if needed.

Suggested actions for IDEs: **`suggested-next-actions.md`** in this folder.

---

## Current state
- Track mastery of bass (and other instrument) scores for OTPD repertoire. Core, desktop, Ensemble, and web runtime code are present. Local automated verification, web/API regression coverage, missing-item detection, auth hardening, and real-library smokes pass.
- Phase: **integration-ready**
- Health: **green-for-integration**

## Local evidence
- Primary local brief: `README.md`
- Project description from local docs: Track mastery of bass (and other instrument) scores for OTPD repertoire. Content is organized by Sets ; practice and mastery apply to Tunes and Parts . Set an instrument (bass, snare, bagpipes, etc.) per set for PDF playback.
- Top-level contents: .git, .gitignore, .pytest_cache, Launch_Practice_Manager.command, README.md, deploy, docs, launch_practice_manager.bat
- Git branch: `feature/operational-legibility-web-runtime`
- Recent meaningful files: `tests/test_web_api.py`, `src/practice_manager/web/api/practice.py`, `src/practice_manager/web/api/assets.py`, `README.md`, `docs/OPERATIONS.md`
- Planning docs present: PRD `prd-practice-manager.md`, tasks `tasks-practice-manager.md`
- Current verification baseline: `68 passed, 1 skipped`

## Recommended next actions
1. Open/merge an integration PR for the verified web-runtime branch (priority: high; ~30 min)
1. Prove the documented VM + rclone deployment path if cloud use is near-term (priority: medium; ~60 min)

## Notes
- `.script-manager/` is treated as generated refresh output and ignored.
- Runtime practice state lives in the OTPD Scores library, not in this repository.
