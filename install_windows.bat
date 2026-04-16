@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ================================================
echo Magpie TTS Studio - Windows Installer
echo ================================================

echo.
echo This installer will:
echo 1. create a local virtual environment
echo 2. install GUI dependencies
echo 3. install NVIDIA NeMo for Magpie TTS
echo 4. optionally pre-download the Magpie model
echo.

echo Note for Windows:
echo Text normalization via nemo_text_processing / Pynini is not installed by default here.
echo The app can still synthesize speech, but TN will stay optional and may auto-disable.
echo.

set "PY_CMD="
set "PY_DESC="
set "PY_VER="
set "PY_OK="

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

echo No usable Python interpreter was found.
echo Please install Python and re-run this script.
echo.
echo Tip: python.org installs are usually the least surprising for local venv projects.
pause
exit /b 1

:python_selected
for /f %%V in ('%PY_CMD% -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PY_VER=%%V"
for /f %%C in ('%PY_CMD% -c "import sys; print(1 if sys.version_info >= (3, 10) else 0)" 2^>nul') do set "PY_OK=%%C"

echo Using interpreter: %PY_DESC%
if defined PY_VER echo Detected version: %PY_VER%

if not "%PY_OK%"=="1" (
    echo.
    echo WARNING: Detected Python %PY_VER%.
    echo Magpie / NVIDIA NeMo usually expects Python 3.10 or newer.
    echo The installation will continue anyway, but some packages may fail later.
    echo.
)

if exist ".venv\Scripts\python.exe" (
    echo Existing venv found.
    choice /C RK /N /T 10 /D R /M "[R]ebuild venv default in 10s, [K]eep current venv? "
    if errorlevel 2 (
        echo Keeping existing venv.
    ) else (
        echo Removing existing venv for a clean reinstall...
        rmdir /S /Q .venv
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating venv...
    %PY_CMD% -m venv .venv
    if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo Upgrading packaging tools...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :error

echo.
choice /C GCS /N /T 20 /D G /M "Install mode: [G]PU CUDA12 default in 20s, [C]PU, [S]kip NeMo install? "
if errorlevel 3 set "MODE=skip"
if errorlevel 2 set "MODE=cpu"
if errorlevel 1 set "MODE=gpu"

echo Installing common requirements...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    echo Installing PyTorch CUDA 12.4 wheels...
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    if errorlevel 1 goto :error
)

if /I "%MODE%"=="cpu" (
    echo Installing CPU PyTorch wheels...
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 goto :error
)

if /I not "%MODE%"=="skip" goto :install_nemo
goto :ask_prefetch

:install_nemo
echo.
echo Installing NeMo core package without auto-pulling unsupported Windows TN dependencies...
python -m pip install --no-deps "nemo_toolkit @ git+https://github.com/NVIDIA-NeMo/NeMo.git"
if errorlevel 1 goto :nemo_core_fallback

goto :after_nemo_core

:nemo_core_fallback
echo GitHub NeMo core install failed. Trying published package fallback...
python -m pip install --no-deps nemo-toolkit
if errorlevel 1 goto :error

:after_nemo_core
echo Installing curated NeMo runtime dependencies for Windows...
python -m pip install -r requirements_nemo_windows.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    echo Installing optional CUDA helper packages for NeMo...
    python -m pip install "numba-cuda[cu12]" "cuda-python>=12.6.0,<13"
    if errorlevel 1 (
        echo WARNING: Optional CUDA helper packages could not be installed.
        echo The app may still work, but GPU inference could be less reliable depending on your setup.
        echo.
    )
)

set "IMPORT_RETRY_COUNT=0"
:run_nemo_import_check
echo Running import check...
python tools\check_nemo_import.py > import_check.json
if not errorlevel 1 goto :nemo_import_ok

echo.
echo Import check did not pass yet. Looking for missing runtime packages...
for /f "usebackq delims=" %%P in (`python tools\resolve_missing_package.py import_check.json`) do set "MISSING_PACKAGE=%%P"
if not defined MISSING_PACKAGE goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__none__" goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__unknown__" goto :nemo_import_failed_final

set /a IMPORT_RETRY_COUNT+=1
if %IMPORT_RETRY_COUNT% GTR 6 goto :nemo_import_failed_final

echo Installing missing runtime package: %MISSING_PACKAGE%
python -m pip install %MISSING_PACKAGE%
if errorlevel 1 goto :nemo_import_failed_final
goto :run_nemo_import_check

:nemo_import_ok
echo.
echo NeMo installation step finished.
goto :ask_prefetch

:nemo_import_failed_final
echo.
echo ERROR: NeMo was installed, but the Magpie model class could not be imported.
echo Import check details:
type import_check.json
echo.
echo If you updated files inside an older project folder, use a clean rebuild of the .venv next run.
echo Please keep this console output and send it back for another patch round.
goto :error

:ask_prefetch

:install_nemo
echo.
echo Installing NeMo core package without auto-pulling unsupported Windows TN dependencies...
python -m pip install --no-deps "nemo_toolkit @ git+https://github.com/NVIDIA-NeMo/NeMo.git"
if errorlevel 1 goto :nemo_core_fallback

goto :after_nemo_core

:nemo_core_fallback
echo GitHub NeMo core install failed. Trying published package fallback...
python -m pip install --no-deps nemo-toolkit
if errorlevel 1 goto :error

:after_nemo_core
echo Installing curated NeMo runtime dependencies for Windows...
python -m pip install -r requirements_nemo_windows.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    echo Installing optional CUDA helper packages for NeMo...
    python -m pip install "numba-cuda[cu12]" "cuda-python>=12.6.0,<13"
    if errorlevel 1 (
        echo WARNING: Optional CUDA helper packages could not be installed.
        echo The app may still work, but GPU inference could be less reliable depending on your setup.
        echo.
    )
)

