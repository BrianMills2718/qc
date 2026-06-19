"""Show recent LLM and tool errors from the observability SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Sequence


DEFAULT_DB_PATH = Path.home() / "projects" / "data" / "llm_observability.db"


@dataclass(frozen=True)
class RecentError:
    """One recent observability error row."""

    timestamp: str
    source: str
    task: str
    trace_id: str
    detail: str


def fetch_recent_errors(
    db_path: Path,
    *,
    days: int,
    project: str,
    limit: int,
) -> list[RecentError]:
    """Fetch recent LLM and tool errors for a project."""
    if limit <= 0:
        return []
    if not db_path.exists():
        raise FileNotFoundError(f"Observability DB not found: {db_path}")

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = sqlite3.connect(str(db_path))
    try:
        llm_rows = conn.execute(
            """
            SELECT timestamp, 'llm', COALESCE(task, ''), COALESCE(trace_id, ''),
                   COALESCE(error_type, error, validation_errors, '')
            FROM llm_calls
            WHERE project = ?
              AND timestamp >= ?
              AND (
                error IS NOT NULL
                OR error_type IS NOT NULL
                OR validation_errors IS NOT NULL
              )
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (project, cutoff, limit),
        ).fetchall()
        tool_rows = conn.execute(
            """
            SELECT timestamp, 'tool', COALESCE(task, ''), COALESCE(trace_id, ''),
                   COALESCE(error_type, error_message, status, '')
            FROM tool_calls
            WHERE project = ?
              AND timestamp >= ?
              AND (
                error_type IS NOT NULL
                OR error_message IS NOT NULL
                OR status NOT IN ('ok', 'success', 'completed')
              )
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (project, cutoff, limit),
        ).fetchall()
    finally:
        conn.close()

    errors = [
        RecentError(
            timestamp=str(row[0]),
            source=str(row[1]),
            task=str(row[2]),
            trace_id=str(row[3]),
            detail=str(row[4]),
        )
        for row in [*llm_rows, *tool_rows]
    ]
    errors.sort(key=lambda err: err.timestamp, reverse=True)
    return errors[:limit]


def format_errors(errors: Sequence[RecentError]) -> str:
    """Format recent errors as compact terminal text."""
    if not errors:
        return "No recent errors found."

    lines = ["Recent errors:"]
    for err in errors:
        task = err.task or "-"
        trace_id = err.trace_id or "-"
        detail = err.detail or "-"
        lines.append(f"- {err.timestamp} [{err.source}] task={task} trace={trace_id} {detail}")
    return "\n".join(lines)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--project", default="qualitative_coding", help="Project filter")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows to show")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Observability DB path")
    args = parser.parse_args()

    try:
        errors = fetch_recent_errors(
            args.db,
            days=args.days,
            project=args.project,
            limit=args.limit,
        )
    except FileNotFoundError as exc:
        print(exc)
        return 1

    print(format_errors(errors))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
