#!/usr/bin/env python3
"""Export opt-in live D7 candidate-selection baseline predictions."""

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

from qc_clean.core.d7_live_baseline import export_d7_live_candidate_baseline_async
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Run the live D7 baseline export CLI."""
    parser = argparse.ArgumentParser(
        description="Export live candidate-selection predictions as a D7 baseline package"
    )
    parser.add_argument("project_id", help="Project ID to export live baseline predictions for")
    parser.add_argument("--projects-dir", type=Path, help="Optional project store directory")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    parser.add_argument("--name", help="Optional baseline name")
    parser.add_argument("--description", default="", help="Optional baseline description")
    parser.add_argument("--model", default="gpt-5-mini", help="Live model name")
    parser.add_argument("--max-targets", type=int, default=20)
    parser.add_argument("--candidates-per-claim", type=int, default=5)
    parser.add_argument("--retrieval-mode", default="lexical_bm25")
    parser.add_argument("--bm25-k1", type=float, default=1.2)
    parser.add_argument("--bm25-b", type=float, default=0.75)
    parser.add_argument("--contrary-cue-weight", type=float, default=1.25)
    parser.add_argument("--expanded-term-weight", type=float, default=0.5)
    parser.add_argument("--embedding-model")
    parser.add_argument("--embedding-dimensions", type=int)
    parser.add_argument("--semantic-weight", type=float, default=1.0)
    parser.add_argument("--min-semantic-similarity", type=float, default=0.0)
    parser.add_argument("--trace-id", help="Base trace ID for live baseline observability")
    parser.add_argument(
        "--max-budget",
        type=float,
        default=1.0,
        help="Pre-flight llm_client budget limit for live baseline export",
    )
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=args.projects_dir) if args.projects_dir else ProjectStore()
    try:
        state = store.load(args.project_id)
        package = asyncio.run(export_d7_live_candidate_baseline_async(
            state,
            name=args.name,
            description=args.description,
            model_name=args.model,
            max_targets=args.max_targets,
            candidates_per_claim=args.candidates_per_claim,
            retrieval_mode=args.retrieval_mode,
            bm25_k1=args.bm25_k1,
            bm25_b=args.bm25_b,
            contrary_cue_weight=args.contrary_cue_weight,
            expanded_term_weight=args.expanded_term_weight,
            embedding_model=args.embedding_model,
            embedding_dimensions=args.embedding_dimensions,
            semantic_weight=args.semantic_weight,
            min_semantic_similarity=args.min_semantic_similarity,
            trace_id=args.trace_id or f"qualitative_coding/d7-live-baseline/{state.id}",
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
