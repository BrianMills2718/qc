#!/usr/bin/env python3
"""Validate completed adjudication sample responses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.adjudication_sample import load_adjudication_response_package


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a completed adjudication sample response package."""
    parser = argparse.ArgumentParser(description="Validate adjudication responses")
    parser.add_argument("package", help="Path to a completed adjudication sample JSON package")
    args = parser.parse_args(argv)

    try:
        report = load_adjudication_response_package(Path(args.package))
    except ValueError as exc:
        print(json.dumps({
            "schema_version": 1,
            "package_type": "adjudication_response_validation",
            "status": "invalid",
            "error_count": 1,
            "errors": [
                {
                    "item_id": "__package__",
                    "field": "package",
                    "message": str(exc),
                }
            ],
            "caution": (
                "This report validates response completeness and shape only; "
                "it is not expert evidence, a gold set, a correctness estimate, "
                "or a benchmark result."
            ),
        }, indent=2))
        return 1

    payload = report.model_dump(mode="json")
    print(json.dumps(payload, indent=2))
    return 0 if report.status == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
