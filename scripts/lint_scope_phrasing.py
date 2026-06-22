#!/usr/bin/env python3
"""Lint report text for corpus-scope-sensitive phrasing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.scope_lint import lint_scope_phrasing


def main(argv: Sequence[str] | None = None) -> int:
    """Run scope phrasing lint and emit a JSON report."""
    parser = argparse.ArgumentParser(description="Lint corpus-scope-sensitive phrasing")
    parser.add_argument("project_id", help="Project ID whose corpus scope should govern linting")
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input-file", type=Path, help="Text/Markdown file to lint")
    input_group.add_argument("--text", help="Inline text to lint")
    parser.add_argument(
        "--projects-dir",
        type=Path,
        help="Optional project store directory; defaults to ~/.qc_projects",
    )
    args = parser.parse_args(argv)

    store = ProjectStore(projects_dir=args.projects_dir)
    try:
        state = store.load(args.project_id)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        return 1

    if args.input_file is not None:
        try:
            text = args.input_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
            return 1
        source = str(args.input_file)
    else:
        text = args.text or ""
        source = "inline"

    report = lint_scope_phrasing(state, text, source=source)
    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 1 if report.status == "warn" else 0


if __name__ == "__main__":
    raise SystemExit(main())
