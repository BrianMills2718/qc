#!/usr/bin/env python3
"""Compatibility wrapper for the repo-local plan-status checker.

This repo does not use the shared numbered-plan `Gap Summary` format. Keep this
legacy entrypoint callable, but delegate to `scripts/sync_plan_status.py` so it
checks the real Completed Plans table instead of returning a vacuous empty list.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR.parent / "sync_plan_status.py"


if __name__ == "__main__":
    if not TARGET.exists():
        print(f"Missing target script: {TARGET}", file=sys.stderr)
        raise SystemExit(2)

    sys.argv = [str(TARGET), *sys.argv[1:]]
    runpy.run_path(str(TARGET), run_name="__main__")
