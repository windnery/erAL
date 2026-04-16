"""Test package bootstrap for unittest discovery."""

from __future__ import annotations

import sys
from pathlib import Path


_TESTS_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_ROOT.parent
_SRC_PATH = _REPO_ROOT / "src"
_SRC_TEXT = str(_SRC_PATH)

if _SRC_PATH.is_dir():
    if _SRC_TEXT in sys.path:
        sys.path.remove(_SRC_TEXT)
    sys.path.insert(0, _SRC_TEXT)
