#!/usr/bin/env python3
"""Export a QC process-tracing handoff package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.process_tracing_handoff import write_process_tracing_handoff_package


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for process-tracing handoff export."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id", help="QC project ID")
    parser.add_argument("--output", required=True, help="Output package JSON path")
    parser.add_argument("--projects-dir", help="Explicit project store directory")
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=Path(args.projects_dir) if args.projects_dir else None)
    try:
        state = store.load(args.project_id)
    except FileNotFoundError:
        print(f"Project not found: {args.project_id}", file=sys.stderr)
        return 1

    package = write_process_tracing_handoff_package(state, args.output)
    print(json.dumps({
        "status": "pass",
        "project_id": package.project_id,
        "output": args.output,
        "observed_patterns": len(package.observed_patterns),
        "abductive_candidates": len(package.abductive_candidates),
        "analytic_claims": len(package.analytic_claims),
        "anchors": len(package.anchors),
        "caveat": package.caveats[0],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
