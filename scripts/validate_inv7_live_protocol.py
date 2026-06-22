#!/usr/bin/env python3
"""Validate a versioned INV-7 live benchmark protocol package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.inv7_live_protocol import load_inv7_live_protocol


def main(argv: Sequence[str] | None = None) -> int:
    """Validate an INV-7 live protocol package and emit machine-readable JSON."""
    parser = argparse.ArgumentParser(description="Validate an INV-7 live protocol package")
    parser.add_argument("protocol", help="Path to a schema_version=1 INV-7 live protocol JSON")
    args = parser.parse_args(argv)

    try:
        package = load_inv7_live_protocol(Path(args.protocol))
    except ValueError as exc:
        print(json.dumps({"valid": False, "error": str(exc)}))
        return 1

    print(json.dumps({
        "valid": True,
        "protocol_id": package.protocol_id,
        "dataset_name": package.dataset_name,
        "split": package.split,
        "fixture_set_id": package.fixture_set_id,
        "fixture_set_version": package.fixture_set_version,
        "fixture_count": len(package.fixture_prompt_hashes),
        "model": package.model,
        "trace_id": package.trace_id,
        "max_budget": package.max_budget,
        "prompt_frozen": package.prompt_frozen,
        "contamination_checked": package.contamination_checked,
        "registered_before_run": package.registered_before_run,
        "success_criteria_count": len(package.success_criteria),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
