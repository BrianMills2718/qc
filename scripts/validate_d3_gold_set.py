#!/usr/bin/env python3
"""Validate a versioned D3 held-out gold-set package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d3_gold import load_d3_gold_set


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a D3 gold-set package and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(description="Validate a versioned D3 gold-set package")
    parser.add_argument("gold_set", help="Path to a schema_version=1 D3 gold-set JSON package")
    args = parser.parse_args(argv)

    try:
        package = load_d3_gold_set(args.gold_set)
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1

    print(json.dumps({
        "valid": True,
        "gold_set_id": package.gold_set_id,
        "dataset_name": package.dataset_name,
        "split": package.split,
        "corpus_sha256": package.corpus_sha256,
        "project_state_sha256": package.project_state_sha256,
        "prompt_frozen": package.prompt_frozen,
        "contamination_checked": package.contamination_checked,
        "coder_count": package.adjudication.coder_count,
        "application_gold_count": len(package.application_gold),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
