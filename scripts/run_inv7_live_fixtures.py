#!/usr/bin/env python3
"""Run live INV-7 prompt-injection fixtures and write scorecard input JSON."""

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

from qc_clean.core.inv7_fixtures import (
    _call_live_fixture_model,
    load_inv7_live_fixture_manifest,
    run_inv7_live_fixtures_async,
)


DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TRACE_ID = "qualitative_coding/inv7-live-fixtures"
DEFAULT_MAX_BUDGET = 1.0


def main(argv: Sequence[str] | None = None) -> int:
    """Run live INV-7 fixtures and write a PROMPT_INJECTION-compatible file."""
    parser = argparse.ArgumentParser(description="Run live INV-7 prompt-injection fixtures")
    parser.add_argument("--output", required=True, help="Path to write INV-7 fixture results JSON")
    parser.add_argument(
        "--fixtures",
        help="Optional schema_version=1 INV-7 live fixture manifest JSON",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Live model name")
    parser.add_argument("--trace-id", default=DEFAULT_TRACE_ID, help="llm_client trace ID prefix")
    parser.add_argument(
        "--max-budget",
        type=float,
        default=DEFAULT_MAX_BUDGET,
        help="llm_client maximum budget for the live fixture run",
    )
    args = parser.parse_args(argv)

    if args.fixtures:
        manifest = load_inv7_live_fixture_manifest(Path(args.fixtures))
        payload = asyncio.run(
            run_inv7_live_fixtures_async(
                model_name=args.model,
                trace_id=args.trace_id,
                max_budget=args.max_budget,
                fixtures=manifest.fixtures,
                call_model=_call_live_fixture_model,
                package_id=manifest.package_id,
                split=manifest.split,
                fixture_set_id=manifest.fixture_set_id,
                fixture_set_version=manifest.fixture_set_version,
                prompt_frozen=manifest.prompt_frozen,
                contamination_checked=manifest.contamination_checked,
                note=manifest.note,
            )
        )
    else:
        payload = asyncio.run(
            run_inv7_live_fixtures_async(
                model_name=args.model,
                trace_id=args.trace_id,
                max_budget=args.max_budget,
            )
        )
    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    evaluations = payload["prompt_injection_evaluations"]
    failed = sum(1 for item in evaluations if item["attack_succeeded"])
    print(
        json.dumps(
            {
                "output": str(output_path),
                "mode": payload["mode"],
                "evaluator": payload["evaluator"],
                "model": payload["model"],
                "trace_id": payload["trace_id"],
                "total_fixtures": len(evaluations),
                "failed": failed,
                "passed": len(evaluations) - failed,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
