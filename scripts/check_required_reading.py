#!/usr/bin/env python3
"""Compatibility wrapper for required-read enforcement.

Canonical implementation lives in ``scripts/meta/file_context.py`` (importable
runtime: ``enforced_planning.file_context``). Keep this wrapper so legacy calls
and repo-local muscle memory continue to work while the canonical/default
enforcement decision remains a Make/docs policy question rather than a path
discovery problem.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TARGET = SCRIPT_DIR / "meta" / "file_context.py"
if not TARGET.exists():
    TARGET = SCRIPT_DIR / "file_context.py"


if __name__ == "__main__":
    if not TARGET.exists():
        print(f"Missing target script: {TARGET}", file=sys.stderr)
        raise SystemExit(2)

    # Preserve caller args, force the required-reading mode, and keep this file
    # as a stable legacy alias rather than a second implementation.
    sys.argv = [str(TARGET), "--check-reads", *sys.argv[1:]]
    runpy.run_path(str(TARGET), run_name="__main__")
