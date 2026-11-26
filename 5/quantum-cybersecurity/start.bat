@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0.python\python.exe" set "PATH=%~dp0.python;%PATH%"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo Python 3.10 or newer was not found. Run setup-windows.bat first.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 (echo Failed to create virtual environment.& pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt
if errorlevel 1 (echo Dependency installation failed.& pause & exit /b 1)
start "Quantum Cybersecurity server" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" -m waitress --listen=127.0.0.1:5000 app:app
timeout /t 3 /nobreak >nul
start "" "http://localhost:5000"
echo Server started in a separate window. Close that window to stop it.
