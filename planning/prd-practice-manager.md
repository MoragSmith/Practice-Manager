# Practice Manager - Product Requirements Document

## Status
- Status: active_build
- Completion: core product implemented; verification and deployment hardening remain
- Test status: standardized suite passing locally as of 2026-05-23 (`68 passed, 1 skipped`); web API regression coverage includes library/status/assets/practice, missing-item reconciliation, and Basic Auth checking

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
- Automatic missing-item reconciliation for renamed/removed tunes and parts

### Operations
- Standard launch/test scripts
- Environment diagnostics and repair notes
- Deployment guide and systemd assets

## Known Gaps
- Deployment remains documented rather than fully proven end-to-end in this repo
- Internet-facing deployments should use HTTPS plus Basic Auth at minimum; IAP/VPN is preferred for stronger protection

## Immediate Next Steps
1. Decide whether the web-runtime branch is ready for merge or needs one more hardening pass
2. If deployment is near-term, prove the documented VM path on a real target

## Product Questions Still Worth Answering
- Is the web app intended as a full peer to desktop, or primarily a remote-access companion?
- Is the deployment target public enough to require IAP/VPN, or is HTTPS + Basic Auth sufficient for the first release?
