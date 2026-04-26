from __future__ import annotations

from pathlib import Path
from typing import Optional

from huggingface_hub import snapshot_download

from .constants import AUXILIARY_MODEL_REPO_IDS, MODEL_FILENAME, MODEL_REPO_ID
from .file_utils import ensure_dir
from .runtime_env import configure_runtime_environment


class OfflineCacheMissingError(FileNotFoundError):
    """Raised when offline mode is enabled but required cached files are missing."""


def _repo_dir(cache_dir: str | Path) -> Path:
    return ensure_dir(cache_dir) / MODEL_REPO_ID.replace("/", "__")


def model_file_from_cache(cache_dir: str | Path) -> Optional[Path]:
    repo_dir = _repo_dir(cache_dir)
    candidate = repo_dir / MODEL_FILENAME
    if candidate.exists():
        return candidate
    matches = list(repo_dir.rglob(MODEL_FILENAME))
    return matches[0] if matches else None


def _snapshot_download(repo_id: str, cache_dir: str | Path, *, local_dir: Path | None = None, offline_mode: bool = False) -> str:
    kwargs = {
        "repo_id": repo_id,
        "resume_download": True,
        "local_files_only": bool(offline_mode),
    }
    if local_dir is not None:
        kwargs["local_dir"] = str(local_dir)
        kwargs["local_dir_use_symlinks"] = False
    else:
        kwargs["cache_dir"] = str(cache_dir)
    return snapshot_download(**kwargs)


def ensure_model_cached(cache_dir: str | Path, *, force_download: bool = False, offline_mode: bool = False) -> Path:
    cache_dir = ensure_dir(cache_dir)
    configure_runtime_environment(cache_dir, offline_mode=offline_mode)
    repo_dir = _repo_dir(cache_dir)

    if not force_download:
        existing = model_file_from_cache(cache_dir)
        if existing:
            return existing

    if offline_mode:
        raise OfflineCacheMissingError(
            "Offline mode is enabled, but the main Magpie .nemo checkpoint is not present in the local cache. "
            "Disable offline mode once and run Download/check model, or pre-download the model before using offline mode."
        )

    _snapshot_download(MODEL_REPO_ID, cache_dir, local_dir=repo_dir, offline_mode=False)
    model_path = model_file_from_cache(cache_dir)
    if not model_path:
        raise FileNotFoundError(f"Could not find {MODEL_FILENAME} after download.")
    return model_path


def ensure_auxiliary_models_cached(cache_dir: str | Path, *, offline_mode: bool = False) -> list[str]:
    """Cache/check known auxiliary models used during Magpie restore/inference.

    Magpie/NeMo may load helper models such as WavLM, ByT5 and the NVIDIA nano codec
    through Hugging Face/Transformers during the first real model restore. Pre-caching
    them reduces first-run surprises and makes Settings -> Offline mode practical.
    """
    cache_dir = ensure_dir(cache_dir)
    configure_runtime_environment(cache_dir, offline_mode=offline_mode)
    resolved: list[str] = []
    for repo_id in AUXILIARY_MODEL_REPO_IDS:
        try:
            resolved.append(_snapshot_download(repo_id, cache_dir, offline_mode=offline_mode))
        except Exception as exc:
            if offline_mode:
                raise OfflineCacheMissingError(
                    f"Offline mode is enabled, but auxiliary model '{repo_id}' is not fully available in the local cache. "
                    "Disable offline mode once and run Download/check model before using offline mode."
                ) from exc
            raise
    return resolved


def ensure_all_model_files_cached(cache_dir: str | Path, *, offline_mode: bool = False) -> Path:
    model_path = ensure_model_cached(cache_dir, offline_mode=offline_mode)
    ensure_auxiliary_models_cached(cache_dir, offline_mode=offline_mode)
    return model_path
