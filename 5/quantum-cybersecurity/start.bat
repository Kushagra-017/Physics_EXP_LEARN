@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 or newer and add it to PATH.
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
