@echo off
setlocal EnableExtensions
cd /d "%~dp0"

for /F "delims=" %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"
set "C_RESET=%ESC%[0m"
set "C_STEP=%ESC%[96m"
set "C_ERR=%ESC%[91m"

if not exist ".venv\Scripts\python.exe" (
    echo %C_ERR%[ERROR]%C_RESET% Virtual environment not found. Please run install_windows.bat first.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo %C_ERR%[ERROR]%C_RESET% Could not activate virtual environment.
    pause
    exit /b 1
)

echo %C_STEP%[STEP]%C_RESET% Starting Magpie TTS Studio. Console will be minimized where Windows allows it.
python tools\minimize_console.py >nul 2>nul
python app.py
exit /b %errorlevel%
