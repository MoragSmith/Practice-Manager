# Practice Manager: Web Migration Plan

## Overview

Extract shared logic into a `core` package, then add a web backend and frontend. Same data (practice_status.json, OTPD Scores on Google Drive), full practice tracking, plus a library browser.

## Phase 1: Extract Core Package ✓

**Goal:** Shared logic usable by both desktop and web, without breaking the Mac app.

**Structure:**
```
src/practice_manager/
├── core/                    # Shared: no GUI, no platform-specific open
│   ├── __init__.py
│   ├── config.py            # Library discovery, paths, constants
│   ├── data_model.py        # Load/save JSON, item management
│   ├── discovery.py         # Sets, tunes, parts discovery
│   ├── assets.py            # PDF/WAV path resolution (+ open_file for desktop)
│   └── decay.py             # Score decay
├── gui/                     # Desktop: PySide6
├── ensemble/                # Optional: Playwright download workflow
└── ...
```

**Tasks:**
- [x] Create `core/` with config, data_model, discovery, assets, decay
- [x] Fix config `_get_project_root()` for new path depth
- [x] Update all imports (run.py, gui, ensemble, tests)
- [x] Remove old top-level modules
- [x] Run tests to verify desktop unchanged

## Phase 2: Refactor Desktop to Use Core ✓

**Goal:** Desktop app imports from `practice_manager.core`; behavior identical.

**Tasks:**
- [x] Update run.py, main_window, session_window, download_parts_workflow
- [x] Update test imports
- [ ] Run full test suite
- [ ] Manual smoke test: launch desktop, start session, success/fail

## Phase 3: Add Web Backend ✓

**Goal:** FastAPI server with practice session + library browse APIs.

**Structure:**
```
src/practice_manager/
├── web/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   └── api/
│       ├── library.py       # GET /api/library, /api/library/sets/{set_id}
│       ├── practice.py      # POST /api/practice/start, success, fail
│       ├── assets.py        # GET /api/assets/pdf, /api/assets/wav (stream)
│       └── status.py        # GET/POST /api/status, POST /api/status/decay
```

**API:**
- `GET /api/library` – full library (sets with tunes, parts)
- `GET /api/library/sets/{set_id}` – single set details
- `GET /api/status` – practice_status.json (read)
- `POST /api/status` – save (JSON body)
- `POST /api/status/decay` – apply decay and save
- `POST /api/practice/start` – start session (item_type, item_id, instrument, …); returns pdf_url, wav_url
- `POST /api/practice/success` – record success
- `POST /api/practice/fail` – record fail
- `GET /api/assets/pdf?path=...` – stream PDF (path relative to library)
- `GET /api/assets/wav?path=...` – stream WAV

**Config:** Uses same discovery as desktop (tracker-config.json, LIBRARY_ROOT env).

**Run:** `python run_web.py` or `uvicorn src.practice_manager.web.main:app --reload --host 0.0.0.0`

**Tasks:**
- [x] Create `web/` package
- [x] FastAPI app with CORS
- [x] Library API (uses core.discovery, core.config)
- [x] Status API (uses core.data_model)
- [x] Practice API (start, success, fail)
- [x] Asset streaming (PDF, WAV)
- [x] requirements-web.txt

## Phase 4: Add Web Frontend ✓

**Goal:** SPA for library browse + practice session.

**Features:**
- Library browser: sections → sets → tunes/parts, instrument selector
- Practice session: PDF viewer (left), audio player (right), Success/Fail/End
- Full practice tracking (streak, score, decay)

**Tech:** Vanilla HTML/CSS/JS, served from FastAPI static mount.

**Location:** `src/practice_manager/web/static/` (index.html, style.css, app.js)

**Tasks:**
- [x] Frontend scaffold
- [x] Library browse UI
- [x] Practice session UI (PDF + audio)
- [x] Wire to backend APIs

## Phase 5: Deployment

**Goal:** Web app in cloud, data from Google Drive.

**Options:**
1. **rclone mount** – Mount Google Drive on VPS; app reads/writes filesystem
2. **rclone sync** – Periodic sync Drive → server; app uses local copy
3. **Google Drive API** – Direct API access (more complex)

**Recommended:** rclone mount or sync to a cloud VM (e.g. Fly.io, DigitalOcean, Railway).

**Tasks:**
- [ ] Choose host
- [ ] Set up Google Drive access (rclone)
- [ ] Deploy FastAPI (gunicorn/uvicorn)
- [ ] Deploy frontend (static or same server)
- [ ] Auth (optional: basic auth, OAuth, or VPN)

## Data Location

- **OTPD Scores:** Google Drive (user's)
- **practice_status.json:** `{library_root}/#Script Resources/data/practice_status.json`
- **Web server:** Needs read/write access to that path (via Drive mount or sync)

## Backward Compatibility

- Desktop app: unchanged behavior, same tracker-config.json, same JSON schema
- Web: uses same JSON, same discovery logic; `LIBRARY_ROOT` points to Drive path
