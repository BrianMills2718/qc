#!/usr/bin/env python3
"""Export theoretical-sampling candidate packages from a saved project."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.theoretical_sampling_candidates import (
    export_theoretical_sampling_candidates,
)
from qc_clean.core.theoretical_sampling_protocol import load_theoretical_sampling_protocol


def main(argv: Sequence[str] | None = None) -> int:
    """Run the theoretical-sampling candidate export CLI."""
    parser = argparse.ArgumentParser(
        description="Export loaded-document theoretical-sampling candidates"
    )
    parser.add_argument("project_id", help="Project ID to export candidates for")
    parser.add_argument("--projects-dir", type=Path, help="Optional project store directory")
    parser.add_argument(
        "--protocol",
        required=True,
        type=Path,
        help="Path to a schema_version=1 theoretical-sampling protocol JSON",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument(
        "--candidate-name",
        action="append",
        dest="candidate_names",
        help="Optional loaded document name to consider; may be repeated",
    )
    parser.add_argument("--max-suggestions", type=int, help="Optional suggestion limit")
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=args.projects_dir) if args.projects_dir else ProjectStore()
    try:
        state = store.load(args.project_id)
        protocol = load_theoretical_sampling_protocol(args.protocol)
        package = export_theoretical_sampling_candidates(
            state,
            protocol,
            candidate_names=args.candidate_names,
            max_suggestions=args.max_suggestions,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(package, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
