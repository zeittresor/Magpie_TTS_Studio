# Magpie TTS Studio

A modern PyQt6 desktop GUI for the Hugging Face model `nvidia/magpie_tts_multilingual_357m`.

## Features

- modern dark/light desktop UI
- separate settings window for app language, TTS language, speaker, device and storage paths
- local cache folder for Hugging Face downloads
- first-run or manual model pre-download
- WAV export with timestamp-based filenames
- last-output playback inside the app
- virtual-environment friendly Windows setup scripts

  <img width="1143" height="983" alt="magpie_tts_studio" src="https://github.com/user-attachments/assets/c553af37-64cd-4e16-8925-65cb9d27bc57" />

Direct english output (example):

  https://github.com/user-attachments/assets/ed5dcb96-3f7a-476e-b8b6-ccc55e748d26

  German Voice Output (example random generated sci-fi story):

https://github.com/user-attachments/assets/aa309b10-f6c8-4867-bd62-ee82161e4a4f

## Project structure

- `app.py` — GUI entry point
- `src/main_window.py` — main application window
- `src/options_dialog.py` — settings dialog
- `src/tts_backend.py` — Magpie/NeMo loading and synthesis backend
- `tools/preload_models.py` — optional model prefetch tool
- `install_windows.bat` — creates venv, installs dependencies, optionally pre-downloads model
- `run_windows.bat` — launches the app inside the venv

## Quick start

### Windows

1. Extract the ZIP.
2. Run `install_windows.bat`.
3. The installer now tries Python 3.12, 3.11, 3.10, then any available `py`/`python` interpreter. If your version is older than 3.10, it warns but still continues.
4. After setup, run `run_windows.bat`.

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

- This model is large, so keep enough free disk space for the `.nemo` checkpoint plus cache files.
- If the GitHub NeMo install fails, the Windows installer tries a published-package fallback.
- `Apply text normalization` is intentionally optional because text-normalization availability can vary by environment.
- The app stores settings in `app_data/settings.json`.

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
