# Magpie TTS Studio

A modern PyQt6 desktop GUI for the Hugging Face model `nvidia/magpie_tts_multilingual_357m` by NVIDIA.

## Features

- modern dark/light desktop UI
- separate settings window for app language, TTS language, speaker, device and storage paths
- local cache folder for Hugging Face downloads
- first-run or manual model pre-download
- WAV export with timestamp-based filenames
- generation progress bar with model/synthesis/post-processing phases
- optional WAV post-processing: peak normalization, output gain, chorus, echo, robot/vocoder-like voice coloration, tremolo, bitcrusher, pitch and speed changes
- built-in audio-effect preview using `assets/audio/effect_preview_clean.wav`
- small CUDA speed optimization via TF32 where supported
- last-output playback inside the app
- virtual-environment friendly Windows setup scripts
- future-friendly `cuda-bindings` install to avoid NeMo/pip resolver warnings on Windows without hard-pinning CUDA below 13

Interface Preview (here a example in german language, but the app supports English, German, Spanish, French, Italian, Vietnamese, Chinese, Hindi, Japanese)

<img width="1123" height="1023" alt="v2_6_test_german" src="https://github.com/user-attachments/assets/e4fa2090-17f1-4f75-8a9b-cb9e0bb6d04c" />

Preview Output Audio with used postprocessing:

https://github.com/user-attachments/assets/edc8d234-aabe-460a-8cf4-a4f596d2afe0

## Project structure

- `app.py` — GUI entry point
- `src/main_window.py` — main application window
- `src/options_dialog.py` — settings dialog
- `src/tts_backend.py` — Magpie/NeMo loading and synthesis backend
- `src/audio_effects.py` — dependency-light WAV post-processing effects
- `assets/audio/effect_preview_clean.wav` — clean sample used for effect preview playback
- `docs/` — patch notes and project documentation
- `tools/preload_models.py` — optional model prefetch tool
- `tools/minimize_console.py` — Windows console minimize helper used by the starter scripts
- `install_windows.bat` — creates venv, installs dependencies, optionally pre-downloads model
- `run_windows.bat` — launches the app inside the venv

## Quick start

### Windows

1. Extract the ZIP.
2. Run `install_windows.bat`.
3. The installer now tries Python 3.12, 3.11, 3.10, then any available `py`/`python` interpreter. If your version is older than 3.10, it warns but still continues.
4. After setup, the installer asks whether it should start the GUI immediately. If you do not answer within 10 seconds, it starts the GUI and minimizes the console window where Windows allows it. The minimize helper now uses a small Python/ctypes helper instead of fragile inline PowerShell quoting.
5. Later starts still use `run_windows.bat`.

### Manual install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install torch torchvision torchaudio
python -m pip install "nemo_toolkit[asr,tts] @ git+https://github.com/NVIDIA/NeMo.git"
python tools/preload_models.py
python app.py
```

## Notes

- Versioned patch notes are stored in `docs/` to keep the project root focused on launch/install files.
- This model is large, so keep enough free disk space for the `.nemo` checkpoint plus cache files.
- If the GitHub NeMo install fails, the Windows installer tries a published-package fallback.
- The installer explicitly installs `cuda-bindings>=12.8.0`, because recent NeMo builds declare it as a non-macOS runtime dependency. There is intentionally no `<13` cap; pip may select CUDA Python 12.x or newer 13.x wheels when they are compatible with the rest of the environment. This prevents the common pip resolver warning: `nemo-toolkit ... requires cuda-bindings, which is not installed`.
- `Apply text normalization` is intentionally optional because text-normalization availability can vary by environment.
- The app stores settings in `app_data/settings.json`.
- Audio effects are applied after Magpie has generated the WAV data. This keeps the core model inference path stable and allows fast reconfiguration of output coloration.
- In Settings → Audio effects, use `Preview original` and `Preview current effects` to compare the bundled clean WAV with the currently selected effect chain without generating new speech.
- The complete installation including all requirements takes ~7.5GB disc space at all.
- The first audio might take a while because the engine have to load the model into memory first, its much faster for the next runs.

## Supported model languages

- English (`en`)
- German (`de`)
- Spanish (`es`)
- French (`fr`)
- Italian (`it`)
- Vietnamese (`vi`)
- Chinese (`zh`)
- Hindi (`hi`)
- Japanese (`ja`)

## Speakers

- Sofia
- Aria
- Jason
- Leo
- John


## Windows note

This project uses a Windows-specific NeMo install path. `nemo_text_processing` / `pynini` is intentionally not installed by default because pip-based Windows installs are not officially supported for that dependency chain. The app can still synthesize speech normally, and text normalization remains optional.

## GUI Source

github.com/zeittresor/Magpie_TTS_Studio

## v0.2.4 note: NeMo/Magpie embedding compatibility

Recent NeMo builds may create a Magpie text embedding with a slightly different vocabulary row count than the public `nvidia/magpie_tts_multilingual_357m` checkpoint. Version 0.2.4 includes a narrow compatibility patch during model loading so a tiny row-count drift does not crash the GUI on first generation. Full tracebacks are still written to the log if a real model-loading error remains.

## v0.2.5 note: generalized NeMo embedding compatibility

Version 0.2.5 replaces the earlier hardcoded embedding-row workaround with a generic compatibility layer for future NeMo/tokenizer vocabulary drift. The patch only adapts row-count differences for 2D PyTorch `Embedding` weights when the embedding width is unchanged. It copies overlapping checkpoint rows and leaves additional runtime rows initialized. Large mismatches or different embedding widths still fail normally.

Advanced environment overrides:

```bat
set MAGPIE_EMBEDDING_COMPAT_MAX_ROWS=4096
set MAGPIE_EMBEDDING_COMPAT_MAX_RATIO=0.50
set MAGPIE_DISABLE_EMBEDDING_COMPAT_PATCH=1
```

