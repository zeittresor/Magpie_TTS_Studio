# Patch Notes v0.2.8

## Added

- Added a one-time automatic first-GUI-start `Download/check model` run.
- Added APIPA/link-local detection so the automatic check is skipped when the machine has no normal network IP.
- Added Settings → General option: `Run Download/check model automatically on first start`.
- Added `src/network_utils.py` for local IP detection without contacting a web service.

## Behavior

- The auto-check only runs when offline mode is disabled.
- It only marks itself complete after a successful model/cache check.
- Manual `Download/check model` remains available and also marks the first-start check as satisfied after success.

## Changed

- Updated README with first-start model check documentation.
- Updated installer text to mention the GUI-side first-start cache check.
- Version bumped to 0.2.8.
