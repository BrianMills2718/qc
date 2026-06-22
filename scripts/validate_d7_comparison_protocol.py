#!/usr/bin/env python3
"""Validate a D7 retrieval comparison protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_comparison_protocol import load_d7_comparison_protocol


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a D7 comparison protocol and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(description="Validate a D7 retrieval comparison protocol")
    parser.add_argument("protocol", help="Path to a schema_version=1 D7 comparison protocol JSON")
    args = parser.parse_args(argv)

    try:
        package = load_d7_comparison_protocol(Path(args.protocol))
    except ValueError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}))
        return 1

    print(
        json.dumps(
            {
                "status": "valid",
                "schema_version": package.schema_version,
                "package_type": package.package_type,
                "protocol_id": package.protocol_id,
                "project_id": package.project_id,
                "gold_set_id": package.gold_set_id,
                "split": package.split,
                "expected_prediction_count": len(package.expected_predictions),
                "metric_criteria_count": len(package.metric_criteria),
                "caution": package.caution,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
