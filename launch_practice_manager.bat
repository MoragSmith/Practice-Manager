@echo off
REM Backward-compatible wrapper. Canonical launcher lives in scripts/launch/.
setlocal
set "SCRIPT_DIR=%~dp0"
call "%SCRIPT_DIR%scripts\launch\launch_practice_manager.bat"
