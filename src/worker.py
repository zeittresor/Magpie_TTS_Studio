from __future__ import annotations

import traceback
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from .downloader import ensure_all_model_files_cached
from .tts_backend import GenerationRequest, MagpieBackend


class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    file_ready = pyqtSignal(str)


class DownloadWorker(QObject):
    def __init__(self, cache_dir: str, offline_mode: bool = False) -> None:
        super().__init__()
        self.cache_dir = cache_dir
        self.offline_mode = offline_mode
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            self.signals.status.emit("download_started")
            self.signals.progress.emit(0, "download_started")
            model_path = ensure_all_model_files_cached(self.cache_dir, offline_mode=self.offline_mode)
            self.signals.progress.emit(100, "download_done")
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

    def _progress(self, percent: int, code: str) -> None:
        self.signals.progress.emit(percent, code)
        self.signals.status.emit(code)

    def run(self) -> None:
        try:
            self.signals.status.emit("generation_started")
            self.signals.progress.emit(0, "generation_started")
            output_path: Path = self.backend.generate(self.request, progress_callback=self._progress)
            self.signals.file_ready.emit(str(output_path))
            self.signals.finished.emit(str(output_path))
        except Exception:
            self.signals.error.emit(traceback.format_exc())
