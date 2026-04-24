# Patch notes v0.2.2

## Installer/runtime dependency cleanup

- Added explicit `cuda-bindings>=12.6.0,<13` to `requirements_nemo_windows.txt`.
- GPU helper install now also repeats `cuda-bindings>=12.6.0,<13` next to `cuda-python` so older/dirty environments are repaired more reliably.
- Added a non-fatal `pip check` step after curated NeMo runtime dependency installation.
- If `pip check` still reports conflicts, the installer now warns but does not abort immediately. This makes it easier to distinguish harmless resolver noise from real import/runtime failures.

## Why this patch exists

Some NeMo 2.x builds declare `cuda-bindings` as a runtime dependency on non-macOS systems. When NeMo is installed in a curated Windows setup with `--no-deps`, pip can later warn that `cuda-bindings` is missing even though the app may still run. Installing the dependency explicitly keeps the environment cleaner and removes that warning in normal cases.
