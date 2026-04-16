from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.constants import CACHE_DIR
from src.downloader import ensure_model_cached


def main() -> int:
    parser = argparse.ArgumentParser(description="Prefetch Magpie TTS files into the local cache.")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR))
    args = parser.parse_args()

    model_path = ensure_model_cached(args.cache_dir)
    print(f"Model cached at: {model_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
