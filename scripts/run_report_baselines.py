#!/usr/bin/env python3
"""Generate transcript-to-report comparison baselines for a saved project."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.report_baseline import (
    DEFAULT_REPORT_BASELINE_MODES,
    export_report_baseline_package_async,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the report-baseline export CLI."""
    parser = argparse.ArgumentParser(
        description="Generate transcript-to-report comparison baselines for a project"
    )
    parser.add_argument("project_id", help="Project ID to export report baselines for")
    parser.add_argument("--projects-dir", type=Path, help="Optional project store directory")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument(
        "--mode",
        action="append",
        choices=DEFAULT_REPORT_BASELINE_MODES,
        help="Baseline mode to run; repeatable. Defaults to both modes.",
    )
    parser.add_argument("--model", default="gpt-5-mini", help="Model name")
    parser.add_argument(
        "--max-chars-per-doc",
        type=int,
        help="Optional per-document character cap before prompting",
    )
    parser.add_argument("--trace-id", help="Optional llm_client trace ID prefix")
    parser.add_argument(
        "--max-budget",
        type=float,
        default=5.0,
        help="Pre-flight llm_client budget limit for baseline generation",
    )
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=args.projects_dir) if args.projects_dir else ProjectStore()
    try:
        state = store.load(args.project_id)
        package = asyncio.run(export_report_baseline_package_async(
            state,
            modes=args.mode or DEFAULT_REPORT_BASELINE_MODES,
            model_name=args.model,
            max_chars_per_doc=args.max_chars_per_doc,
            trace_id=args.trace_id,
            max_budget=args.max_budget,
        ))
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
