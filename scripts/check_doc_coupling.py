#!/usr/bin/env python3
"""Compatibility wrapper for the canonical doc-coupling checker.

Canonical implementation lives in ``scripts/meta/check_doc_coupling.py``.
Keep this wrapper because operator habits, hooks, and docs already point at the
short path; the goal is one implementation with multiple stable entrypoints,
not duplicate logic.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "meta" / "check_doc_coupling.py"


if __name__ == "__main__":
    if not TARGET.exists():
        print(f"Missing target script: {TARGET}", file=sys.stderr)
        raise SystemExit(2)

    sys.argv = [str(TARGET), *sys.argv[1:]]
    runpy.run_path(str(TARGET), run_name="__main__")
