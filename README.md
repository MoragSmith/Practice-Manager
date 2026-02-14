# Practice Manager

Track mastery of bass (and other instrument) scores for OTPD repertoire. Content is organized by **Sets**; practice and mastery apply to **Tunes** and **Parts**.

## Setup

1. Activate the shared development environment:
   ```bash
   source "/Users/moragsmith/Smith-Parkes Dropbox/Morag Smith/Home/Computer/Scripts/shared-dev-env/bin/activate"
   ```
   Or run `activate_shared_dev.sh` from the Scripts directory.  
   Practice Manager requires PySide6 and PyYAML (install with `pip install PySide6` if needed).

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

```bash
python run.py
```

## JSON Schema (practice_status.json)

Location: `OTPD Scores/#Script Resources/data/practice_status.json`

| Field | Type | Description |
|-------|------|-------------|
| schema_version | int | Schema version (currently 1) |
| last_updated | string | ISO timestamp of last save |
| decay_rate_percent_per_day | float | Default 1.0 (1% per day) |
| focus_instrument | string | "bass", "snare", etc. |
| focus_set_ids | array | Set IDs in focus list |
| show_focus_only | bool | If true, show only focus sets on next launch |
| items | object | Map of item_id → item record |

**Item record:**

| Field | Type | Description |
|-------|------|-------------|
| type | string | "set", "tune", or "part" |
| streak | int | Current success streak |
| score | float | 0–100 |
| last_practiced | string? | ISO timestamp |
| last_score_updated | string? | ISO timestamp (for decay) |
| missing | bool | True if item was renamed/removed |

**Item ID format:**
- Set: `SectionName|SetFolderName`
- Tune: `SectionName|SetFolderName|TuneName`
- Part: `SectionName|SetFolderName|Parts|PartLabel`

## Mastery Rules

- **Mastery**: 10 successes in a row (for tunes and parts only)
- **Score**: `(streak / 10) * 100` after each practice, capped at 100
- **Decay**: Tunes decay at configurable rate (default 1%/day); sets and parts do not decay
- **Reset Part**: Manual action sets streak and score to 0 for that part only

## Known Gaps / Future Work

- **Missing items**: The schema supports `missing: true` for renamed/removed items, and the UI shows "(missing)" in the sets list. Nothing currently *sets* items as missing; that logic (comparing discovered IDs vs stored items) is not implemented.
- **widgets.py**: Placeholder module for future shared UI components; unused.
- **Windows/Linux**: PDF/WAV open via `os.startfile`/`xdg-open`. macOS-only features (Acrobat left-half tiling, Music mini player, session bottom-right layout) do not apply.

## Tests

Activate shared-dev-env first, then (from project root):
```bash
pytest tests/ -v
```
