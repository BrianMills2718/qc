#!/usr/bin/env python3
"""Compare exported D7 retrieval prediction packages against a gold file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d7_retrieval import compare_d7_retrieval_predictions
from qc_clean.core.persistence.project_store import ProjectStore
from scripts.bench_phase0 import load_d7_gold_file


def main(argv: Sequence[str] | None = None) -> int:
    """Run the retrieval prediction comparison CLI."""
    parser = argparse.ArgumentParser(
        description="Score D7 retrieval prediction packages against one gold file"
    )
    parser.add_argument("project_id", help="Project ID to score")
    parser.add_argument("--gold-file", required=True, type=Path, help="D7 gold JSON file")
    parser.add_argument(
        "--predictions-file",
        required=True,
        action="append",
        type=Path,
        help="Retrieval prediction package JSON file; repeat to compare multiple packages",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report output path")
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
        gold_payload = load_d7_gold_file(args.gold_file)
        packages = [load_prediction_package(path) for path in args.predictions_file]
        report = compare_d7_retrieval_predictions(
            state,
            gold_payload=gold_payload,
            prediction_packages=packages,
        )
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


def load_prediction_package(path: Path) -> dict[str, Any]:
    """Load one retrieval prediction package from disk."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 retrieval prediction file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 retrieval prediction file '{path}' is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"D7 retrieval prediction file '{path}' must be a JSON object")
    return raw


if __name__ == "__main__":
    raise SystemExit(main())
