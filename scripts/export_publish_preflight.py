#!/usr/bin/env python3
"""Run strict local preflight for export publish/handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.export.audit_event_log import (
    append_export_audit_event,
    mirror_export_audit_event_log_to_sqlite,
)
from qc_clean.core.export.publish_preflight import run_export_publish_preflight
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Run export publish preflight and print a JSON report."""
    parser = argparse.ArgumentParser(description="Run export publish preflight")
    parser.add_argument("--manifest", required=True, type=Path, help="Export audit manifest path")
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Optional base directory for resolving manifest artifact paths",
    )
    parser.add_argument("--project-id", help="Optional project ID for project-state hash checking")
    parser.add_argument(
        "--projects-dir",
        type=Path,
        help="Optional project store directory; defaults to ~/.qc_projects",
    )
    parser.add_argument(
        "--audit-log",
        type=Path,
        help="Optional export audit event JSONL log to append a publish_preflight event",
    )
    parser.add_argument(
        "--audit-db",
        type=Path,
        help="Optional SQLite mirror for the audit event log; requires --audit-log",
    )
    parser.add_argument(
        "--scope-lint",
        action="store_true",
        help="Also lint textual export artifacts for unsafe corpus-scope phrasing",
    )
    args = parser.parse_args(argv)
    if args.audit_db and not args.audit_log:
        print(json.dumps({"status": "error", "error": "--audit-db requires --audit-log"}, indent=2))
        return 1

    state = None
    if args.project_id:
        store = ProjectStore(projects_dir=args.projects_dir)
        try:
            state = store.load(args.project_id)
        except FileNotFoundError as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 1

    report = run_export_publish_preflight(
        args.manifest,
        base_dir=args.base_dir,
        state=state,
        scope_lint=args.scope_lint,
    )
    if args.audit_log:
        try:
            append_export_audit_event(
                args.audit_log,
                event_type="publish_preflight",
                event_status=report.status,
                manifest_path=args.manifest,
                payload=report.model_dump(mode="json"),
            )
            if args.audit_db:
                mirror_export_audit_event_log_to_sqlite(args.audit_log, args.audit_db)
        except (OSError, ValueError) as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 1
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
