from __future__ import annotations

import traceback
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from .downloader import ensure_model_cached
from .tts_backend import GenerationRequest, MagpieBackend


class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    file_ready = pyqtSignal(str)


class DownloadWorker(QObject):
    def __init__(self, cache_dir: str) -> None:
        super().__init__()
        self.cache_dir = cache_dir
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.status.emit("download_started")
            model_path = ensure_model_cached(self.cache_dir)
            self.signals.file_ready.emit(str(model_path))
            self.signals.finished.emit(str(model_path))
        except Exception:
            self.signals.error.emit(traceback.format_exc())


class GenerateWorker(QObject):
    def __init__(self, backend: MagpieBackend, request: GenerationRequest) -> None:
        super().__init__()
        self.backend = backend
        self.request = request
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.status.emit("generation_started")
            output_path: Path = self.backend.generate(self.request)
            self.signals.file_ready.emit(str(output_path))
            self.signals.finished.emit(str(output_path))
        except Exception:
            self.signals.error.emit(traceback.format_exc())
