#!/usr/bin/env python3
"""Verify a hash manifest for project export artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.export.audit_manifest import (
    load_export_audit_manifest,
    verify_export_audit_manifest_payload,
)
from qc_clean.core.export.audit_event_log import (
    append_export_audit_event,
    mirror_export_audit_event_log_to_sqlite,
)
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Verify an export audit manifest and print a JSON report."""
    parser = argparse.ArgumentParser(description="Verify an export audit hash manifest")
    parser.add_argument("manifest", type=Path, help="Export audit manifest JSON path")
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Optional base directory for resolving relative artifact paths",
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
        help="Optional export audit event JSONL log to append a manifest_verified event",
    )
    parser.add_argument(
        "--audit-db",
        type=Path,
        help="Optional SQLite mirror for the audit event log; requires --audit-log",
    )
    args = parser.parse_args(argv)
    if args.audit_db and not args.audit_log:
        print(json.dumps({"status": "error", "error": "--audit-db requires --audit-log"}, indent=2))
        return 1

    try:
        manifest = load_export_audit_manifest(args.manifest)
    except ValueError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    state = None
    if args.project_id:
        store = ProjectStore(projects_dir=args.projects_dir)
        try:
            state = store.load(args.project_id)
        except FileNotFoundError as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 1

    base_dir = args.base_dir if args.base_dir is not None else args.manifest.parent
    report = verify_export_audit_manifest_payload(
        manifest,
        base_dir=base_dir,
        state=state,
    )
    if args.audit_log:
        try:
            append_export_audit_event(
                args.audit_log,
                event_type="manifest_verified",
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
    return 0 if report.status == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
