#!/usr/bin/env python3
"""Verify a local export audit event log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.export.audit_event_log import verify_export_audit_event_log


def main(argv: Sequence[str] | None = None) -> int:
    """Verify an export audit event log and print a JSON report."""
    parser = argparse.ArgumentParser(description="Verify an export audit event log")
    parser.add_argument("log", type=Path, help="Export audit event JSONL path")
    args = parser.parse_args(argv)

    report = verify_export_audit_event_log(args.log)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
