#!/usr/bin/env python3
"""Mirror a verified export audit event JSONL log into SQLite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.export.audit_event_log import mirror_export_audit_event_log_to_sqlite


def main(argv: Sequence[str] | None = None) -> int:
    """Mirror an export audit event log into SQLite and print a JSON report."""
    parser = argparse.ArgumentParser(description="Mirror export audit JSONL events into SQLite")
    parser.add_argument("log", type=Path, help="Export audit event JSONL path")
    parser.add_argument("--db", required=True, type=Path, help="SQLite audit event database path")
    args = parser.parse_args(argv)

    try:
        report = mirror_export_audit_event_log_to_sqlite(args.log, args.db)
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
