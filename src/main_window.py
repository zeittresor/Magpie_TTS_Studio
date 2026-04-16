from __future__ import annotations

import logging
import traceback
from pathlib import Path

from PyQt6.QtCore import QThread, QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .constants import APP_NAME, APP_VERSION, LANGUAGES
from .file_utils import ensure_dir, open_in_file_manager
from .options_dialog import OptionsDialog
from .settings_manager import SettingsManager
from .style import build_stylesheet
from .translations import tr
from .tts_backend import GenerationRequest, MagpieBackend
from .worker import DownloadWorker, GenerateWorker

LOGGER = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load()
        self.lang = self.settings.get("app_language", "en")
        self.backend = MagpieBackend()
        self.last_output_path: Path | None = None
        self.active_thread: QThread | None = None
        self.active_worker = None

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._build_ui()
        self.apply_settings_to_ui()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1100, 760)

        central = QWidget(self)
        root = QVBoxLayout(central)
        root.setSpacing(14)

        title = QLabel(APP_NAME)
        title.setObjectName("titleLabel")
        subtitle = QLabel("NVIDIA Magpie multilingual TTS desktop frontend")
        subtitle.setObjectName("subtitleLabel")
        root.addWidget(title)
        root.addWidget(subtitle)

        content = QGridLayout()
        content.setHorizontalSpacing(14)
        content.setVerticalSpacing(14)

        self.voice_box = QGroupBox()
        voice_layout = QVBoxLayout(self.voice_box)
        self.voice_summary = QLabel()
        self.voice_summary.setWordWrap(True)
        self.voice_button = QPushButton()
        self.voice_button.clicked.connect(self.open_options)
        voice_layout.addWidget(self.voice_summary)
        voice_layout.addWidget(self.voice_button)

        self.text_box = QGroupBox()
        text_layout = QVBoxLayout(self.text_box)
        self.text_label = QLabel()
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type or paste text here…")
        self.text_edit.setMinimumHeight(280)
        text_layout.addWidget(self.text_label)
        text_layout.addWidget(self.text_edit)

        self.output_box = QGroupBox()
        output_layout = QVBoxLayout(self.output_box)
        self.last_output_label = QLabel()
        self.last_output_label.setWordWrap(True)
        buttons_1 = QHBoxLayout()
        self.generate_button = QPushButton()
        self.generate_button.clicked.connect(self.generate_audio)
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.text_edit.clear)
        self.download_button = QPushButton()
        self.download_button.clicked.connect(self.download_model)
        buttons_1.addWidget(self.generate_button)
        buttons_1.addWidget(self.clear_button)
        buttons_1.addWidget(self.download_button)

        buttons_2 = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.clicked.connect(self.play_last_output)
        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self.player.stop)
        self.open_output_button = QPushButton()
        self.open_output_button.clicked.connect(lambda: open_in_file_manager(self.settings["output_dir"]))
        self.open_cache_button = QPushButton()
        self.open_cache_button.clicked.connect(lambda: open_in_file_manager(self.settings["cache_dir"]))
        buttons_2.addWidget(self.play_button)
        buttons_2.addWidget(self.stop_button)
        buttons_2.addWidget(self.open_output_button)
        buttons_2.addWidget(self.open_cache_button)

        output_layout.addWidget(self.last_output_label)
        output_layout.addLayout(buttons_1)
        output_layout.addLayout(buttons_2)

        self.log_box = QGroupBox()
        log_layout = QVBoxLayout(self.log_box)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(220)
        log_layout.addWidget(self.log_view)

        content.addWidget(self.voice_box, 0, 0)
        content.addWidget(self.output_box, 0, 1)
        content.addWidget(self.text_box, 1, 0, 1, 2)
        content.addWidget(self.log_box, 2, 0, 1, 2)

        root.addLayout(content)
        self.setCentralWidget(central)

        self._build_menu()
        self.statusBar().showMessage("Ready.")

    def _build_menu(self) -> None:
        menu_file = self.menuBar().addMenu("File")
        menu_help = self.menuBar().addMenu("Help")

        self.action_options = QAction("Settings", self)
        self.action_options.triggered.connect(self.open_options)
        menu_file.addAction(self.action_options)

        self.action_exit = QAction("Exit", self)
        self.action_exit.triggered.connect(self.close)
        menu_file.addAction(self.action_exit)

        self.action_about = QAction("About", self)
        self.action_about.triggered.connect(self.show_about)
        menu_help.addAction(self.action_about)

    def append_log(self, text: str) -> None:
        self.log_view.append(text)
        LOGGER.info(text)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(f"{tr(self.lang, 'app_title')} v{APP_VERSION}")
        self.voice_box.setTitle(tr(self.lang, "voice_section"))
        self.text_box.setTitle(tr(self.lang, "text_label"))
        self.output_box.setTitle(tr(self.lang, "output_section"))
        self.log_box.setTitle(tr(self.lang, "log_section"))
        self.text_label.setText(tr(self.lang, "text_label"))
        self.voice_button.setText(tr(self.lang, "open_options"))
        self.generate_button.setText(tr(self.lang, "generate"))
        self.clear_button.setText(tr(self.lang, "clear"))
        self.download_button.setText(tr(self.lang, "download"))
        self.play_button.setText(tr(self.lang, "play_last"))
        self.stop_button.setText(tr(self.lang, "stop_audio"))
        self.open_output_button.setText(tr(self.lang, "open_output"))
        self.open_cache_button.setText(tr(self.lang, "open_cache"))
        self.action_options.setText(tr(self.lang, "menu_options"))
        self.action_about.setText(tr(self.lang, "menu_about"))
        self.action_exit.setText(tr(self.lang, "exit"))
        self.menuBar().actions()[0].setText(tr(self.lang, "file"))
        self.menuBar().actions()[1].setText(tr(self.lang, "help"))
        self._refresh_voice_summary()
        self._refresh_last_output_label()
        self.statusBar().showMessage(tr(self.lang, "status_ready"))

    def _refresh_voice_summary(self) -> None:
        self.voice_summary.setText(
            f"{tr(self.lang, 'app_language')}: {LANGUAGES.get(self.settings['app_language'], self.settings['app_language'])}\n"
            f"{tr(self.lang, 'tts_language')}: {LANGUAGES.get(self.settings['tts_language'], self.settings['tts_language'])}\n"
            f"{tr(self.lang, 'speaker')}: {self.settings['speaker']}\n"
            f"{tr(self.lang, 'device')}: {self.settings['device']}"
        )

    def _refresh_last_output_label(self) -> None:
        if self.last_output_path and self.last_output_path.exists():
            self.last_output_label.setText(f"{tr(self.lang, 'last_output')}:\n{self.last_output_path}")
        else:
            self.last_output_label.setText(tr(self.lang, "no_output_yet"))

    def apply_settings_to_ui(self) -> None:
        self.lang = self.settings.get("app_language", "en")
        ensure_dir(self.settings["output_dir"])
        ensure_dir(self.settings["cache_dir"])
        self.text_edit.setPlainText(self.settings.get("last_text", ""))
        self.setStyleSheet(build_stylesheet(self.settings.get("theme", "dark")))
        self.retranslate_ui()

    def show_about(self) -> None:
        QMessageBox.information(self, tr(self.lang, "info"), tr(self.lang, "about_text"))

    def open_options(self) -> None:
        dialog = OptionsDialog(self.settings, self)
        if dialog.exec():
            self.settings.update(dialog.get_settings())
            self.settings["last_text"] = self.text_edit.toPlainText()
            self.settings_manager.save(self.settings)
            self.apply_settings_to_ui()
            self.append_log(tr(self.lang, "app_restart_note"))

    def _set_busy(self, busy: bool, status_text: str | None = None) -> None:
        self.generate_button.setEnabled(not busy)
        self.download_button.setEnabled(not busy)
        self.voice_button.setEnabled(not busy)
        if status_text:
            self.statusBar().showMessage(status_text)

    def _start_worker(self, worker) -> None:
        self.active_thread = QThread(self)
        self.active_worker = worker
        worker.moveToThread(self.active_thread)
        self.active_thread.started.connect(worker.run)
        worker.signals.finished.connect(self._worker_finished)
        worker.signals.error.connect(self._worker_error)
        worker.signals.file_ready.connect(self._worker_file_ready)
        worker.signals.status.connect(self._worker_status)
        worker.signals.finished.connect(self.active_thread.quit)
        worker.signals.error.connect(self.active_thread.quit)
        self.active_thread.finished.connect(self.active_thread.deleteLater)
        self.active_thread.start()

    def _worker_status(self, code: str) -> None:
        mapping = {
            "download_started": tr(self.lang, "status_downloading"),
            "generation_started": tr(self.lang, "status_generating"),
        }
        self.statusBar().showMessage(mapping.get(code, tr(self.lang, "status_ready")))

    def _worker_file_ready(self, path_str: str) -> None:
        path = Path(path_str)
        if path.suffix.lower() == ".wav":
            self.last_output_path = path
            self._refresh_last_output_label()

    def _worker_finished(self, result: str) -> None:
        self._set_busy(False, tr(self.lang, "status_done"))
        if result.lower().endswith(".wav"):
            self.append_log(f"{tr(self.lang, 'generation_complete')} {result}")
            if self.settings.get("autoplay", True):
                self.play_last_output()
        else:
            self.append_log(f"{tr(self.lang, 'download_complete')} {result}")

    def _worker_error(self, details: str) -> None:
        self._set_busy(False, tr(self.lang, "status_error"))
        self.append_log(details)
        QMessageBox.critical(self, tr(self.lang, "error"), details)

    def download_model(self) -> None:
        self.settings["last_text"] = self.text_edit.toPlainText()
        self.settings_manager.save(self.settings)
        self._set_busy(True, tr(self.lang, "status_downloading"))
        worker = DownloadWorker(self.settings["cache_dir"])
        self._start_worker(worker)

    def generate_audio(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, tr(self.lang, "warning"), tr(self.lang, "text_label"))
            return
        self.settings["last_text"] = text
        self.settings_manager.save(self.settings)
        request = GenerationRequest(
            text=text,
            tts_language=self.settings["tts_language"],
            speaker=self.settings["speaker"],
            device=self.settings["device"],
            apply_text_normalization=bool(self.settings.get("apply_text_normalization", False)),
            output_dir=self.settings["output_dir"],
            cache_dir=self.settings["cache_dir"],
            filename_template=self.settings["filename_template"],
            save_output_copy=bool(self.settings.get("save_output_copy", True)),
        )
        self._set_busy(True, tr(self.lang, "status_generating"))
        worker = GenerateWorker(self.backend, request)
        self._start_worker(worker)

    def play_last_output(self) -> None:
        if not self.last_output_path or not self.last_output_path.exists():
            QMessageBox.information(self, tr(self.lang, "info"), tr(self.lang, "no_output_yet"))
            return
        self.player.setSource(QUrl.fromLocalFile(str(self.last_output_path)))
        self.player.play()
        self.statusBar().showMessage(f"{tr(self.lang, 'preview_section')}: {self.last_output_path.name}")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.settings["last_text"] = self.text_edit.toPlainText()
        self.settings_manager.save(self.settings)
        super().closeEvent(event)
