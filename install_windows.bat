@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

for /F "delims=" %%A in ('echo prompt $E^| cmd') do set "ESC=%%A"
set "C_RESET=%ESC%[0m"
set "C_HEAD=%ESC%[95m"
set "C_STEP=%ESC%[96m"
set "C_OK=%ESC%[92m"
set "C_WARN=%ESC%[93m"
set "C_ERR=%ESC%[91m"
set "C_DIM=%ESC%[90m"

call :header "Magpie TTS Studio - Windows Installer"
echo.
echo This installer will:
echo   1. create a local virtual environment
echo   2. install GUI dependencies
echo   3. install NVIDIA NeMo and curated Windows runtime dependencies
echo   4. optionally pre-download the Magpie model
echo   5. optionally start the GUI after setup
echo.
call :warn "Text normalization via nemo_text_processing / Pynini is not installed by default on Windows."
call :info "The app can still synthesize speech. TN remains optional and may auto-disable."
echo.

set "PY_CMD="
set "PY_DESC="
set "PY_VER="
set "PY_OK="
set "MODE="
set "MISSING_PACKAGE="

call :step "Searching for a usable Python interpreter..."
call :try_candidate "py -3.12" "Python 3.12 via py launcher"
if defined PY_CMD goto :python_selected
call :try_candidate "py -3.11" "Python 3.11 via py launcher"
if defined PY_CMD goto :python_selected
call :try_candidate "py -3.10" "Python 3.10 via py launcher"
if defined PY_CMD goto :python_selected
call :try_candidate "py -3" "Default Python 3 via py launcher"
if defined PY_CMD goto :python_selected
call :try_candidate "py" "Default Python via py launcher"
if defined PY_CMD goto :python_selected
call :try_candidate "python" "python on PATH"
if defined PY_CMD goto :python_selected

call :err "No usable Python interpreter was found."
echo Please install Python and re-run this script.
echo.
echo Tip: python.org installs are usually the least surprising for local venv projects.
pause
exit /b 1

