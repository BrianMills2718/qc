#!/usr/bin/env python3
"""Evaluation-harness Phase 0: print a grounding/reliability scorecard for a project.

Usage:
    python scripts/bench_phase0.py <project_id> [--gold-file gold.json]
        [--d7-baselines-file baselines.json] [--prompt-injection-file inv7.json]
        [--output scorecard.json]

Agent-drivable: emits JSON to stdout (and optionally a file). See
docs/EVALUATION_HARNESS.md (Phase 0). Deterministic, no LLM calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.bench import (
    DEFAULT_OBSERVABILITY_DB_PATH,
    d10_cost_latency_scorecard,
    d10_wall_clock_scorecard,
    phase0_scorecard,
)
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
        "--d7-baselines-file",
        help="Optional D7 baseline prediction JSON file; applied in memory only",
    )
    parser.add_argument(
        "--prompt-injection-file",
        help="Optional INV-7 prompt-injection fixture results JSON file; applied in memory only",
    )
    parser.add_argument(
        "--observability-db",
        type=Path,
        default=None,
        help=(
            "Optional llm_client observability SQLite DB for D10 cost/latency; "
            "defaults to the shared llm_client DB when omitted"
        ),
    )
    parser.add_argument(
        "--trace-id",
        help="Optional exact trace_id for D10 cost/latency; default uses project trace prefix",
    )
    parser.add_argument("--output", help="Optional path to write the JSON scorecard")
    args = parser.parse_args(argv)

    store = ProjectStore()
    try:
        state = store.load(args.project_id)
    except FileNotFoundError:
        print(json.dumps({"error": f"Project '{args.project_id}' not found."}))
        return 1
    loaded_state = state

    if args.gold_file:
        try:
            gold = load_d7_gold_file(Path(args.gold_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["disconfirmation_gold"] = gold

    if args.d7_baselines_file:
        try:
            baselines = load_d7_baselines_file(Path(args.d7_baselines_file))
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}))
            return 1
        state = state.model_copy(deep=True)
        state.config.extra = dict(state.config.extra)
        state.config.extra["disconfirmation_baselines"] = baselines

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
    card.setdefault("_meta", {})["input_hashes"] = phase0_input_hashes(
        loaded_state,
        gold_file=Path(args.gold_file) if args.gold_file else None,
        d7_baselines_file=Path(args.d7_baselines_file) if args.d7_baselines_file else None,
        prompt_injection_file=Path(args.prompt_injection_file) if args.prompt_injection_file else None,
        observability_db=args.observability_db,
    )
    observability_db = args.observability_db or DEFAULT_OBSERVABILITY_DB_PATH
    card["wall_clock_d10"] = d10_wall_clock_scorecard(state)
    card["cost_latency_d10"] = d10_cost_latency_scorecard(
        state,
        observability_db,
        trace_id=args.trace_id,
    )

    text = json.dumps(card, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    return 0


def phase0_input_hashes(
    state,
    *,
    gold_file: Path | None,
    d7_baselines_file: Path | None,
    prompt_injection_file: Path | None,
    observability_db: Path | None,
) -> dict[str, Any]:
    """Return deterministic SHA-256 input hashes for Phase 0 bench output."""
    return {
        "hash_algorithm": "sha256",
        "project_id": state.id,
        "project_state_sha256": sha256_jsonable(state.model_dump(mode="json")),
        "corpus_sha256": sha256_jsonable(corpus_hash_payload(state)),
        "gold_file_sha256": sha256_file(gold_file) if gold_file else None,
        "d7_baselines_file_sha256": (
            sha256_file(d7_baselines_file) if d7_baselines_file else None
        ),
        "prompt_injection_file_sha256": (
            sha256_file(prompt_injection_file) if prompt_injection_file else None
        ),
        "observability_db_sha256": sha256_file(observability_db),
    }


def corpus_hash_payload(state) -> list[dict[str, Any]]:
    """Return the canonical corpus payload used for dataset hashing."""
    return [
        {
            "id": doc.id,
            "name": doc.name,
            "content": doc.content,
            "metadata": doc.metadata,
        }
        for doc in state.corpus.documents
    ]


def sha256_jsonable(value: Any) -> str:
    """Hash a JSON-serializable value using canonical compact JSON."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path | None) -> str | None:
    """Hash file bytes, returning None when no file exists."""
    if path is None or not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_d7_baselines_file(path: Path) -> Any:
    """Load and shape-check an external D7 baseline prediction file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 baselines file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 baselines file '{path}' is not valid JSON: {exc}") from exc

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("disconfirmation_baselines"), list):
        return raw["disconfirmation_baselines"]
    raise ValueError(
        "D7 baselines file must be a JSON list of baseline predictions or an "
        "object with a 'disconfirmation_baselines' list"
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
