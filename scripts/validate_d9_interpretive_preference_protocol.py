#!/usr/bin/env python3
"""Validate a versioned D9 interpretive-preference protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d9_interpretive_preference_protocol import (  # noqa: E402
    load_d9_interpretive_preference_protocol,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a D9 interpretive-preference protocol and emit JSON."""
    parser = argparse.ArgumentParser(
        description="Validate a D9 interpretive-preference protocol package"
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 D9 interpretive-preference protocol JSON",
    )
    args = parser.parse_args(argv)

    try:
        package = load_d9_interpretive_preference_protocol(Path(args.protocol))
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1

    print(json.dumps({
        "valid": True,
        "protocol_id": package.protocol_id,
        "project_id": package.project_id,
        "dataset_name": package.dataset_name,
        "split": package.split,
        "corpus_sha256": package.corpus_sha256,
        "project_state_sha256": package.project_state_sha256,
        "comparison_artifact_sha256": package.comparison_artifact_sha256,
        "prompt_frozen": package.prompt_frozen,
        "contamination_checked": package.contamination_checked,
        "registered_before_evaluation": package.registered_before_evaluation,
        "blinded": package.blinded,
        "evaluator_types": package.evaluator_plan.evaluator_types,
        "planned_evaluator_count": package.evaluator_plan.planned_evaluator_count,
        "target_criteria": package.target_criteria,
        "target_surfaces": package.target_surfaces,
        "planned_case_count": package.planned_case_count,
        "non_inferiority_margin": package.non_inferiority_margin,
        "outcome_metrics": package.outcome_metrics,
        "success_criteria_count": len(package.success_criteria),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
