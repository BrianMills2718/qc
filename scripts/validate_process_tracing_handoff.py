#!/usr/bin/env python3
"""Validate a QC process-tracing handoff package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.process_tracing_handoff import load_process_tracing_handoff_package


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for process-tracing handoff validation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", help="Process-tracing handoff package JSON")
    args = parser.parse_args(argv)

    try:
        package = load_process_tracing_handoff_package(args.package)
    except Exception as exc:
        print(f"Invalid process-tracing handoff package: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "pass",
        "project_id": package.project_id,
        "observed_patterns": len(package.observed_patterns),
        "abductive_candidates": len(package.abductive_candidates),
        "analytic_claims": len(package.analytic_claims),
        "anchors": len(package.anchors),
        "caveat": package.caveats[0],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
