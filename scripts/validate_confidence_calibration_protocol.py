#!/usr/bin/env python3
"""Validate a versioned confidence-calibration protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.confidence_calibration_protocol import (  # noqa: E402
    load_confidence_calibration_protocol,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a confidence-calibration protocol and emit JSON."""
    parser = argparse.ArgumentParser(
        description="Validate a confidence-calibration protocol package"
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 confidence-calibration protocol JSON",
    )
    args = parser.parse_args(argv)

    try:
        package = load_confidence_calibration_protocol(Path(args.protocol))
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
        "prediction_artifact_sha256": package.prediction_artifact_sha256,
        "prompt_frozen": package.prompt_frozen,
        "contamination_checked": package.contamination_checked,
        "registered_before_evaluation": package.registered_before_evaluation,
        "label_sources": package.label_plan.label_sources,
        "planned_labeler_count": package.label_plan.planned_labeler_count,
        "target_surfaces": package.target_surfaces,
        "confidence_source": package.confidence_source,
        "planned_item_count": package.planned_item_count,
        "outcome_metrics": package.outcome_metrics,
        "success_criteria_count": len(package.success_criteria),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
