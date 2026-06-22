#!/usr/bin/env python3
"""Export theoretical-sampling result packages from selected candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.theoretical_sampling_results import (
    export_theoretical_sampling_results,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the theoretical-sampling result export CLI."""

    parser = argparse.ArgumentParser(
        description="Export theoretical-sampling result packages"
    )
    parser.add_argument(
        "protocol",
        type=Path,
        help="Path to a schema_version=1 theoretical-sampling protocol JSON",
    )
    parser.add_argument(
        "--candidates-file",
        required=True,
        type=Path,
        help="Theoretical-sampling candidate package JSON file",
    )
    parser.add_argument(
        "--selected-candidate-id",
        action="append",
        required=True,
        dest="selected_candidate_ids",
        help="Selected candidate ID; may be repeated",
    )
    parser.add_argument(
        "--success-criterion-met",
        action="append",
        required=True,
        dest="success_criteria_met",
        help="Pre-registered success criterion marked as met; may be repeated",
    )
    parser.add_argument(
        "--stopped-by-rule",
        action="store_true",
        help="Mark the result package as stopped by the protocol stopping rule",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args(argv)

    try:
        protocol = _load_json(args.protocol, label="protocol")
        candidates = _load_json(args.candidates_file, label="candidates")
        package = export_theoretical_sampling_results(
            protocol,
            candidates,
            selected_candidate_ids=args.selected_candidate_ids,
            success_criteria_met=args.success_criteria_met,
            stopped_by_rule=args.stopped_by_rule,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(package, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


def _load_json(path: Path, *, label: str) -> Any:
    """Load a JSON file with context-rich errors."""

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Theoretical sampling {label} file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Theoretical sampling {label} file '{path}' is not valid JSON: {exc}"
        ) from exc


if __name__ == "__main__":
    raise SystemExit(main())
