@echo off
REM Canonical Windows launcher for Practice Manager.
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "PYTHON_BIN=%PROJECT_ROOT%\..\shared-dev-env\Scripts\python.exe"

if not exist "%PYTHON_BIN%" (
  echo Shared environment python not found at: %PYTHON_BIN%
  echo Update launcher path or recreate shared-dev-env.
  exit /b 1
)

cd /d "%PROJECT_ROOT%"
"%PYTHON_BIN%" run.py
