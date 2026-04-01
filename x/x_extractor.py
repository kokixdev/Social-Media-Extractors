#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys


CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from common.social_media_extractor import run_extractor


if __name__ == "__main__":
    raise SystemExit(run_extractor("X", "https://x.com/username"))
