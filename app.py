from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.constants import APP_NAME
from src.logger import setup_logging
from src.runtime_env import configure_runtime_environment
from src.settings_manager import SettingsManager


def main() -> int:
    setup_logging()
    startup_settings = SettingsManager().load()
    configure_runtime_environment(
        startup_settings.get("cache_dir", "app_data/hf_cache"),
        offline_mode=bool(startup_settings.get("offline_mode", False)),
    )

    # Import after runtime environment setup so Transformers/HF/NeMo see the
    # correct cache and offline flags when they are loaded later.
    from src.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
