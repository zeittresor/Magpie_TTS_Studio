from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .constants import APP_DATA_DIR, DEFAULT_SETTINGS, SETTINGS_PATH


class SettingsManager:
    def __init__(self, path: Path = SETTINGS_PATH) -> None:
        self.path = Path(path)
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            self.save(DEFAULT_SETTINGS.copy())
            return DEFAULT_SETTINGS.copy()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        self.save(merged)
        return merged

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
