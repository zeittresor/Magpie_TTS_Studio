from __future__ import annotations

import traceback
from pathlib import Path

import soundfile as sf
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .audio_effects import apply_audio_effects
from .constants import DEFAULT_SETTINGS, DEVICE_OPTIONS, LANGUAGES, PREVIEW_DIR, PREVIEW_SAMPLE_PATH, SPEAKERS
from .file_utils import ensure_dir
from .translations import tr


class OptionsDialog(QDialog):
    def __init__(self, settings: dict, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings.copy()
        self.lang = self.settings.get("app_language", "en")
        self.preview_player = QMediaPlayer(self)
        self.preview_audio_output = QAudioOutput(self)
        self.preview_player.setAudioOutput(self.preview_audio_output)
        self.setMinimumWidth(720)
        self.resize(820, 820)
        self._build_ui()
        self._load_values()
        self.retranslate_ui()

    def _build_ui(self) -> None:
        self.layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.general_tab = QWidget()
        self.audio_tab = QWidget()
        self.tabs.addTab(self.general_tab, "")
        self.tabs.addTab(self.audio_tab, "")
        self.layout.addWidget(self.tabs)

        self._build_general_tab()
        self._build_audio_tab()

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

    def _build_general_tab(self) -> None:
        tab_layout = QVBoxLayout(self.general_tab)
        self.form = QFormLayout()
        self.form.setVerticalSpacing(10)
        tab_layout.addLayout(self.form)
        tab_layout.addStretch(1)

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

    def _build_audio_tab(self) -> None:
        outer_layout = QVBoxLayout(self.audio_tab)
        scroll = QScrollArea(self.audio_tab)
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        scroll_container = QWidget()
        scroll.setWidget(scroll_container)
        tab_layout = QVBoxLayout(scroll_container)

        self.effects_box = QGroupBox()
        self.effects_form = QFormLayout(self.effects_box)
        self.effects_form.setVerticalSpacing(10)
        tab_layout.addWidget(self.effects_box)
        tab_layout.addStretch(1)

        self.audio_effects_enabled_check = QCheckBox()
        self.normalize_audio_check = QCheckBox()
        self.chorus_enabled_check = QCheckBox()
        self.echo_enabled_check = QCheckBox()
        self.robot_enabled_check = QCheckBox()
        self.tremolo_enabled_check = QCheckBox()
        self.bitcrusher_enabled_check = QCheckBox()

        self.normalize_target_spin = self._double_spin(-12.0, 0.0, 0.1, " dB")
        self.output_gain_spin = self._double_spin(-24.0, 12.0, 0.5, " dB")
        self.chorus_mix_spin = self._spin(0, 100, 1, " %")
        self.chorus_depth_spin = self._double_spin(0.0, 40.0, 0.5, " ms")
        self.chorus_rate_spin = self._double_spin(0.05, 8.0, 0.05, " Hz")
        self.echo_delay_spin = self._spin(20, 1200, 10, " ms")
        self.echo_decay_spin = self._spin(0, 95, 1, " %")
        self.robot_carrier_spin = self._double_spin(20.0, 420.0, 1.0, " Hz")
        self.robot_mix_spin = self._spin(0, 100, 1, " %")
        self.tremolo_rate_spin = self._double_spin(0.1, 25.0, 0.1, " Hz")
        self.tremolo_depth_spin = self._spin(0, 100, 1, " %")
        self.bitcrusher_bits_spin = self._spin(4, 16, 1, " bit")
        self.bitcrusher_hold_spin = self._spin(1, 32, 1, " samples")
        self.pitch_shift_spin = self._double_spin(-12.0, 12.0, 0.1, " st")
        self.speed_factor_spin = self._double_spin(0.5, 2.0, 0.01, "×")

        self.preview_original_button = QPushButton()
        self.preview_effects_button = QPushButton()
        self.stop_preview_button = QPushButton()
        self.preview_original_button.clicked.connect(lambda: self._play_effect_preview(False))
        self.preview_effects_button.clicked.connect(lambda: self._play_effect_preview(True))
        self.stop_preview_button.clicked.connect(self.preview_player.stop)
        preview_wrap = QWidget()
        preview_row = QHBoxLayout(preview_wrap)
        preview_row.setContentsMargins(0, 0, 0, 0)
        preview_row.addWidget(self.preview_original_button)
        preview_row.addWidget(self.preview_effects_button)
        preview_row.addWidget(self.stop_preview_button)

        self.label_preview_controls = QLabel()
        self.label_normalize_target = QLabel()
        self.label_output_gain = QLabel()
        self.label_chorus_mix = QLabel()
        self.label_chorus_depth = QLabel()
        self.label_chorus_rate = QLabel()
        self.label_echo_delay = QLabel()
        self.label_echo_decay = QLabel()
        self.label_robot_carrier = QLabel()
        self.label_robot_mix = QLabel()
        self.label_tremolo_rate = QLabel()
        self.label_tremolo_depth = QLabel()
        self.label_bitcrusher_bits = QLabel()
        self.label_bitcrusher_hold = QLabel()
        self.label_pitch_shift = QLabel()
        self.label_speed_factor = QLabel()

        self.effects_form.addRow(self.label_preview_controls, preview_wrap)
        self.effects_form.addRow(QLabel(""), self.audio_effects_enabled_check)
        self.effects_form.addRow(QLabel(""), self.normalize_audio_check)
        self.effects_form.addRow(self.label_normalize_target, self.normalize_target_spin)
        self.effects_form.addRow(self.label_output_gain, self.output_gain_spin)
        self.effects_form.addRow(QLabel(""), self.chorus_enabled_check)
        self.effects_form.addRow(self.label_chorus_mix, self.chorus_mix_spin)
        self.effects_form.addRow(self.label_chorus_depth, self.chorus_depth_spin)
        self.effects_form.addRow(self.label_chorus_rate, self.chorus_rate_spin)
        self.effects_form.addRow(QLabel(""), self.echo_enabled_check)
        self.effects_form.addRow(self.label_echo_delay, self.echo_delay_spin)
        self.effects_form.addRow(self.label_echo_decay, self.echo_decay_spin)
        self.effects_form.addRow(QLabel(""), self.robot_enabled_check)
        self.effects_form.addRow(self.label_robot_carrier, self.robot_carrier_spin)
        self.effects_form.addRow(self.label_robot_mix, self.robot_mix_spin)
        self.effects_form.addRow(QLabel(""), self.tremolo_enabled_check)
        self.effects_form.addRow(self.label_tremolo_rate, self.tremolo_rate_spin)
        self.effects_form.addRow(self.label_tremolo_depth, self.tremolo_depth_spin)
        self.effects_form.addRow(QLabel(""), self.bitcrusher_enabled_check)
        self.effects_form.addRow(self.label_bitcrusher_bits, self.bitcrusher_bits_spin)
        self.effects_form.addRow(self.label_bitcrusher_hold, self.bitcrusher_hold_spin)
        self.effects_form.addRow(self.label_pitch_shift, self.pitch_shift_spin)
        self.effects_form.addRow(self.label_speed_factor, self.speed_factor_spin)

    def _spin(self, minimum: int, maximum: int, step: int, suffix: str = "") -> QSpinBox:
        widget = QSpinBox()
        widget.setRange(minimum, maximum)
        widget.setSingleStep(step)
        widget.setSuffix(suffix)
        return widget

    def _double_spin(self, minimum: float, maximum: float, step: float, suffix: str = "") -> QDoubleSpinBox:
        widget = QDoubleSpinBox()
        widget.setRange(minimum, maximum)
        widget.setSingleStep(step)
        widget.setDecimals(2)
        widget.setSuffix(suffix)
        return widget

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

        self.audio_effects_enabled_check.setChecked(bool(self.settings.get("audio_effects_enabled", False)))
        self.normalize_audio_check.setChecked(bool(self.settings.get("normalize_audio", True)))
        self.normalize_target_spin.setValue(float(self.settings.get("normalize_target_db", -1.0)))
        self.output_gain_spin.setValue(float(self.settings.get("output_gain_db", 0.0)))
        self.chorus_enabled_check.setChecked(bool(self.settings.get("chorus_enabled", False)))
        self.chorus_mix_spin.setValue(int(round(float(self.settings.get("chorus_mix", 0.35)) * 100)))
        self.chorus_depth_spin.setValue(float(self.settings.get("chorus_depth_ms", 8.0)))
        self.chorus_rate_spin.setValue(float(self.settings.get("chorus_rate_hz", 0.28)))
        self.echo_enabled_check.setChecked(bool(self.settings.get("echo_enabled", False)))
        self.echo_delay_spin.setValue(int(self.settings.get("echo_delay_ms", 220)))
        self.echo_decay_spin.setValue(int(round(float(self.settings.get("echo_decay", 0.28)) * 100)))
        self.robot_enabled_check.setChecked(bool(self.settings.get("robot_enabled", False)))
        self.robot_carrier_spin.setValue(float(self.settings.get("robot_carrier_hz", 90.0)))
        self.robot_mix_spin.setValue(int(round(float(self.settings.get("robot_mix", 0.65)) * 100)))
        self.tremolo_enabled_check.setChecked(bool(self.settings.get("tremolo_enabled", False)))
        self.tremolo_rate_spin.setValue(float(self.settings.get("tremolo_rate_hz", 5.0)))
        self.tremolo_depth_spin.setValue(int(round(float(self.settings.get("tremolo_depth", 0.45)) * 100)))
        self.bitcrusher_enabled_check.setChecked(bool(self.settings.get("bitcrusher_enabled", False)))
        self.bitcrusher_bits_spin.setValue(int(self.settings.get("bitcrusher_bits", 10)))
        self.bitcrusher_hold_spin.setValue(int(self.settings.get("bitcrusher_hold", 1)))
        self.pitch_shift_spin.setValue(float(self.settings.get("pitch_shift_semitones", 0.0)))
        self.speed_factor_spin.setValue(float(self.settings.get("speed_factor", 1.0)))
        self.lang = self.app_language_combo.currentData() or "en"

    def retranslate_ui(self) -> None:
        self.lang = self.app_language_combo.currentData() or self.lang
        self.setWindowTitle(tr(self.lang, "options_title"))
        self.tabs.setTabText(0, tr(self.lang, "general_tab"))
        self.tabs.setTabText(1, tr(self.lang, "audio_effects_tab"))
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

        self.effects_box.setTitle(tr(self.lang, "audio_effects_section"))
        self.audio_effects_enabled_check.setText(tr(self.lang, "enable_audio_effects"))
        self.normalize_audio_check.setText(tr(self.lang, "normalize_audio"))
        self.chorus_enabled_check.setText(tr(self.lang, "chorus_enabled"))
        self.echo_enabled_check.setText(tr(self.lang, "echo_enabled"))
        self.robot_enabled_check.setText(tr(self.lang, "robot_enabled"))
        self.tremolo_enabled_check.setText(tr(self.lang, "tremolo_enabled"))
        self.bitcrusher_enabled_check.setText(tr(self.lang, "bitcrusher_enabled"))
        self.label_preview_controls.setText(tr(self.lang, "effect_preview_controls"))
        self.preview_original_button.setText(tr(self.lang, "preview_original"))
        self.preview_effects_button.setText(tr(self.lang, "preview_effects"))
        self.stop_preview_button.setText(tr(self.lang, "stop_preview"))
        self.label_normalize_target.setText(tr(self.lang, "normalize_target_db"))
        self.label_output_gain.setText(tr(self.lang, "output_gain_db"))
        self.label_chorus_mix.setText(tr(self.lang, "chorus_mix"))
        self.label_chorus_depth.setText(tr(self.lang, "chorus_depth_ms"))
        self.label_chorus_rate.setText(tr(self.lang, "chorus_rate_hz"))
        self.label_echo_delay.setText(tr(self.lang, "echo_delay_ms"))
        self.label_echo_decay.setText(tr(self.lang, "echo_decay"))
        self.label_robot_carrier.setText(tr(self.lang, "robot_carrier_hz"))
        self.label_robot_mix.setText(tr(self.lang, "robot_mix"))
        self.label_tremolo_rate.setText(tr(self.lang, "tremolo_rate_hz"))
        self.label_tremolo_depth.setText(tr(self.lang, "tremolo_depth"))
        self.label_bitcrusher_bits.setText(tr(self.lang, "bitcrusher_bits"))
        self.label_bitcrusher_hold.setText(tr(self.lang, "bitcrusher_hold"))
        self.label_pitch_shift.setText(tr(self.lang, "pitch_shift_semitones"))
        self.label_speed_factor.setText(tr(self.lang, "speed_factor"))
        self.hint_label.setText(
            f"• {tr(self.lang, 'offline_hint')}\n"
            f"• {tr(self.lang, 'device_auto_hint')}\n"
            f"• {tr(self.lang, 'audio_effects_hint')}\n"
            f"• {tr(self.lang, 'effect_preview_hint')}\n"
            f"• {tr(self.lang, 'app_restart_note')}"
        )

    def _collect_audio_effect_settings(self, force_enabled: bool = False) -> dict:
        return {
            "audio_effects_enabled": True if force_enabled else self.audio_effects_enabled_check.isChecked(),
            "normalize_audio": self.normalize_audio_check.isChecked(),
            "normalize_target_db": self.normalize_target_spin.value(),
            "output_gain_db": self.output_gain_spin.value(),
            "chorus_enabled": self.chorus_enabled_check.isChecked(),
            "chorus_mix": self.chorus_mix_spin.value() / 100.0,
            "chorus_depth_ms": self.chorus_depth_spin.value(),
            "chorus_rate_hz": self.chorus_rate_spin.value(),
            "echo_enabled": self.echo_enabled_check.isChecked(),
            "echo_delay_ms": self.echo_delay_spin.value(),
            "echo_decay": self.echo_decay_spin.value() / 100.0,
            "robot_enabled": self.robot_enabled_check.isChecked(),
            "robot_carrier_hz": self.robot_carrier_spin.value(),
            "robot_mix": self.robot_mix_spin.value() / 100.0,
            "tremolo_enabled": self.tremolo_enabled_check.isChecked(),
            "tremolo_rate_hz": self.tremolo_rate_spin.value(),
            "tremolo_depth": self.tremolo_depth_spin.value() / 100.0,
            "bitcrusher_enabled": self.bitcrusher_enabled_check.isChecked(),
            "bitcrusher_bits": self.bitcrusher_bits_spin.value(),
            "bitcrusher_hold": self.bitcrusher_hold_spin.value(),
            "pitch_shift_semitones": self.pitch_shift_spin.value(),
            "speed_factor": self.speed_factor_spin.value(),
        }

    def _play_effect_preview(self, with_effects: bool) -> None:
        if not PREVIEW_SAMPLE_PATH.exists():
            QMessageBox.warning(
                self,
                tr(self.lang, "warning"),
                f"{tr(self.lang, 'preview_sample_missing')}\n{PREVIEW_SAMPLE_PATH}",
            )
            return

        try:
            self.preview_player.stop()
            target_path: Path = PREVIEW_SAMPLE_PATH
            if with_effects:
                audio, sample_rate = sf.read(str(PREVIEW_SAMPLE_PATH), dtype="float32", always_2d=False)
                processed = apply_audio_effects(audio, int(sample_rate), self._collect_audio_effect_settings(force_enabled=True))
                target_path = ensure_dir(PREVIEW_DIR) / "effect_preview_current.wav"
                sf.write(str(target_path), processed, int(sample_rate))
            self.preview_player.setSource(QUrl.fromLocalFile(str(target_path)))
            self.preview_player.play()
        except Exception:
            QMessageBox.critical(self, tr(self.lang, "error"), traceback.format_exc())

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
            **self._collect_audio_effect_settings(force_enabled=False),
        }
