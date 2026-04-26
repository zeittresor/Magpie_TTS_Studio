# Patch Notes v0.2.7

- Added an optional offline mode under Settings → General.
- Offline mode sets Hugging Face / Transformers local-files-only environment flags before Magpie loads.
- The app now configures HF/Transformers/NeMo cache paths at startup instead of only during generation.
- Download/check model now also pre-caches known auxiliary runtime models used by Magpie/NeMo:
  - `microsoft/wavlm-base-plus`
  - `google/byt5-small`
  - `nvidia/nemo-nano-codec-22khz-1.89kbps-21.5fps`
- In offline mode, missing cache files produce an explicit cache-missing error instead of silently attempting internet access.
- Telemetry/noise-reduction environment defaults were added for local desktop usage.
- README updated with an Offline mode section and integrated user-provided README changes.
