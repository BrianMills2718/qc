#!/usr/bin/env python3
"""Evaluation-harness Phase 0: print a grounding/reliability scorecard for a project.

Usage:
    python scripts/bench_phase0.py <project_id> [--output scorecard.json]

Agent-drivable: emits JSON to stdout (and optionally a file). See
docs/EVALUATION_HARNESS.md (Phase 0). Deterministic, no LLM calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.bench import phase0_scorecard
from qc_clean.core.persistence.project_store import ProjectStore


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluation-harness Phase 0 scorecard")
    parser.add_argument("project_id", help="Project ID to score")
    parser.add_argument("--output", help="Optional path to write the JSON scorecard")
    args = parser.parse_args()

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
    except FileNotFoundError:
        print(json.dumps({"error": f"Project '{args.project_id}' not found."}))
        return 1

    card = phase0_scorecard(state)
    text = json.dumps(card, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
