#!/usr/bin/env python3
"""Validate a versioned D6 bias-audit protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.d6_bias_protocol import load_d6_bias_protocol


def main(argv: Sequence[str] | None = None) -> int:
    """Validate a D6 bias protocol package and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(description="Validate a D6 bias protocol package")
    parser.add_argument("protocol", help="Path to a schema_version=1 D6 bias protocol JSON")
    args = parser.parse_args(argv)

    try:
        package = load_d6_bias_protocol(Path(args.protocol))
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1

    print(json.dumps({
        "valid": True,
        "protocol_id": package.protocol_id,
        "project_id": package.project_id,
        "dataset_name": package.dataset_name,
        "split": package.split,
        "dimensions": package.dimensions,
        "corpus_sha256": package.corpus_sha256,
        "project_state_sha256": package.project_state_sha256,
        "prompt_frozen": package.prompt_frozen,
        "contamination_checked": package.contamination_checked,
        "registered_before_run": package.registered_before_run,
        "attribute_count": len(package.attribute_policy.attributes),
        "planned_case_count": package.case_set.planned_case_count,
        "success_criteria_count": len(package.success_criteria),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
