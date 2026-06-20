#!/usr/bin/env python3
"""Plan-index consistency check for this repo's table-based plan tracking.

Why this is repo-local and not the shared `scripts/meta/sync_plan_status.py`:
the shared checker expects numbered `docs/plans/NN_name.md` files plus a
`## Gap Summary` table. This repo deliberately tracks plans with `## Active
Plans` / `## Completed Plans` tables in `docs/plans/CLAUDE.md` and unnumbered
record files under `docs/plans/completed/`. Pointed at this layout the shared
checker matches zero files and reports a *vacuous* green (the F1 false-green
finding). This validator checks what actually exists so the green means
something: every Completed-table record path resolves, and every record file is
referenced by the table.

Run: `python scripts/sync_plan_status.py --check` (used by `make docs-check`).
`--list` prints the parsed Completed rows.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLANS_DIR = Path("docs/plans")
PLANS_INDEX = PLANS_DIR / "CLAUDE.md"
COMPLETED_DIR = PLANS_DIR / "completed"

# `| Name | Outcome | `completed/FILE.md` |` — pull the record path out of the
# row. Tolerant of backticks and surrounding whitespace.
_RECORD_RE = re.compile(r"`?(completed/[^`|]+\.md)`?")


def _completed_rows(index_text: str) -> list[tuple[str, str]]:
    """Return (row_text, record_path) for each Completed Plans table row."""
    rows: list[tuple[str, str]] = []
    in_completed = False
    for line in index_text.splitlines():
        if line.startswith("## "):
            in_completed = line.strip() == "## Completed Plans"
            continue
        if not in_completed or not line.lstrip().startswith("|"):
            continue
        m = _RECORD_RE.search(line)
        if m:
            rows.append((line.strip(), m.group(1)))
    return rows


def check() -> list[str]:
    """Return a list of human-readable problems; empty means consistent."""
    if not PLANS_INDEX.exists():
        return [f"Missing plan index: {PLANS_INDEX}"]

    rows = _completed_rows(PLANS_INDEX.read_text(encoding="utf-8"))
    referenced = {record for _, record in rows}
    problems: list[str] = []

    # 1. Every referenced record file must exist.
    for _, record in rows:
        if not (PLANS_DIR / record).exists():
            problems.append(f"Completed row references missing record: {record}")

    # 2. Every record file on disk must be referenced (no orphan/unlisted plans).
    if COMPLETED_DIR.exists():
        for record_file in sorted(COMPLETED_DIR.glob("*.md")):
            rel = f"completed/{record_file.name}"
            if rel not in referenced:
                problems.append(f"Record file not listed in Completed Plans table: {rel}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail (exit 1) on any inconsistency")
    parser.add_argument("--list", "-l", action="store_true", help="Print parsed Completed rows")
    args = parser.parse_args()

    if args.list:
        for _, record in _completed_rows(PLANS_INDEX.read_text(encoding="utf-8")):
            print(f"  {record}")
        return 0

    problems = check()
    if problems:
        print("Plan index inconsistencies:")
        for p in problems:
            print(f"  - {p}")
        return 1 if args.check else 0
    print("All plan records are consistent with the Completed Plans table.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
