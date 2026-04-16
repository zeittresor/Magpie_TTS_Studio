from __future__ import annotations

import importlib
import json
import sys
import traceback


def main() -> int:
    result = {
        "ok": False,
        "missing_module": None,
        "error_type": None,
        "error": None,
        "magpie_class_found": False,
    }
    try:
        mod = importlib.import_module("nemo.collections.tts")
        models = getattr(mod, "models", None)
        if models is None:
            models = importlib.import_module("nemo.collections.tts.models")
        result["magpie_class_found"] = hasattr(models, "MagpieTTSModel") or hasattr(models, "MagpieTTS_Model")
        result["ok"] = bool(result["magpie_class_found"])
        if not result["ok"]:
            result["error_type"] = "RuntimeError"
            result["error"] = "Magpie TTS model class was not found in NeMo."
    except ModuleNotFoundError as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["missing_module"] = getattr(exc, "name", None)
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        tb = traceback.format_exc(limit=6)
        result["traceback"] = tb
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
