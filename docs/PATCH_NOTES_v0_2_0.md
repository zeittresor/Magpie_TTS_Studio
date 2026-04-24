# Patch notes v0.2.0

## Added

- Generation progress bar in the main window.
- Phase status updates for model loading, synthesis, post-processing and WAV saving.
- New `Audio effects` tab in the settings dialog.
- Optional WAV post-processing after TTS generation and before autoplay:
  - peak normalization
  - output gain
  - chorus
  - echo / delay
  - robot / vocoder-like coloration
  - tremolo
  - bitcrusher / lo-fi
  - pitch shift
  - speed factor
- `src/audio_effects.py` with dependency-light NumPy DSP helpers.

## Changed

- Version bumped to `0.2.0`.
- CUDA TF32 fast path is enabled where supported to improve inference speed on modern NVIDIA GPUs.
- The loaded Magpie model is now moved to the newly selected device instead of being stuck on the first device choice.
- Main-window voice summary now also shows whether effects are active.
- Settings dialog is split into `General` and `Audio effects` tabs to avoid an overly long single page.

## Notes

- The progress bar is phase-based because the Magpie/NeMo `do_tts` call does not expose fine-grained token/sample progress callbacks.
- The vocoder option is intentionally described as “vocoder-like”; it is a lightweight offline post-filter, not a full analysis/synthesis vocoder.
