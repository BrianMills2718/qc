#!/usr/bin/env python3
"""Run an agent reviewer over a report review packet."""

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

from qc_clean.core.report_review_response import review_report_packet_file_async


def main(argv: Sequence[str] | None = None) -> int:
    """Run the report review response CLI."""
    parser = argparse.ArgumentParser(
        description="Run an agent reviewer over a report comparison packet"
    )
    parser.add_argument("packet", type=Path, help="Report review packet JSON path")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument("--model", default="gpt-5-mini", help="Model name")
    parser.add_argument("--reviewer-id", default="agent-reviewer", help="Reviewer identifier")
    parser.add_argument("--trace-id", help="Optional llm_client trace ID")
    parser.add_argument("--max-budget", type=float, default=5.0, help="Maximum llm_client budget")
    args = parser.parse_args(argv)

    try:
        response = asyncio.run(review_report_packet_file_async(
            args.packet,
            model_name=args.model,
            reviewer_id=args.reviewer_id,
            trace_id=args.trace_id,
            max_budget=args.max_budget,
        ))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, RuntimeError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(response, indent=2)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
