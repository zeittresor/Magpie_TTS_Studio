from __future__ import annotations

import os


def main() -> int:
    if os.name != "nt":
        return 0
    try:
        import ctypes

        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
