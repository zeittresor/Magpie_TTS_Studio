from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.constants import AUXILIARY_MODEL_REPO_IDS, CACHE_DIR
from src.downloader import ensure_all_model_files_cached


def main() -> int:
    parser = argparse.ArgumentParser(description="Prefetch Magpie TTS files into the local cache.")
    parser.add_argument("--cache-dir", default=str(CACHE_DIR))
    parser.add_argument("--offline-check", action="store_true", help="Only verify already cached files; do not access the network.")
    args = parser.parse_args()

    model_path = ensure_all_model_files_cached(args.cache_dir, offline_mode=bool(args.offline_check))
    print(f"Main model cached at: {model_path}")
    if AUXILIARY_MODEL_REPO_IDS:
        print("Auxiliary runtime models checked/cached:")
        for repo_id in AUXILIARY_MODEL_REPO_IDS:
            print(f"  - {repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