set "IMPORT_RETRY_COUNT=0"
:run_nemo_import_check
echo Running import check...
python tools\check_nemo_import.py > import_check.json
if not errorlevel 1 goto :nemo_import_ok

echo.
echo Import check did not pass yet. Looking for missing runtime packages...
for /f "usebackq delims=" %%P in (`python tools
esolve_missing_package.py import_check.json`) do set "MISSING_PACKAGE=%%P"
if not defined MISSING_PACKAGE goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__none__" goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__unknown__" goto :nemo_import_failed_final

set /a IMPORT_RETRY_COUNT+=1
if %IMPORT_RETRY_COUNT% GTR 6 goto :nemo_import_failed_final

echo Installing missing runtime package: %MISSING_PACKAGE%
python -m pip install %MISSING_PACKAGE%
if errorlevel 1 goto :nemo_import_failed_final
goto :run_nemo_import_check

:nemo_import_ok
echo.
echo NeMo installation step finished.
goto :ask_prefetch

:nemo_import_failed_final
echo.
echo ERROR: NeMo was installed, but the Magpie model class could not be imported.
echo Import check details:
type import_check.json
echo.
echo If you updated files inside an older project folder, use a clean rebuild of the .venv next run.
echo Please keep this console output and send it back for another patch round.
goto :error

:ask_prefetch

:install_nemo
echo.
echo Installing NeMo core package without auto-pulling unsupported Windows TN dependencies...
python -m pip install --no-deps "nemo_toolkit @ git+https://github.com/NVIDIA-NeMo/NeMo.git"
if errorlevel 1 goto :nemo_core_fallback

goto :after_nemo_core

:nemo_core_fallback
echo GitHub NeMo core install failed. Trying published package fallback...
python -m pip install --no-deps nemo-toolkit
if errorlevel 1 goto :error

:after_nemo_core
echo Installing curated NeMo runtime dependencies for Windows...
python -m pip install -r requirements_nemo_windows.txt
if errorlevel 1 goto :error

if /I "%MODE%"=="gpu" (
    echo Installing optional CUDA helper packages for NeMo...
    python -m pip install "numba-cuda[cu12]" "cuda-python>=12.6.0,<13"
    if errorlevel 1 (
        echo WARNING: Optional CUDA helper packages could not be installed.
        echo The app may still work, but GPU inference could be less reliable depending on your setup.
        echo.
    )
)

set "IMPORT_RETRY_COUNT=0"
:run_nemo_import_check
echo Running import check...
python tools\check_nemo_import.py > import_check.json
if not errorlevel 1 goto :nemo_import_ok

echo.
echo Import check did not pass yet. Looking for missing runtime packages...
for /f "usebackq delims=" %%P in (`python tools
esolve_missing_package.py import_check.json`) do set "MISSING_PACKAGE=%%P"
if not defined MISSING_PACKAGE goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__none__" goto :nemo_import_failed_final
if /I "%MISSING_PACKAGE%"=="__unknown__" goto :nemo_import_failed_final

set /a IMPORT_RETRY_COUNT+=1
if %IMPORT_RETRY_COUNT% GTR 6 goto :nemo_import_failed_final

echo Installing missing runtime package: %MISSING_PACKAGE%
python -m pip install %MISSING_PACKAGE%
if errorlevel 1 goto :nemo_import_failed_final
goto :run_nemo_import_check

:nemo_import_ok
echo.
echo NeMo installation step finished.
goto :ask_prefetch

:nemo_import_failed_final
echo.
echo ERROR: NeMo was installed, but the Magpie model class could not be imported.
echo Import check details:
type import_check.json
echo.
echo If you updated files inside an older project folder, use a clean rebuild of the .venv next run.
echo Please keep this console output and send it back for another patch round.
goto :error

:ask_prefetch
choice /C YN /N /T 10 /D Y /M "Pre-download the Magpie model now? [Y/N] default Y in 10s: "
if errorlevel 2 goto :done
if errorlevel 1 (
    echo Downloading model into local cache...
    python tools\preload_models.py
    if errorlevel 1 goto :error
)

:done
echo.
echo Installation finished.
echo Start the app with run_windows.bat
pause
exit /b 0

:error
echo.
echo Installation failed.
pause
exit /b 1

:try_candidate
%~1 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PY_CMD=%~1"
    set "PY_DESC=%~2"
)
goto :eof
