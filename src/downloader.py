from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from huggingface_hub import snapshot_download

from .constants import MODEL_FILENAME, MODEL_REPO_ID
from .file_utils import ensure_dir


def _repo_dir(cache_dir: str | Path) -> Path:
    return ensure_dir(cache_dir) / MODEL_REPO_ID.replace("/", "__")


def model_file_from_cache(cache_dir: str | Path) -> Optional[Path]:
    repo_dir = _repo_dir(cache_dir)
    candidate = repo_dir / MODEL_FILENAME
    if candidate.exists():
        return candidate
    matches = list(repo_dir.rglob(MODEL_FILENAME))
    return matches[0] if matches else None


def ensure_model_cached(cache_dir: str | Path, *, force_download: bool = False) -> Path:
    cache_dir = str(ensure_dir(cache_dir))
    repo_dir = _repo_dir(cache_dir)
    if not force_download:
        existing = model_file_from_cache(cache_dir)
        if existing:
            return existing

    os.environ.setdefault("HF_HOME", cache_dir)
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", cache_dir)
    snapshot_download(
        repo_id=MODEL_REPO_ID,
        local_dir=str(repo_dir),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    model_path = model_file_from_cache(cache_dir)
    if not model_path:
        raise FileNotFoundError(f"Could not find {MODEL_FILENAME} after download.")
    return model_path
