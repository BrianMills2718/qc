#!/usr/bin/env python3
"""Import completed adjudication responses into D3/D7 gold packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.adjudication_import import (
    build_adjudication_gold_import,
    write_adjudication_gold_import,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Import adjudication responses and write requested gold packages."""
    parser = argparse.ArgumentParser(description="Import adjudication responses")
    parser.add_argument("package", type=Path, help="Completed adjudication response package")
    parser.add_argument("--output-d3", type=Path, help="Optional D3 gold package output path")
    parser.add_argument("--output-d7", type=Path, help="Optional D7 gold package output path")
    parser.add_argument("--gold-set-id", required=True, help="Stable gold-set ID")
    parser.add_argument("--dataset-name", required=True, help="Human-readable dataset name")
    parser.add_argument(
        "--split",
        choices=["held_out", "dev", "public_comparator"],
        default="dev",
        help="Evaluation split represented by generated packages",
    )
    parser.add_argument("--coder-count", type=int, required=True, help="Number of coders")
    parser.add_argument("--adjudicator", required=True, help="Adjudicator identifier")
    parser.add_argument("--protocol", required=True, help="Adjudication protocol summary")
    parser.add_argument(
        "--prompt-frozen",
        action="store_true",
        help="Mark prompts/models as frozen before scoring this split",
    )
    parser.add_argument(
        "--contamination-checked",
        action="store_true",
        help="Mark train/test contamination as checked for this split",
    )
    parser.add_argument("--notes", default="", help="Optional adjudication notes")
    args = parser.parse_args(argv)

    if args.output_d3 is None and args.output_d7 is None:
        print(json.dumps({"status": "error", "error": "At least one output is required"}, indent=2))
        return 1

    try:
        payload = json.loads(args.package.read_text(encoding="utf-8"))
        result = build_adjudication_gold_import(
            payload,
            gold_set_id=args.gold_set_id,
            dataset_name=args.dataset_name,
            coder_count=args.coder_count,
            adjudicator=args.adjudicator,
            protocol=args.protocol,
            include_d3=args.output_d3 is not None,
            include_d7=args.output_d7 is not None,
            split=args.split,
            prompt_frozen=args.prompt_frozen,
            contamination_checked=args.contamination_checked,
            notes=args.notes,
        )
        outputs = write_adjudication_gold_import(
            result,
            d3_output=args.output_d3,
            d7_output=args.output_d7,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    report = result.report.model_dump(mode="json")
    report.update(outputs)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
