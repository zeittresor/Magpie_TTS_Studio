from __future__ import annotations

from pathlib import Path

APP_NAME = "Magpie TTS Studio"
APP_VERSION = "0.1.0"
APP_ORG = "OpenAI"
APP_DOMAIN = "local.magpie.tts.studio"

MODEL_REPO_ID = "nvidia/magpie_tts_multilingual_357m"
MODEL_FILENAME = "magpie_tts_multilingual_357m.nemo"
DEFAULT_SAMPLE_RATE = 22000

BASE_DIR = Path(__file__).resolve().parents[1]
APP_DATA_DIR = BASE_DIR / "app_data"
CACHE_DIR = APP_DATA_DIR / "hf_cache"
MODELS_DIR = APP_DATA_DIR / "models"
OUTPUT_DIR = APP_DATA_DIR / "outputs"
LOG_DIR = APP_DATA_DIR / "logs"
SETTINGS_PATH = APP_DATA_DIR / "settings.json"

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
    "autoplay": True,
    "save_output_copy": True,
    "output_dir": str(OUTPUT_DIR),
    "cache_dir": str(CACHE_DIR),
    "last_text": "Hello from Magpie TTS Studio.",
    "theme": "dark",
    "filename_template": "magpie_{timestamp}_{language}_{speaker}.wav",
}
