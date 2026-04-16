from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import soundfile as sf

from .constants import DEFAULT_SAMPLE_RATE, MODEL_REPO_ID, SPEAKERS
from .downloader import ensure_model_cached, model_file_from_cache
from .file_utils import ensure_dir

LOGGER = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    text: str
    tts_language: str
    speaker: str
    device: str
    apply_text_normalization: bool
    output_dir: str
    cache_dir: str
    filename_template: str
    save_output_copy: bool


class MagpieBackend:
    def __init__(self) -> None:
        self.model = None
        self.device = None
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.model_path: Optional[Path] = None

    def _resolve_device(self, wanted: str):
        import torch

        if wanted == "cuda":
            return torch.device("cuda")
        if wanted == "cpu":
            return torch.device("cpu")
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_model_class(self):
        from nemo.collections.tts import models as nemo_tts_models

        model_cls = getattr(nemo_tts_models, "MagpieTTSModel", None)
        if model_cls is None:
            model_cls = getattr(nemo_tts_models, "MagpieTTS_Model", None)
        if model_cls is None:
            raise RuntimeError("Magpie TTS model class was not found in NeMo.")
        return model_cls

    def ensure_loaded(self, cache_dir: str, device_choice: str) -> None:
        if self.model is not None:
            return

        import os

        os.environ.setdefault("HF_HOME", cache_dir)
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", cache_dir)
        os.environ.setdefault("NEMO_CACHE_DIR", cache_dir)

        self.model_path = ensure_model_cached(cache_dir)
        model_cls = self._load_model_class()
        self.device = self._resolve_device(device_choice)

        repo_or_path = str(self.model_path.parent) if self.model_path else MODEL_REPO_ID
        try:
            LOGGER.info("Loading Magpie from local snapshot: %s", repo_or_path)
            self.model = model_cls.from_pretrained(repo_or_path)
        except Exception as first_error:
            LOGGER.warning("Local snapshot loading failed: %s", first_error)
            LOGGER.info("Falling back to Hugging Face repo id: %s", MODEL_REPO_ID)
            self.model = model_cls.from_pretrained(MODEL_REPO_ID)

        if hasattr(self.model, "to"):
            self.model = self.model.to(self.device)
        if hasattr(self.model, "eval"):
            self.model.eval()

        self.sample_rate = int(getattr(self.model, "sample_rate", DEFAULT_SAMPLE_RATE))
        LOGGER.info("Magpie model loaded on device %s with sample rate %s", self.device, self.sample_rate)

    def _safe_filename(self, template: str, language: str, speaker: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rendered = template.format(timestamp=timestamp, language=language, speaker=speaker)
        rendered = re.sub(r"[^A-Za-z0-9._-]+", "_", rendered).strip("._")
        if not rendered.lower().endswith(".wav"):
            rendered += ".wav"
        return rendered or f"magpie_{timestamp}.wav"

    def generate(self, request: GenerationRequest) -> Path:
        import numpy as np
        import torch

        if not request.text.strip():
            raise ValueError("Text is empty.")

        self.ensure_loaded(request.cache_dir, request.device)
        speaker_index = SPEAKERS[request.speaker]

        if request.save_output_copy:
            output_dir = ensure_dir(request.output_dir)
            output_path = output_dir / self._safe_filename(request.filename_template, request.tts_language, request.speaker)
        else:
            preview_dir = ensure_dir(Path(request.cache_dir) / "preview_audio")
            output_path = preview_dir / "last_preview.wav"

        apply_tn = bool(request.apply_text_normalization)
        if apply_tn:
            try:
                import nemo_text_processing  # noqa: F401
            except Exception as exc:
                LOGGER.warning(
                    "Text normalization was requested, but nemo_text_processing is not available. "
                    "Proceeding with apply_TN=False. Details: %s",
                    exc,
                )
                apply_tn = False

        with torch.no_grad():
            audio, _audio_len = self.model.do_tts(
                request.text.strip(),
                language=request.tts_language,
                apply_TN=apply_tn,
                speaker_index=speaker_index,
            )

        audio_np = audio.float().detach().cpu().numpy()
        audio_np = np.squeeze(audio_np)
        sf.write(str(output_path), audio_np, self.sample_rate)
        LOGGER.info("Saved audio to %s", output_path)
        return output_path

    def model_is_cached(self, cache_dir: str) -> bool:
        return model_file_from_cache(cache_dir) is not None
