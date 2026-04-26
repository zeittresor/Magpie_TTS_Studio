from __future__ import annotations

from pathlib import Path

APP_NAME = "Magpie TTS Studio"
APP_VERSION = "0.2.8"
APP_ORG = "OpenAI"
APP_DOMAIN = "local.magpie.tts.studio"

MODEL_REPO_ID = "nvidia/magpie_tts_multilingual_357m"
MODEL_FILENAME = "magpie_tts_multilingual_357m.nemo"
AUXILIARY_MODEL_REPO_IDS = (
    "microsoft/wavlm-base-plus",
    "google/byt5-small",
    "nvidia/nemo-nano-codec-22khz-1.89kbps-21.5fps",
)
DEFAULT_SAMPLE_RATE = 22000

BASE_DIR = Path(__file__).resolve().parents[1]
APP_DATA_DIR = BASE_DIR / "app_data"
CACHE_DIR = APP_DATA_DIR / "hf_cache"
MODELS_DIR = APP_DATA_DIR / "models"
OUTPUT_DIR = APP_DATA_DIR / "outputs"
LOG_DIR = APP_DATA_DIR / "logs"
SETTINGS_PATH = APP_DATA_DIR / "settings.json"
ASSETS_DIR = BASE_DIR / "assets"
AUDIO_ASSETS_DIR = ASSETS_DIR / "audio"
PREVIEW_SAMPLE_PATH = AUDIO_ASSETS_DIR / "effect_preview_clean.wav"
PREVIEW_DIR = APP_DATA_DIR / "preview"

LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
    "es": "Español",
    "fr": "Français",
    "it": "Italiano",
    "vi": "Tiếng Việt",
    "zh": "简体中文",
    "hi": "हिन्दी",
    "ja": "日本語",
}

SPEAKERS = {
    "Sofia": 1,
    "Aria": 2,
    "Jason": 3,
    "Leo": 4,
    "John": 0,
}

DEVICE_OPTIONS = ["auto", "cuda", "cpu"]

DEFAULT_SETTINGS = {
    "app_language": "en",
    "tts_language": "en",
    "speaker": "Sofia",
    "device": "auto",
    "apply_text_normalization": False,
    "offline_mode": False,
    "auto_download_on_first_start": True,
    "first_start_model_check_done": False,
    "autoplay": True,
    "save_output_copy": True,
    "output_dir": str(OUTPUT_DIR),
    "cache_dir": str(CACHE_DIR),
    "last_text": "Hello from Magpie TTS Studio.",
    "theme": "dark",
    "filename_template": "magpie_{timestamp}_{language}_{speaker}.wav",
    "audio_effects_enabled": False,
    "normalize_audio": True,
    "normalize_target_db": -1.0,
    "output_gain_db": 0.0,
    "chorus_enabled": False,
    "chorus_mix": 0.35,
    "chorus_depth_ms": 8.0,
    "chorus_rate_hz": 0.28,
    "echo_enabled": False,
    "echo_delay_ms": 220,
    "echo_decay": 0.28,
    "robot_enabled": False,
    "robot_carrier_hz": 90.0,
    "robot_mix": 0.65,
    "tremolo_enabled": False,
    "tremolo_rate_hz": 5.0,
    "tremolo_depth": 0.45,
    "bitcrusher_enabled": False,
    "bitcrusher_bits": 10,
    "bitcrusher_hold": 1,
    "pitch_shift_semitones": 0.0,
    "speed_factor": 1.0,
}
