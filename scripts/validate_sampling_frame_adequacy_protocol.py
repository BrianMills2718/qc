#!/usr/bin/env python3
"""Validate a versioned sampling-frame adequacy protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.sampling_frame_adequacy_protocol import (
    load_sampling_frame_adequacy_protocol,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a sampling-frame adequacy protocol and emit JSON."""
    parser = argparse.ArgumentParser(
        description="Validate a sampling-frame adequacy protocol package"
    )
    parser.add_argument(
        "protocol",
        help="Path to a schema_version=1 sampling-frame adequacy protocol JSON",
    )
    args = parser.parse_args(argv)

    try:
        package = load_sampling_frame_adequacy_protocol(Path(args.protocol))
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
        "corpus_scope_sha256": package.corpus_scope_sha256,
        "scope_frozen": package.scope_frozen,
        "contamination_checked": package.contamination_checked,
        "registered_before_evaluation": package.registered_before_evaluation,
        "dimensions": package.dimensions,
        "reviewer_types": package.reviewer_plan.reviewer_types,
        "planned_reviewer_count": package.reviewer_plan.planned_reviewer_count,
        "success_criteria_count": len(package.success_criteria),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
