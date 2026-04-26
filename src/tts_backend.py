from __future__ import annotations

import logging
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

import soundfile as sf

from .audio_effects import apply_audio_effects
from .constants import DEFAULT_SAMPLE_RATE, MODEL_REPO_ID, SPEAKERS
from .downloader import ensure_model_cached, model_file_from_cache
from .file_utils import ensure_dir
from .runtime_env import configure_runtime_environment

LOGGER = logging.getLogger(__name__)
ProgressCallback = Callable[[int, str], None]


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
    audio_effects: dict[str, Any] | None = None
    offline_mode: bool = False


class MagpieBackend:
    def __init__(self) -> None:
        self.model = None
        self.device = None
        self.sample_rate = DEFAULT_SAMPLE_RATE
        self.model_path: Optional[Path] = None
        self._loaded_device_choice: str | None = None

    def _resolve_device(self, wanted: str):
        import torch

        if wanted == "cuda":
            return torch.device("cuda")
        if wanted == "cpu":
            return torch.device("cpu")
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _configure_cache_environment(self, cache_dir: str | Path, offline_mode: bool = False) -> None:
        """Keep Magpie, Transformers and HF downloads inside the project cache when possible."""
        configure_runtime_environment(cache_dir, offline_mode=offline_mode)

    def _load_model_class(self):
        from nemo.collections.tts import models as nemo_tts_models

        model_cls = getattr(nemo_tts_models, "MagpieTTSModel", None)
        if model_cls is None:
            model_cls = getattr(nemo_tts_models, "MagpieTTS_Model", None)
        if model_cls is None:
            raise RuntimeError("Magpie TTS model class was not found in NeMo.")
        return model_cls

    def _embedding_compat_policy(self, checkpoint_rows: int, runtime_rows: int) -> tuple[bool, str]:
        """Return whether a row-count-only embedding drift is safe enough to adapt.

        NeMo and tokenizer packages can evolve independently from the released Magpie
        checkpoint. A future NeMo build may therefore create a text embedding with more
        or fewer vocabulary rows than the checkpoint contains. We can safely adapt the
        *row count* for inference as long as the embedding width stays unchanged. The
        guard below prevents accidentally hiding a completely unrelated checkpoint/model
        mismatch. Power users may override the limits with environment variables when
        testing newer NeMo releases.
        """
        row_delta = abs(int(checkpoint_rows) - int(runtime_rows))
        largest = max(int(checkpoint_rows), int(runtime_rows), 1)
        relative_delta = row_delta / largest

        max_delta = int(os.environ.get("MAGPIE_EMBEDDING_COMPAT_MAX_ROWS", "4096"))
        max_ratio = float(os.environ.get("MAGPIE_EMBEDDING_COMPAT_MAX_RATIO", "0.50"))

        if row_delta == 0:
            return False, "row count already matches"
        if row_delta <= max_delta and relative_delta <= max_ratio:
            return True, f"row_delta={row_delta}, relative_delta={relative_delta:.3f}"
        return False, (
            f"row_delta={row_delta}, relative_delta={relative_delta:.3f}, "
            f"limits=max_rows:{max_delta}, max_ratio:{max_ratio:.3f}"
        )

    @contextmanager
    def _temporary_embedding_compat_patch(self) -> Iterator[None]:
        """Adapt compatible Magpie embedding row-count drift while loading checkpoints.

        The patch is intentionally narrow:
        - only PyTorch Embedding weights are considered,
        - both tensors must be 2D,
        - the embedding width must be identical,
        - only the number of vocabulary rows may differ,
        - the drift must stay within configurable safety limits.

        When accepted, overlapping rows are copied from the checkpoint. Extra rows in a
        newer runtime embedding keep their runtime initialization. If a newer checkpoint
        has more rows than the runtime model, the extra checkpoint rows are ignored with
        a clear warning. Different embedding widths still fail normally.
        """
        if os.environ.get("MAGPIE_DISABLE_EMBEDDING_COMPAT_PATCH", "").strip().lower() in {"1", "true", "yes", "on"}:
            LOGGER.info("Magpie embedding compatibility patch is disabled by environment variable.")
            yield
            return

        import torch

        original_load_state_dict = torch.nn.Embedding.load_state_dict

        def patched_load_state_dict(module, state_dict, *args, **kwargs):  # type: ignore[no-untyped-def]
            try:
                incoming = state_dict.get("weight") if isinstance(state_dict, dict) else None
                target = getattr(module, "weight", None)
                if incoming is not None and target is not None:
                    same_rank = getattr(incoming, "ndim", None) == 2 and getattr(target, "ndim", None) == 2
                    if same_rank:
                        checkpoint_shape = tuple(int(x) for x in incoming.shape)
                        runtime_shape = tuple(int(x) for x in target.shape)
                        same_width = checkpoint_shape[1] == runtime_shape[1]
                        if same_width and checkpoint_shape[0] != runtime_shape[0]:
                            allowed, reason = self._embedding_compat_policy(checkpoint_shape[0], runtime_shape[0])
                            if allowed:
                                if checkpoint_shape[0] > runtime_shape[0]:
                                    LOGGER.warning(
                                        "Adapting Magpie embedding while loading: checkpoint=%s runtime=%s. "
                                        "The runtime model has fewer rows; extra checkpoint rows are ignored. %s",
                                        checkpoint_shape,
                                        runtime_shape,
                                        reason,
                                    )
                                else:
                                    LOGGER.warning(
                                        "Adapting Magpie embedding while loading: checkpoint=%s runtime=%s. "
                                        "Overlapping rows are copied; extra runtime rows keep initialization. %s",
                                        checkpoint_shape,
                                        runtime_shape,
                                        reason,
                                    )
                                fixed_weight = target.detach().clone()
                                rows_to_copy = min(checkpoint_shape[0], runtime_shape[0])
                                fixed_weight[:rows_to_copy, :] = incoming[:rows_to_copy, :].to(
                                    device=fixed_weight.device,
                                    dtype=fixed_weight.dtype,
                                )
                                state_dict = dict(state_dict)
                                state_dict["weight"] = fixed_weight
                            else:
                                LOGGER.error(
                                    "Refusing to adapt large Magpie embedding row-count mismatch: "
                                    "checkpoint=%s runtime=%s. %s",
                                    checkpoint_shape,
                                    runtime_shape,
                                    reason,
                                )
            except Exception:
                LOGGER.debug("Embedding compatibility patch could not adjust this state_dict entry.", exc_info=True)
            return original_load_state_dict(module, state_dict, *args, **kwargs)

        torch.nn.Embedding.load_state_dict = patched_load_state_dict  # type: ignore[assignment]
        try:
            yield
        finally:
            torch.nn.Embedding.load_state_dict = original_load_state_dict  # type: ignore[assignment]

    def _restore_from_local_nemo(self, model_cls, requested_device):
        if not self.model_path or not self.model_path.exists():
            raise FileNotFoundError("No local .nemo model file is available.")
        LOGGER.info("Loading Magpie from local .nemo file: %s", self.model_path)
        with self._temporary_embedding_compat_patch():
            try:
                return model_cls.restore_from(
                    restore_path=str(self.model_path),
                    map_location=requested_device,
                )
            except TypeError:
                return model_cls.restore_from(str(self.model_path))

    def _restore_from_hf_repo(self, model_cls):
        LOGGER.info("Falling back to Hugging Face repo id: %s", MODEL_REPO_ID)
        with self._temporary_embedding_compat_patch():
            return model_cls.from_pretrained(MODEL_REPO_ID)

    def ensure_loaded(self, cache_dir: str, device_choice: str, offline_mode: bool = False) -> None:
        requested_device = self._resolve_device(device_choice)
        if self.model is not None and self.device == requested_device:
            return

        import torch

        if self.model is not None and self.device != requested_device:
            LOGGER.info("Moving already loaded Magpie model from %s to %s", self.device, requested_device)
            self.model = self.model.to(requested_device)
            self.device = requested_device
            self._loaded_device_choice = device_choice
            return

        self._configure_cache_environment(cache_dir, offline_mode=offline_mode)

        # Helpful speed defaults on RTX/Ampere+ GPUs. Safe no-op on older hardware/CPU.
        if requested_device.type == "cuda":
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                torch.set_float32_matmul_precision("high")
            except Exception:
                LOGGER.debug("Could not enable CUDA TF32 fast path.", exc_info=True)

        self.model_path = ensure_model_cached(cache_dir, offline_mode=offline_mode)
        model_cls = self._load_model_class()
        self.device = requested_device

        try:
            self.model = self._restore_from_local_nemo(model_cls, requested_device)
        except Exception as local_error:
            LOGGER.warning("Local .nemo loading failed: %s", local_error)
            if offline_mode:
                raise RuntimeError(
                    "Offline mode is enabled and the local Magpie .nemo checkpoint could not be restored. "
                    "Disable offline mode once to refresh the cache, or inspect the local model file. "
                    f"Original error: {local_error}"
                ) from local_error
            self.model = self._restore_from_hf_repo(model_cls)

        if hasattr(self.model, "to"):
            self.model = self.model.to(self.device)
        if hasattr(self.model, "eval"):
            self.model.eval()

        self._loaded_device_choice = device_choice
        self.sample_rate = int(getattr(self.model, "sample_rate", DEFAULT_SAMPLE_RATE))
        LOGGER.info("Magpie model loaded on device %s with sample rate %s", self.device, self.sample_rate)

    def _safe_filename(self, template: str, language: str, speaker: str) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rendered = template.format(timestamp=timestamp, language=language, speaker=speaker)
        rendered = re.sub(r"[^A-Za-z0-9._-]+", "_", rendered).strip("._")
        if not rendered.lower().endswith(".wav"):
            rendered += ".wav"
        return rendered or f"magpie_{timestamp}.wav"

    def _emit_progress(self, callback: ProgressCallback | None, percent: int, code: str) -> None:
        if callback:
            if int(percent) < 0:
                callback(-1, code)
            else:
                callback(max(0, min(int(percent), 100)), code)

    def generate(self, request: GenerationRequest, progress_callback: ProgressCallback | None = None) -> Path:
        import numpy as np
        import torch

        if not request.text.strip():
            raise ValueError("Text is empty.")

        self._emit_progress(progress_callback, -1, "generation_loading_model")
        self.ensure_loaded(request.cache_dir, request.device, offline_mode=bool(request.offline_mode))
        self._emit_progress(progress_callback, 20, "generation_model_ready")

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

        self._emit_progress(progress_callback, 30, "generation_synthesizing")
        with torch.inference_mode():
            audio, _audio_len = self.model.do_tts(
                request.text.strip(),
                language=request.tts_language,
                apply_TN=apply_tn,
                speaker_index=speaker_index,
            )

        audio_np = audio.float().detach().cpu().numpy()
        audio_np = np.squeeze(audio_np).astype(np.float32, copy=False)
        self._emit_progress(progress_callback, 82, "generation_postprocessing")
        audio_np = apply_audio_effects(audio_np, self.sample_rate, request.audio_effects)

        self._emit_progress(progress_callback, 95, "generation_saving")
        sf.write(str(output_path), audio_np, self.sample_rate)
        self._emit_progress(progress_callback, 100, "generation_done")
        LOGGER.info("Saved audio to %s", output_path)
        return output_path

    def model_is_cached(self, cache_dir: str) -> bool:
        return model_file_from_cache(cache_dir) is not None
