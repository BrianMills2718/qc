"""Tests for observability error reporting helpers."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from scripts.recent_errors import fetch_recent_errors, format_errors


def _create_observability_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE llm_calls (
                timestamp TEXT,
                project TEXT,
                task TEXT,
                trace_id TEXT,
                error TEXT,
                error_type TEXT,
                validation_errors TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE tool_calls (
                timestamp TEXT,
                project TEXT,
                task TEXT,
                trace_id TEXT,
                status TEXT,
                error_type TEXT,
                error_message TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def test_fetch_recent_errors_filters_and_orders_rows(tmp_path: Path) -> None:
    """Recent project-matching LLM and tool failures are returned newest first."""
    db_path = tmp_path / "observability.db"
    _create_observability_db(db_path)
    now = datetime.now()

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO llm_calls VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                (now - timedelta(minutes=5)).isoformat(),
                "qualitative_coding",
                "pipeline",
                "trace-llm",
                "bad schema",
                "ValidationError",
                None,
            ),
        )
        conn.execute(
            "INSERT INTO tool_calls VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                now.isoformat(),
                "qualitative_coding",
                "fetch",
                "trace-tool",
                "failed",
                None,
                "network down",
            ),
        )
        conn.execute(
            "INSERT INTO llm_calls VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                (now - timedelta(days=9)).isoformat(),
                "qualitative_coding",
                "old",
                "trace-old",
                "old failure",
                None,
                None,
            ),
        )
        conn.execute(
            "INSERT INTO tool_calls VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                now.isoformat(),
                "other_project",
                "other",
                "trace-other",
                "failed",
                None,
                "ignored",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    errors = fetch_recent_errors(db_path, days=7, project="qualitative_coding", limit=10)

    assert [(err.source, err.trace_id, err.detail) for err in errors] == [
        ("tool", "trace-tool", "network down"),
        ("llm", "trace-llm", "ValidationError"),
    ]
    formatted = format_errors(errors)
    assert "Recent errors:" in formatted
    assert "trace-tool" in formatted
    assert "ValidationError" in formatted


def test_fetch_recent_errors_respects_zero_limit(tmp_path: Path) -> None:
    """A zero limit avoids touching the database."""
    missing_db = tmp_path / "missing.db"

    assert fetch_recent_errors(missing_db, days=7, project="qualitative_coding", limit=0) == []
