from __future__ import annotations

import json
import sys


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "import_check.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    missing = (data.get("missing_module") or "").strip()
    if not missing:
        print("__none__")
        return 0

    root = missing.split(".")[0]

    # Windows note:
    # nemo_text_processing pulls in Pynini/OpenFST. That dependency chain is not a
    # normal pip-installable Windows runtime dependency and is only required for
    # NeMo text normalization. Magpie inference can run with apply_TN=False, so the
    # installer should warn and continue instead of trying `pip install pynini`.
    optional_windows_tn_modules = {"pynini", "nemo_text_processing"}
    if root in optional_windows_tn_modules:
        print("__optional_windows_text_normalization__")
        return 0

    mapping = {
        "nv_one_logger": "nv-one-logger-pytorch-lightning-integration>=2.3.1",
        "wandb": "wandb>=0.17",
        "lightning": "lightning>2.2.1,<=2.4.0",
        "kaldialign": "kaldialign",
        "nemo_run": "nemo-run",
        "megatron": "megatron-core",
        "transformer_engine": "transformer-engine",
    }
    package = mapping.get(root)
    if not package:
        if root.replace("_", "").isalnum():
            package = root
        else:
            print("__unknown__")
            return 0
    print(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