:python_selected
for /f %%V in ('%PY_CMD% -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PY_VER=%%V"
for /f %%C in ('%PY_CMD% -c "import sys; print(1 if sys.version_info >= (3, 10) else 0)" 2^>nul') do set "PY_OK=%%C"

call :ok "Using interpreter: %PY_DESC%"
if defined PY_VER call :info "Detected version: %PY_VER%"

if not "%PY_OK%"=="1" (
    echo.
    call :warn "Detected Python %PY_VER%. Magpie / NVIDIA NeMo usually expects Python 3.10 or newer."
    call :warn "The installation will continue anyway, but some packages may fail later."
    echo.
)

if exist ".venv\Scripts\python.exe" (
    call :warn "Existing venv found."
    choice /C RK /N /T 10 /D R /M "[R]ebuild venv default in 10s, [K]eep current venv? "
    if errorlevel 2 (
        call :info "Keeping existing venv."
    ) else (
        call :step "Removing existing venv for a clean reinstall..."
        rmdir /S /Q .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    call :step "Creating venv..."
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

call :step "Upgrading packaging tools..."
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error

echo.
choice /C GCS /N /T 20 /D G /M "Install mode: [G]PU CUDA default in 20s, [C]PU, [S]kip NeMo install? "
if errorlevel 3 (
    set "MODE=skip"
) else if errorlevel 2 (
    set "MODE=cpu"
) else (
    set "MODE=gpu"
)
call :info "Selected install mode: %MODE%"

call :step "Installing common requirements..."
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    call :step "Installing PyTorch CUDA 12.4 wheels..."
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    if errorlevel 1 goto :error
)

if /I "%MODE%"=="cpu" (
    call :step "Installing CPU PyTorch wheels..."
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 goto :error
)

if /I "%MODE%"=="skip" goto :ask_prefetch

echo.
call :step "Installing NeMo core package without auto-pulling unsupported Windows TN dependencies..."
python -m pip install --no-deps "nemo_toolkit @ git+https://github.com/NVIDIA-NeMo/NeMo.git"
if errorlevel 1 goto :nemo_core_fallback
goto :after_nemo_core

:nemo_core_fallback
call :warn "GitHub NeMo core install failed. Trying published package fallback..."
python -m pip install --no-deps nemo-toolkit
if errorlevel 1 goto :error

:after_nemo_core
call :step "Installing curated NeMo runtime dependencies for Windows..."
python -m pip install -r requirements_nemo_windows.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    echo.
    call :step "Installing optional CUDA helper packages for NeMo..."
    call :info "No upper CUDA major cap is used here; pip may choose CUDA Python 12.x or 13.x if compatible."
    python -m pip install "cuda-bindings>=12.8.0" "cuda-python>=12.8.0" "numba-cuda[cu12]"
    if errorlevel 1 (
        call :warn "Optional CUDA helper packages could not be installed."
        call :warn "The app may still work, but GPU inference could be less reliable depending on your setup."
        echo.
    )
)

call :step "Checking installed Python package consistency..."
python -m pip check
if errorlevel 1 (
    echo.
    call :warn "pip check still reports dependency conflicts."
    call :warn "If the app starts and generates audio, this is often non-fatal, but keep this output for troubleshooting."
    echo.
)

set "IMPORT_RETRY_COUNT=0"
:run_nemo_import_check
set "MISSING_PACKAGE="
call :step "Running import check..."
python tools\check_nemo_import.py > import_check.json
if not errorlevel 1 goto :nemo_import_ok

echo.
call :warn "Import check did not pass yet. Looking for missing runtime packages..."
for /f "usebackq delims=" %%P in (`python tools\resolve_missing_package.py import_check.json`) do set "MISSING_PACKAGE=%%P"
if not defined MISSING_PACKAGE goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__none__" goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__unknown__" goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__optional_windows_text_normalization__" goto :nemo_import_optional_tn

set /a IMPORT_RETRY_COUNT+=1
if %IMPORT_RETRY_COUNT% GTR 6 goto :nemo_import_failed_final

call :step "Installing missing runtime package: %MISSING_PACKAGE%"
python -m pip install %MISSING_PACKAGE%
if errorlevel 1 goto :nemo_import_failed_final
goto :run_nemo_import_check

:nemo_import_ok
echo.
call :ok "NeMo installation step finished."
goto :ask_prefetch

:nemo_import_optional_tn
echo.
call :warn "NeMo import check reported missing Pynini / nemo_text_processing."
call :warn "This is expected on many Windows setups because Pynini is not a normal pip dependency there."
call :info "Continuing with text normalization disabled. Leave the app option unchecked unless you install TN separately."
echo.
goto :ask_prefetch

:nemo_import_failed_final
echo.
call :err "NeMo was installed, but the Magpie model class could not be imported."
echo Import check details:
type import_check.json
echo.
call :warn "If you updated files inside an older project folder, use a clean rebuild of the .venv next run."
call :warn "Please keep this console output and send it back for another patch round."
goto :error

:ask_prefetch
choice /C YN /N /T 10 /D Y /M "Pre-download the Magpie model now? [Y/N] default Y in 10s: "
if errorlevel 2 goto :done
if errorlevel 1 (
    call :step "Downloading model into local cache..."
    python tools\preload_models.py
    if errorlevel 1 goto :error
)

:done
echo.
call :ok "Installation finished."
choice /C YN /N /T 10 /D Y /M "Start Magpie TTS Studio GUI now? [Y/N] default Y in 10s: "
if errorlevel 2 goto :done_no_start
if errorlevel 1 goto :start_gui

:done_no_start
echo.
call :info "Start the app later with run_windows.bat"
echo.
pause
exit /b 0

:start_gui
echo.
call :step "Starting GUI now. The console window will be minimized where Windows allows it."
call :minimize_console
python app.py
echo.
call :info "GUI closed."
pause
exit /b 0

:error
echo.
call :err "Installation failed."
pause
exit /b 1

:minimize_console
python tools\minimize_console.py >nul 2>nul
exit /b 0

:try_candidate
%~1 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=%~1"
    set "PY_DESC=%~2"
)
goto :eof

:header
echo %C_HEAD%================================================%C_RESET%
echo %C_HEAD%%~1%C_RESET%
echo %C_HEAD%================================================%C_RESET%
goto :eof

:step
echo %C_STEP%[STEP]%C_RESET% %~1
goto :eof

:info
echo %C_DIM%[INFO]%C_RESET% %~1
goto :eof

:ok
echo %C_OK%[OK]%C_RESET% %~1
goto :eof

:warn
echo %C_WARN%[WARN]%C_RESET% %~1
goto :eof

:err
echo %C_ERR%[ERROR]%C_RESET% %~1
goto :eof
