# Practice Manager

Track mastery of bass (and other instrument) scores for OTPD repertoire at **Set**, **Tune**, and **Part** levels.

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

   If discovery fails, create `tracker-config.json`:
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

- **Mastery**: 10 successes in a row
- **Score**: `(streak / 10) * 100` after each practice, capped at 100
- **Decay**: Sets and tunes decay at configurable rate (default 1%/day); parts do not decay
- **Reset Part**: Manual action sets streak and score to 0 for that part only

## Tests

Activate shared-dev-env first, then:
```bash
pytest tests/ -v
```
