# Practice Manager - Product Requirements Document

## Status
- Status: active_build
- Completion: core product implemented; verification and deployment hardening remain
- Test status: standardized suite passing locally as of 2026-05-21 (`64 passed, 1 skipped`); web API regression coverage added for library/status/assets/practice, with real-library smoke checks also passing

## Product Goal
Help musicians track mastery of OTPD repertoire by set, tune, and part, with integrated score/audio practice sessions and shared data across desktop and web runtimes.

## Current Product Shape
- Desktop app for library browsing, focused practice, integrated PDF/audio sessions, and Ensemble parts download
- Shared `core` package for config, discovery, assets, persistence, and decay
- Web app with FastAPI backend and browser UI using the same data model and library
- Cloud deployment path documented for a VM + mounted Google Drive workflow

## Implemented
### Shared core
- Library/config discovery
- Practice status persistence with backups
- Set/tune/part discovery
- Asset resolution for PDFs and WAVs
- Tune score decay

### Desktop
- Set/tune/part browsing
- Per-set instrument selection
- Integrated session window
- Success/fail tracking
- Manual part reset
- Ensemble parts download workflow

### Web
- Library, status, practice, and asset APIs
- Static frontend for browse + practice flow
- Recall mode in practice session
- Optional HTTP Basic Auth

### Operations
- Standard launch/test scripts
- Environment diagnostics and repair notes
- Deployment guide and systemd assets

## Known Gaps
- Missing-item detection exists in the schema/UI conceptually but is not yet implemented
- Deployment remains documented rather than fully proven end-to-end in this repo
- `widgets.py` is an unused placeholder

## Immediate Next Steps
1. Decide whether the web-runtime branch is ready for merge or needs one more hardening pass
2. If deployment is near-term, prove the documented VM path on a real target
3. Consider automatic missing-item detection before broader use

## Product Questions Still Worth Answering
- Should “missing” items be marked automatically when discovered library contents diverge from saved practice records?
- Is the web app intended as a full peer to desktop, or primarily a remote-access companion?
- Does the deployment target need stronger auth than optional Basic Auth before real use?
