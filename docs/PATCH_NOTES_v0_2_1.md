# Magpie TTS Studio v0.2.1 patch notes

## Added

- Audio-effect preview controls in the `Audio effects` settings tab:
  - `Preview original` plays the bundled clean WAV unchanged.
  - `Preview current effects` renders the current effect settings to a temporary WAV and plays it immediately.
  - `Stop preview` stops preview playback.
- Bundled preview sample: `assets/audio/effect_preview_clean.wav`.
- Temporary effect previews are written to `app_data/preview/effect_preview_current.wav`.
- `install_windows.bat` now asks after setup whether the GUI should start immediately.
- If no choice is made within 10 seconds, the installer starts the GUI automatically.
- The installer attempts to minimize its console window before launching the GUI, without closing the console.
- `run_windows.bat` now also tries to minimize the console before starting the GUI.

## Fixed / improved

- The installer now treats missing `pynini` / `nemo_text_processing` as an optional Windows text-normalization limitation instead of blindly trying `pip install pynini`.
- Text normalization remains optional; the app also auto-disables `apply_TN` at generation time when `nemo_text_processing` is unavailable.
- The `Audio effects` tab is scrollable so the preview buttons and all effect controls remain reachable on smaller screens.
- The NeMo installation path was cleaned up to avoid duplicated install blocks and brittle fallback behavior.

## Notes

- The preview path deliberately uses a static clean WAV so you can hear effect differences quickly without waiting for Magpie inference.
- `Preview current effects` uses the current visible controls even before saving the dialog settings.
- Pynini is part of the NeMo text-normalization dependency chain. On native Windows it is commonly awkward or unavailable through normal pip installs; this does not prevent basic Magpie TTS synthesis with text normalization off.
