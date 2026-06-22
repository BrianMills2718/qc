#!/usr/bin/env python3
"""Write a hash manifest for existing project export artifacts."""

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
    build_export_audit_manifest,
    write_export_audit_manifest,
)
from qc_clean.core.persistence.project_store import ProjectStore


def main(argv: Sequence[str] | None = None) -> int:
    """Write an export audit manifest and print it as JSON."""
    parser = argparse.ArgumentParser(description="Write an export audit hash manifest")
    parser.add_argument("project_id", help="Project ID used to build the export")
    parser.add_argument(
        "--format",
        required=True,
        choices=["json", "csv", "markdown", "qdpx"],
        help="Export format represented by the artifacts",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        required=True,
        help="Export artifact path; repeat for multi-file exports such as CSV",
    )
    parser.add_argument("--output", required=True, type=Path, help="Manifest JSON output path")
    parser.add_argument(
        "--base-dir",
        type=Path,
        help="Optional base directory for relative artifact paths in the manifest",
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        help="Optional project store directory; defaults to ~/.qc_projects",
    )
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=args.projects_dir)
    try:
        state = store.load(args.project_id)
        manifest = build_export_audit_manifest(
            state,
            export_format=args.format,
            artifact_paths=[Path(path) for path in args.artifact],
            base_dir=args.base_dir,
        )
        write_export_audit_manifest(manifest, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(manifest.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
