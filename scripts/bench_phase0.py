#!/usr/bin/env python3
"""Evaluation-harness Phase 0: print a grounding/reliability scorecard for a project.

Usage:
    python scripts/bench_phase0.py <project_id> [--gold-file gold.json]
        [--prompt-injection-file inv7.json] [--output scorecard.json]

Agent-drivable: emits JSON to stdout (and optionally a file). See
docs/EVALUATION_HARNESS.md (Phase 0). Deterministic, no LLM calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.bench import phase0_scorecard
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Phase 0 scorecard CLI."""
    parser = argparse.ArgumentParser(description="Evaluation-harness Phase 0 scorecard")
    parser.add_argument("project_id", help="Project ID to score")
    parser.add_argument(
        "--gold-file",
        help="Optional D7 disconfirmation gold JSON file; applied in memory only",
    )
    parser.add_argument(
        "--prompt-injection-file",
        help="Optional INV-7 prompt-injection fixture results JSON file; applied in memory only",
    )
    parser.add_argument("--output", help="Optional path to write the JSON scorecard")
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
    except FileNotFoundError:
        print(json.dumps({"error": f"Project '{args.project_id}' not found."}))
        return 1

    if args.gold_file:
        try:
            gold = load_d7_gold_file(Path(args.gold_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["disconfirmation_gold"] = gold

    if args.prompt_injection_file:
        try:
            prompt_injection_results = load_prompt_injection_file(Path(args.prompt_injection_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["prompt_injection_evaluations"] = prompt_injection_results

    try:
        card = phase0_scorecard(state)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    text = json.dumps(card, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return 0


def load_d7_gold_file(path: Path) -> Any:
    """Load and shape-check an external D7 gold annotation file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 gold file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 gold file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("contrary_evidence"), list):
        return raw
    raise ValueError(
        "D7 gold file must be a JSON list of anchors or an object with a "
        "'contrary_evidence' list"
    )


def load_prompt_injection_file(path: Path) -> Any:
    """Load and shape-check an external INV-7 prompt-injection result file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Prompt injection file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Prompt injection file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("prompt_injection_evaluations"), list):
        return raw["prompt_injection_evaluations"]
    raise ValueError(
        "Prompt injection file must be a JSON list of fixture outcomes or an "
        "object with a 'prompt_injection_evaluations' list"
    )


if __name__ == "__main__":
    raise SystemExit(main())
