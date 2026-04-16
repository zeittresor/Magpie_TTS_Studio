from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.constants import APP_NAME
from src.logger import setup_logging
from src.main_window import MainWindow


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
