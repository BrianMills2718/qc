#!/usr/bin/env python3
"""Validate a versioned INV-7 prompt-injection package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.inv7_package import load_inv7_prompt_injection_package


def main(argv: Sequence[str] | None = None) -> int:
    """Validate an INV-7 prompt-injection package and emit JSON."""
    parser = argparse.ArgumentParser(description="Validate a versioned INV-7 prompt-injection package")
    parser.add_argument("package", help="Path to a schema_version=1 INV-7 package JSON")
    args = parser.parse_args(argv)

    try:
        package = load_inv7_prompt_injection_package(Path(args.package))
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    print(json.dumps({
        "ok": True,
        "package_id": package.package_id,
        "mode": package.mode,
        "split": package.split,
        "fixture_set_id": package.fixture_set_id,
        "fixture_set_version": package.fixture_set_version,
        "total_fixtures": package.total_fixtures,
        "failed": package.failed,
        "passed": package.passed,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
