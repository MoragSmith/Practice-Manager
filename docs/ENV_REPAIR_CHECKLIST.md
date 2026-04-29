# Shared Env Repair Checklist

Use this when `pytest` or launch scripts fail due to stale absolute paths in the shared environment.

**Operational overview:** `../../shared-dev-env/README.md` (from this file: `Scripts/shared-dev-env/README.md`) describes the venv layout, helper scripts (`setup/validate_env.sh`, `setup/export_requirements.sh`, `setup/repair_stale_paths.sh`), and stale-path behavior. **`activate_shared_dev.sh`** in `Scripts/` is **self-locating**: it `source`s `shared-dev-env/bin/activate` relative to its own directory, so you do not need to edit a hard-coded Dropbox path for normal use.

## Symptoms

- `pytest: command not found`
- `shared-dev-env/bin/pytest` or `bin/python3` references a non-existent interpreter path
- `grep` finds an old path inside `shared-dev-env/bin/*` (e.g. a previous Dropbox mount); see `shared-dev-env/README.md` and `setup/repair_stale_paths.sh` before rebuilding

## 5-Minute Safe Repair

Run these from your **Scripts** directory—the folder that contains `Practice Manager/`, `shared-dev-env/`, and `activate_shared_dev.sh`.

**Primary path (Finder / Dropbox folder):**

`/Users/moragsmith/Smith-Parkes Dropbox/Morag Smith/Tools & Systems/Scripts`

If your machine uses Dropbox’s filesystem provider instead, the same folder may appear under `~/Library/CloudStorage/Dropbox-*/.../Tools & Systems/Scripts`. Use whichever path actually contains `shared-dev-env` on disk.

1. Remove broken shared environment directory:
   ```bash
   rm -rf "shared-dev-env"
   ```
2. Recreate environment with current interpreter:
   ```bash
   python3 -m venv "shared-dev-env"
   ```
3. Activate and install dependencies used by Practice Manager:
   ```bash
   source "shared-dev-env/bin/activate"
   pip install --upgrade pip
   pip install -r "Practice Manager/requirements.txt"
   pip install -r "Practice Manager/requirements-web.txt"
   playwright install chromium
   ```
4. Ensure `activate_shared_dev.sh` exists next to `shared-dev-env/` and uses the **self-locating** pattern (no hard-coded absolute path to the venv). If the file is missing or was overwritten with a broken `source` line, recreate it:
   ```bash
   cat > "activate_shared_dev.sh" <<'EOF'
   #!/usr/bin/env bash
   # Activates the shared Python venv next to this script (works for any Dropbox mount path).
   # Documentation: shared-dev-env/README.md
   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
   echo "Activating shared development environment..."
   # shellcheck source=/dev/null
   source "$SCRIPT_DIR/shared-dev-env/bin/activate"
   echo "Shared development environment activated."
   EOF
   chmod +x "activate_shared_dev.sh"
   ```
5. Validate from project root:
   ```bash
   cd "Practice Manager"
   bash scripts/env/check_env.sh
   source ../activate_shared_dev.sh
   pytest tests/ -v
   ```

## Notes

- This rebuild is non-destructive for project source files.
- If `python3` is not Python 3.12+, install/enable Python 3.12 first, then recreate the venv.
- For **stale paths inside `bin/`** (wrong Dropbox prefix or moved folder) without a full delete/recreate, see **`shared-dev-env/README.md`** and **`shared-dev-env/setup/repair_stale_paths.sh`**.
