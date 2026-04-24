# Patch notes v0.2.3

## Installer robustness

- Removed the hard `<13` upper bound from the CUDA Python helper package spec.
- `requirements_nemo_windows.txt` now uses `cuda-bindings>=12.8.0` so pip can resolve CUDA Python 12.x or newer 13.x wheels when they are compatible.
- GPU helper installation now uses `cuda-bindings>=12.8.0` and `cuda-python>=12.8.0` without an artificial CUDA-major ceiling.
- Fixed a subtle `choice` / `errorlevel` bug where the selected install mode could fall through and end up as GPU even when CPU or Skip was chosen.

## Windows start/minimize fix

- Replaced the fragile inline PowerShell minimize command with `tools/minimize_console.py` using Windows `ctypes` calls.
- This fixes the broken command fragment like `Out-Null}` that could prevent the GUI from starting after installation.
- `run_windows.bat` uses the same helper.

## Console readability

- Added ANSI-colored `[STEP]`, `[INFO]`, `[OK]`, `[WARN]`, and `[ERROR]` messages to the Windows installer.
- Added minimal colored status output to `run_windows.bat`.

## Notes

- `pip check` can still warn about dependency conflicts in some NeMo/nightly combinations. The installer reports those as warnings instead of immediately aborting if the application import check can proceed.
