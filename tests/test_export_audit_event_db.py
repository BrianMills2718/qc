"""Tests for optional SQLite mirrors of export audit event logs."""

import json
import sqlite3

import pytest

from qc_clean.core.export.audit_event_log import (
    append_export_audit_event,
    mirror_export_audit_event_log_to_sqlite,
    verify_export_audit_event_db,
)


def test_export_audit_event_log_can_be_mirrored_to_sqlite(tmp_path, capsys):
    """Verified JSONL audit events can be mirrored and verified in SQLite."""
    from scripts import mirror_export_audit_event_log_db as mirror_script
    from scripts import verify_export_audit_event_db as verify_script

    log_path = tmp_path / "export_audit_events.jsonl"
    db_path = tmp_path / "export_audit_events.sqlite"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_sha256": "abc"}', encoding="utf-8")
    first = append_export_audit_event(
        log_path,
        event_type="manifest_written",
        event_status="success",
        manifest_path=manifest_path,
        payload={"status": "written"},
    )
    append_export_audit_event(
        log_path,
        event_type="manifest_verified",
        event_status="verified",
        manifest_path=manifest_path,
        payload={"status": "verified"},
    )

    report = mirror_export_audit_event_log_to_sqlite(log_path, db_path).model_dump(mode="json")
    verification = verify_export_audit_event_db(db_path).model_dump(mode="json")
    script_exit = mirror_script.main([str(log_path), "--db", str(db_path)])
    mirror_stdout = json.loads(capsys.readouterr().out)
    verify_exit = verify_script.main([str(db_path)])
    verify_stdout = json.loads(capsys.readouterr().out)

    assert report["status"] == "mirrored"
    assert report["source_event_count"] == 2
    assert report["inserted_event_count"] == 2
    assert report["total_event_count"] == 2
    assert verification["status"] == "verified"
    assert verification["event_count"] == 2
    assert verification["failure_count"] == 0
    assert "not signing" in verification["caveat"]
    assert script_exit == 0
    assert mirror_stdout["status"] == "mirrored"
    assert mirror_stdout["inserted_event_count"] == 0
    assert verify_exit == 0
    assert verify_stdout["status"] == "verified"

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT sequence, event_sha256, previous_event_sha256 FROM export_audit_events "
            "ORDER BY sequence"
        ).fetchall()
    assert rows[0] == (1, first.event_sha256, None)
    assert rows[1][2] == first.event_sha256


def test_export_audit_event_db_mirror_rejects_invalid_source_log(tmp_path):
    """Invalid JSONL logs fail before the SQLite mirror is written."""
    log_path = tmp_path / "export_audit_events.jsonl"
    db_path = tmp_path / "export_audit_events.sqlite"
    log_path.write_text('{"bad": true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="Cannot mirror invalid export audit event log"):
        mirror_export_audit_event_log_to_sqlite(log_path, db_path)

    assert not db_path.exists()


def test_export_audit_event_db_verifier_detects_tampered_payload(tmp_path):
    """SQLite verifier detects modified stored event payloads."""
    log_path = tmp_path / "export_audit_events.jsonl"
    db_path = tmp_path / "export_audit_events.sqlite"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_sha256": "abc"}', encoding="utf-8")
    append_export_audit_event(
        log_path,
        event_type="manifest_written",
        event_status="success",
        manifest_path=manifest_path,
        payload={"status": "written"},
    )
    mirror_export_audit_event_log_to_sqlite(log_path, db_path)

    with sqlite3.connect(db_path) as conn:
        payload_json = conn.execute(
            "SELECT event_payload_json FROM export_audit_events WHERE sequence = 1"
        ).fetchone()[0]
        payload = json.loads(payload_json)
        payload["event_status"] = "tampered"
        conn.execute(
            "UPDATE export_audit_events SET event_payload_json = ? WHERE sequence = 1",
            (json.dumps(payload, sort_keys=True),),
        )

    report = verify_export_audit_event_db(db_path).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert report["failure_count"] == 1
    assert report["failures"][0]["code"] == "event_sha256_mismatch"
