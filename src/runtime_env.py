from __future__ import annotations

import logging
import os
from pathlib import Path

from .file_utils import ensure_dir

LOGGER = logging.getLogger(__name__)

OFFLINE_ENV_KEYS = (
    "HF_HUB_OFFLINE",
    "TRANSFORMERS_OFFLINE",
    "HF_DATASETS_OFFLINE",
)

TELEMETRY_ENV_DEFAULTS = {
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "DO_NOT_TRACK": "1",
    "WANDB_DISABLED": "true",
    "TOKENIZERS_PARALLELISM": "false",
    # NeMo/Lightning/W&B integrations vary by release; these are harmless no-ops
    # when unsupported and help to keep local desktop usage quiet.
    "NEMO_DISABLE_TELEMETRY": "1",
    "ANONYMIZED_TELEMETRY": "False",
}


def configure_runtime_environment(cache_dir: str | Path, offline_mode: bool = False) -> None:
    """Configure cache, telemetry and optional offline flags for HF/Transformers/NeMo.

    The app can run without network access after all model files and auxiliary runtime
    models have been cached. In offline mode, Hugging Face Hub and Transformers are
    forced into local-files-only behavior so failed HEAD/API requests cannot break a
    working local setup.
    """
    cache_path = str(ensure_dir(cache_dir))

    os.environ["HF_HOME"] = cache_path
    os.environ["HUGGINGFACE_HUB_CACHE"] = cache_path
    os.environ["TRANSFORMERS_CACHE"] = cache_path
    os.environ["NEMO_CACHE_DIR"] = cache_path

    for key, value in TELEMETRY_ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)

    if offline_mode:
        for key in OFFLINE_ENV_KEYS:
            os.environ[key] = "1"
        LOGGER.info("Offline mode enabled. HF/Transformers will use local cache only: %s", cache_path)
    else:
        # Allow switching back to online mode within the same GUI process.
        for key in OFFLINE_ENV_KEYS:
            if os.environ.get(key) == "1":
                os.environ.pop(key, None)
        LOGGER.info("Offline mode disabled. Cache path: %s", cache_path)
