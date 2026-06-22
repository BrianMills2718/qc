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

from qc_clean.core.export.audit_event_log import append_export_audit_event
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
    args = parser.parse_args(argv)

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
        except (OSError, ValueError) as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 1
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
