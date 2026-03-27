# Practice Manager

Track mastery of bass (and other instrument) scores for OTPD repertoire. Content is organized by **Sets**; practice and mastery apply to **Tunes** and **Parts**. Set an instrument (bass, snare, bagpipes, etc.) per set for PDF playback.

## Operator Index

- Run desktop app: `python run.py`
- Run web app: `python run_web.py`
- Canonical launch wrappers: `scripts/launch/`
- Script boundary map: `scripts/README.md`
- Machine-room operations guide: `docs/OPERATIONS.md`
- Environment diagnostics: `bash scripts/env/check_env.sh`
- Standard test runner: `bash scripts/env/run_tests.sh`
- Shared env repair checklist: `docs/ENV_REPAIR_CHECKLIST.md`
- Deployment notes: `docs/GOOGLE_CLOUD_DEPLOYMENT.md`

## Project Layout

Use this as the machine-room map for the repository:

- `src/` - active application source code
- `tests/` - automated tests
- `docs/` - human-facing documentation and operational notes
- `deploy/` - deployment/service scripts and configs
- `run.py` / `run_web.py` - canonical desktop and web entrypoints
- `tracker-config.example.json` - template for local machine overrides
- `tracker-config.json` - local-only machine config (gitignored)

Operational boundary notes:

- Runtime practice state is stored in the OTPD Scores library, not in this repo:
  `OTPD Scores/#Script Resources/data/practice_status.json`
- Local transient caches (`__pycache__/`, `.pytest_cache/`, `*.pyc`) are ignored
- See `docs/OPERATIONS.md` for run/maintain guidance

## Setup

1. Activate the shared development environment:
   ```bash
   source ../shared-dev-env/bin/activate
   ```
   Or run `../activate_shared_dev.sh` from this project directory.
   Practice Manager requires PySide6, PyYAML, playwright, pypdf, and PyMuPDF. Install with:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Library discovery**: The app discovers the OTPD Scores library from (in order):
   - OTPD Music Manager's `config/default.yaml` or `data/preferences.json`
   - `#Script Resources/config.json` in the library
   - `tracker-config.json` in this project

   If discovery fails, copy `tracker-config.example.json` to `tracker-config.json` and set your paths:
   ```json
   {
     "library_root": "/path/to/OTPD Scores",
     "otpd_manager_path": "/path/to/OTPD Music Manager"
   }
   ```

## Run

**Desktop:**
```bash
python run.py
```

**Web server** (library browse + practice session API):
```bash
pip install -r requirements-web.txt
python run_web.py
```
Then open http://localhost:8000 (API docs at http://localhost:8000/docs). Uses the same data and config as the desktop app.

**Desktop shortcut (macOS):** Double-click `Practice Manager.app` on Desktop, or run `./launch_practice_manager.sh` from the project. To recreate the app after moving the project, run this from the project directory:
```bash
osacompile -o "$HOME/Desktop/Practice Manager.app" -e 'do shell script "bash \"'"$(pwd)"'/launch_practice_manager.sh\""'
```

Canonical launcher wrappers are in `scripts/launch/`; root launcher files remain as compatibility wrappers.

## JSON Schema (practice_status.json)

Location: `OTPD Scores/#Script Resources/data/practice_status.json`

| Field | Type | Description |
|-------|------|-------------|
| schema_version | int | Schema version (currently 1) |
| last_updated | string | ISO timestamp of last save |
| decay_rate_percent_per_day | float | Default 1.0 (1% per day) |
| focus_instrument | string | Default instrument for sets without override |
| set_instruments | object | Per-set overrides: set_id → "bass", "snare", etc. |
| focus_set_ids | array | Set IDs in focus list |
| show_focus_only | bool | If true, show only focus sets on next launch |
| items | object | Map of item_id → item record |

**Item record:** (items exist only for tunes and parts; sets are organizational)

| Field | Type | Description |
|-------|------|-------------|
| type | string | "tune" or "part" |
| streak | int | Current success streak |
| score | float | 0–100 |
| last_practiced | string? | ISO timestamp |
| last_score_updated | string? | ISO timestamp (for decay) |
| missing | bool | True if item was renamed/removed |

**Item ID format:**
- Tune: `SectionName|SetFolderName|TuneName`
- Part: `SectionName|SetFolderName|Parts|PartLabel`

## Practice Flow

- **Instrument**: Set per set (bass, snare, bagpipes, etc.) in the Set details pane
- **Parts grouping**: Parts are grouped by tune, then by phrase → line → part
- **Single-tune sets**: Competition-style sets without explicit tunes show a "practice complete tune" option
- **Integrated session window**: Single window with PDF on the left, WAV player (upper right), and Success/Fail/End Session buttons (lower right). No external Acrobat or Music app.

## Mastery Rules

- **Mastery**: 10 successes in a row (for tunes and parts only)
- **Score**: `(streak / 10) * 100` after each practice, capped at 100
- **Decay**: Tunes decay at configurable rate (default 1%/day); sets and parts do not decay
- **Reset Part**: Manual action sets streak and score to 0 for that part only

## Download Parts from Ensemble

A **Download Parts** button downloads all part items from the Ensemble Parts workspace (sibling of OTPD Music Book). For each part it downloads:
- Complete WAV (full score)
- Split PDFs (one per instrument: bagpipes, snare, bass, tenor, seconds)

Files are organized into `set_folder/Parts/` using the prefix in filenames (e.g. "Competition 08" maps to the matching set folder).

**Requirements:**
- Ensemble credentials: set `ENSEMBLE_USERNAME` and `ENSEMBLE_PASSWORD` environment variables, or configure in OTPD Music Manager config
- Playwright with Chromium: `playwright install chromium`

## Cloud Deployment (Google Cloud)

To host the web app in the cloud with OTPD Scores on Google Drive, see **[docs/GOOGLE_CLOUD_DEPLOYMENT.md](docs/GOOGLE_CLOUD_DEPLOYMENT.md)**. The guide covers:

- Creating a Compute Engine VM
- Mounting Google Drive with rclone
- Deploying the app and running it as a service
- Optional HTTPS and authentication

## Internal Prompt Templates

Internal AI prompt templates live in `docs/ai-prompts/`.

## Known Gaps / Future Work

- **Missing items**: The schema supports `missing: true` for renamed/removed items, and the UI shows "(missing)" in the sets list. Nothing currently *sets* items as missing; that logic (comparing discovered IDs vs stored items) is not implemented.
- **widgets.py**: Placeholder module for future shared UI components; unused.

## Tests

Activate shared-dev-env first, then (from project root):
```bash
pytest tests/ -v
```
Or use:
```bash
bash scripts/env/run_tests.sh
```

If launch/test tooling is failing due to environment path drift, run:
```bash
bash scripts/env/check_env.sh
```
Then follow `docs/ENV_REPAIR_CHECKLIST.md`.

**Test layout (no mocks; real files and real Ensemble):**
- **test_assets.py** – Asset resolution: instrument-specific PDFs, tune WAV/PDF lookup
- **test_parts_organizer.py** – PartsOrganizer: prefix extraction, folder mapping, file moves with real tmp_path
- **test_config.py** – Config: get_library_root and get_ensemble_config with real config files in tmp_path
- **test_data_model.py**, **test_decay.py**, **test_discovery.py** – Data model, decay, discovery
- **tests/integration/test_ensemble_parts.py** – E2E against real Ensemble: login → Parts → download (requires ENSEMBLE_USERNAME, ENSEMBLE_PASSWORD, library root)

Integration test is skipped if library root or Ensemble credentials are not configured.
