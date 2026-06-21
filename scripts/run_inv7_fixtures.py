#!/usr/bin/env python3
"""Run deterministic INV-7 structural fixtures and write scorecard input JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.inv7_fixtures import run_inv7_structural_fixtures


def main(argv: Sequence[str] | None = None) -> int:
    """Run structural INV-7 fixtures and write a PROMPT_INJECTION-compatible file."""
    parser = argparse.ArgumentParser(description="Run deterministic INV-7 structural fixtures")
    parser.add_argument("--output", required=True, help="Path to write INV-7 fixture results JSON")
    args = parser.parse_args(argv)

    payload = run_inv7_structural_fixtures()
    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    evaluations = payload["prompt_injection_evaluations"]
    failed = sum(1 for item in evaluations if item["attack_succeeded"])
    print(json.dumps({
        "output": str(output_path),
        "mode": payload["mode"],
        "evaluator": payload["evaluator"],
        "total_fixtures": len(evaluations),
        "failed": failed,
        "passed": len(evaluations) - failed,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
