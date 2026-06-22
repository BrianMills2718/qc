#!/usr/bin/env python3
"""Validate a versioned D7 baseline prediction package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_baseline_package import (  # noqa: E402
    D7_BASELINE_PACKAGE_CAUTION,
    build_d7_baseline_package_report,
    validate_d7_baseline_package_payload,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a D7 baseline package and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(description="Validate a versioned D7 baseline package")
    parser.add_argument("package", type=Path, help="D7 baseline package JSON file")
    args = parser.parse_args(argv)

    try:
        raw = json.loads(args.package.read_text(encoding="utf-8"))
        package = validate_d7_baseline_package_payload(raw)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({
            "schema_version": 1,
            "package_type": "d7_baseline_package_validation",
            "status": "fail",
            "error": str(exc),
            "caution": D7_BASELINE_PACKAGE_CAUTION,
        }))
        return 1

    report = build_d7_baseline_package_report(package)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
