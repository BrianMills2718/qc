#!/usr/bin/env python3
"""Verify a local SQLite export audit event mirror."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.export.audit_event_log import verify_export_audit_event_db


def main(argv: Sequence[str] | None = None) -> int:
    """Verify a SQLite export audit event mirror and print a JSON report."""
    parser = argparse.ArgumentParser(description="Verify a SQLite export audit event mirror")
    parser.add_argument("db", type=Path, help="SQLite audit event database path")
    args = parser.parse_args(argv)

    report = verify_export_audit_event_db(args.db)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
