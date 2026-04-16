from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .constants import DEFAULT_SETTINGS, DEVICE_OPTIONS, LANGUAGES, SPEAKERS
from .translations import tr


class OptionsDialog(QDialog):
    def __init__(self, settings: dict, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings.copy()
        self.lang = self.settings.get("app_language", "en")
        self.setMinimumWidth(560)
        self._build_ui()
        self._load_values()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.form.setVerticalSpacing(10)

        self.app_language_combo = QComboBox()
        self.tts_language_combo = QComboBox()
        self.speaker_combo = QComboBox()
        self.device_combo = QComboBox()
        self.theme_combo = QComboBox()
        self.output_dir_edit = QLineEdit()
        self.cache_dir_edit = QLineEdit()
        self.filename_template_edit = QLineEdit()
        self.apply_tn_check = QCheckBox()
        self.autoplay_check = QCheckBox()
        self.save_copy_check = QCheckBox()

        for code, name in LANGUAGES.items():
            self.app_language_combo.addItem(name, code)
            self.tts_language_combo.addItem(name, code)

        for speaker in SPEAKERS:
            self.speaker_combo.addItem(speaker, speaker)

        for device in DEVICE_OPTIONS:
            self.device_combo.addItem(device, device)

        self.theme_combo.addItem("dark", "dark")
        self.theme_combo.addItem("light", "light")

        self.app_language_combo.currentIndexChanged.connect(self.retranslate_ui)

        self.output_browse = QPushButton()
        self.output_browse.clicked.connect(self._browse_output)
        self.cache_browse = QPushButton()
        self.cache_browse.clicked.connect(self._browse_cache)

        output_wrap = QWidget()
        output_row = QHBoxLayout(output_wrap)
        output_row.setContentsMargins(0, 0, 0, 0)
        output_row.addWidget(self.output_dir_edit)
        output_row.addWidget(self.output_browse)

        cache_wrap = QWidget()
        cache_row = QHBoxLayout(cache_wrap)
        cache_row.setContentsMargins(0, 0, 0, 0)
        cache_row.addWidget(self.cache_dir_edit)
        cache_row.addWidget(self.cache_browse)

        self.label_app_language = QLabel()
        self.label_tts_language = QLabel()
        self.label_speaker = QLabel()
        self.label_device = QLabel()
        self.label_theme = QLabel()
        self.label_filename_template = QLabel()
        self.label_output_dir = QLabel()
        self.label_cache_dir = QLabel()

        self.form.addRow(self.label_app_language, self.app_language_combo)
        self.form.addRow(self.label_tts_language, self.tts_language_combo)
        self.form.addRow(self.label_speaker, self.speaker_combo)
        self.form.addRow(self.label_device, self.device_combo)
        self.form.addRow(self.label_theme, self.theme_combo)
        self.form.addRow(QLabel(""), self.apply_tn_check)
        self.form.addRow(QLabel(""), self.autoplay_check)
        self.form.addRow(QLabel(""), self.save_copy_check)
        self.form.addRow(self.label_filename_template, self.filename_template_edit)
        self.form.addRow(self.label_output_dir, output_wrap)
        self.form.addRow(self.label_cache_dir, cache_wrap)
        self.layout.addLayout(self.form)

        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.layout.addWidget(self.hint_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.reset_button = QPushButton()
        self.button_box.addButton(self.reset_button, QDialogButtonBox.ButtonRole.ResetRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.reset_button.clicked.connect(self._reset_defaults)
        self.layout.addWidget(self.button_box)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr(self.lang, "select_output_dir"), self.output_dir_edit.text())
        if path:
            self.output_dir_edit.setText(path)

    def _browse_cache(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr(self.lang, "select_cache_dir"), self.cache_dir_edit.text())
        if path:
            self.cache_dir_edit.setText(path)

    def _reset_defaults(self) -> None:
        self.settings = DEFAULT_SETTINGS.copy()
        self._load_values()
        self.retranslate_ui()

    def _set_combo_by_data(self, combo: QComboBox, value: str) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _load_values(self) -> None:
        self._set_combo_by_data(self.app_language_combo, self.settings.get("app_language", "en"))
        self._set_combo_by_data(self.tts_language_combo, self.settings.get("tts_language", "en"))
        self._set_combo_by_data(self.speaker_combo, self.settings.get("speaker", "Sofia"))
        self._set_combo_by_data(self.device_combo, self.settings.get("device", "auto"))
        self._set_combo_by_data(self.theme_combo, self.settings.get("theme", "dark"))
        self.output_dir_edit.setText(self.settings.get("output_dir", ""))
        self.cache_dir_edit.setText(self.settings.get("cache_dir", ""))
        self.filename_template_edit.setText(self.settings.get("filename_template", DEFAULT_SETTINGS["filename_template"]))
        self.apply_tn_check.setChecked(bool(self.settings.get("apply_text_normalization", False)))
        self.autoplay_check.setChecked(bool(self.settings.get("autoplay", True)))
        self.save_copy_check.setChecked(bool(self.settings.get("save_output_copy", True)))
        self.lang = self.app_language_combo.currentData() or "en"

    def retranslate_ui(self) -> None:
        self.lang = self.app_language_combo.currentData() or self.lang
        self.setWindowTitle(tr(self.lang, "options_title"))
        self.output_browse.setText(tr(self.lang, "browse"))
        self.cache_browse.setText(tr(self.lang, "browse"))
        self.reset_button.setText(tr(self.lang, "reset_defaults"))
        self.apply_tn_check.setText(tr(self.lang, "text_normalization"))
        self.autoplay_check.setText(tr(self.lang, "autoplay"))
        self.save_copy_check.setText(tr(self.lang, "save_output_copy"))
        self.label_app_language.setText(tr(self.lang, "app_language"))
        self.label_tts_language.setText(tr(self.lang, "tts_language"))
        self.label_speaker.setText(tr(self.lang, "speaker"))
        self.label_device.setText(tr(self.lang, "device"))
        self.label_theme.setText(tr(self.lang, "theme"))
        self.label_filename_template.setText(tr(self.lang, "filename_template"))
        self.label_output_dir.setText(tr(self.lang, "output_folder"))
        self.label_cache_dir.setText(tr(self.lang, "cache_folder"))
        self.hint_label.setText(
            f"• {tr(self.lang, 'offline_hint')}\n• {tr(self.lang, 'device_auto_hint')}\n• {tr(self.lang, 'app_restart_note')}"
        )

    def get_settings(self) -> dict:
        return {
            "app_language": self.app_language_combo.currentData(),
            "tts_language": self.tts_language_combo.currentData(),
            "speaker": self.speaker_combo.currentData(),
            "device": self.device_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "output_dir": self.output_dir_edit.text().strip(),
            "cache_dir": self.cache_dir_edit.text().strip(),
            "filename_template": self.filename_template_edit.text().strip() or DEFAULT_SETTINGS["filename_template"],
            "apply_text_normalization": self.apply_tn_check.isChecked(),
            "autoplay": self.autoplay_check.isChecked(),
            "save_output_copy": self.save_copy_check.isChecked(),
        }
