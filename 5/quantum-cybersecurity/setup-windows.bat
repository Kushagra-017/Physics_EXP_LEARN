@echo off
setlocal
cd /d "%~dp0"
title Quantum Cybersecurity - Windows Setup

echo =====================================================
echo   Quantum Cybersecurity - first-time Windows setup
echo =====================================================
echo This setup downloads Python if needed, installs the app
echo dependencies, and opens the app in your browser.
echo Internet access is required. No administrator access
echo should be needed in a writable project folder.
echo.

rem Prefer the project-local Python on later runs.
if exist "%~dp0.python\python.exe" set "PATH=%~dp0.python;%PATH%"
rem Avoid invoking the Microsoft Store app-execution alias on a fresh PC.
where python 2>nul | findstr /i /v /c:"WindowsApps" >nul
if errorlevel 1 goto download_python_check_arch
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto python_ready

:download_python_check_arch
rem The official 64-bit installer targets standard x64 Windows computers.
if /i "%PROCESSOR_ARCHITECTURE%"=="AMD64" goto download_python
if /i "%PROCESSOR_ARCHITEW6432%"=="AMD64" goto download_python
echo This automatic installer supports 64-bit x64 Windows only.
echo For another architecture, install a compatible Python 3.10 or newer
echo from https://www.python.org/downloads/ and run start.bat.
pause
exit /b 1

:download_python
echo Python was not found. Downloading Python 3.12.10 from python.org...
set "PY_SETUP_DIR=%TEMP%\quantum-python-%RANDOM%-%RANDOM%"
mkdir "%PY_SETUP_DIR%" >nul 2>&1
if errorlevel 1 (
  echo Could not create a temporary download folder.
  pause
  exit /b 1
)
set "PY_INSTALLER=%PY_SETUP_DIR%\python-installer.exe"
rem Reject failed or unsigned downloads before running the installer.
powershell.exe -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile $env:PY_INSTALLER; $s = Get-AuthenticodeSignature -LiteralPath $env:PY_INSTALLER; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python installer signature verification failed.' }"
if errorlevel 1 (
  echo Download or signature verification failed. Check your internet connection.
  rmdir /s /q "%PY_SETUP_DIR%" >nul 2>&1
  pause
  exit /b 1
)
echo Installing Python in the project folder. This may take a few minutes...
start "" /wait "%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 Include_pip=1 Include_launcher=0 "TargetDir=%~dp0.python"
set "INSTALL_RESULT=%ERRORLEVEL%"
rmdir /s /q "%PY_SETUP_DIR%" >nul 2>&1
if not exist "%~dp0.python\python.exe" (
  echo Python installation failed with exit code %INSTALL_RESULT%.
  echo Make sure this project folder is writable and try again.
  pause
  exit /b 1
)
set "PATH=%~dp0.python;%PATH%"
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo The installed Python could not be started. Check your Windows installation.
  pause
  exit /b 1
)

:python_ready
echo Python is ready. Installing dependencies and starting the app...
call "%~dp0start.bat"
if errorlevel 1 exit /b 1
exit /b 0
