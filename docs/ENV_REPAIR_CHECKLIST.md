# Shared Env Repair Checklist

Use this when `pytest` or launch scripts fail due to stale absolute paths in the shared environment.

## Symptoms

- `pytest: command not found`
- `activate_shared_dev.sh` points to `Smith-Parkes Dropbox` path
- `shared-dev-env/bin/pytest` references a non-existent python path

## 5-Minute Safe Repair

Run these from:
`/Users/moragsmith/Library/CloudStorage/Dropbox-Smith-Parkes/Morag Smith/Tools & Systems/Scripts`

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
4. Regenerate `activate_shared_dev.sh` to use the current absolute path:
   ```bash
   cat > "activate_shared_dev.sh" <<'EOF'
   #!/bin/bash
   echo "Activating shared development environment..."
   source "/Users/moragsmith/Library/CloudStorage/Dropbox-Smith-Parkes/Morag Smith/Tools & Systems/Scripts/shared-dev-env/bin/activate"
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
