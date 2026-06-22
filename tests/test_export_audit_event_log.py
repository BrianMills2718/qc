"""Tests for local export audit event logs."""

import json

from qc_clean.core.export.audit_event_log import (
    append_export_audit_event,
    verify_export_audit_event_db,
    verify_export_audit_event_log,
)
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import ProjectState


def test_export_audit_event_log_appends_hash_linked_events(tmp_path):
    log_path = tmp_path / "export_audit_events.jsonl"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_sha256": "abc"}', encoding="utf-8")

    first = append_export_audit_event(
        log_path,
        event_type="manifest_written",
        event_status="success",
        manifest_path=manifest_path,
        payload={"status": "written"},
    )
    second = append_export_audit_event(
        log_path,
        event_type="manifest_verified",
        event_status="verified",
        manifest_path=manifest_path,
        payload={"status": "verified"},
    )
    lines = _read_jsonl(log_path)
    report = verify_export_audit_event_log(log_path).model_dump(mode="json")

    assert len(lines) == 2
    assert first.previous_event_sha256 is None
    assert len(first.event_sha256) == 64
    assert second.previous_event_sha256 == first.event_sha256
    assert lines[1]["previous_event_sha256"] == lines[0]["event_sha256"]
    assert report["status"] == "verified"
    assert report["event_count"] == 2
    assert report["failure_count"] == 0
    assert "not signing" in report["caveat"]


def test_export_audit_event_log_detects_modified_event(tmp_path):
    log_path = tmp_path / "export_audit_events.jsonl"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_sha256": "abc"}', encoding="utf-8")
    append_export_audit_event(
        log_path,
        event_type="manifest_written",
        event_status="success",
        manifest_path=manifest_path,
        payload={"status": "written"},
    )

    event = _read_jsonl(log_path)[0]
    event["event_status"] = "tampered"
    log_path.write_text(json.dumps(event) + "\n", encoding="utf-8")

    report = verify_export_audit_event_log(log_path).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert report["failure_count"] == 1
    assert report["failures"][0]["code"] == "event_sha256_mismatch"


def test_export_audit_event_log_missing_file_fails(tmp_path, capsys):
    from scripts import verify_export_audit_event_log as script

    log_path = tmp_path / "missing.jsonl"

    report = verify_export_audit_event_log(log_path).model_dump(mode="json")
    exit_code = script.main([str(log_path)])
    stdout_report = json.loads(capsys.readouterr().out)

    assert report["status"] == "invalid"
    assert report["failures"][0]["code"] == "log_missing"
    assert exit_code == 1
    assert stdout_report["status"] == "invalid"
    assert stdout_report["failures"][0]["code"] == "log_missing"


def test_export_audit_scripts_write_opt_in_events(tmp_path, capsys):
    from scripts import export_publish_preflight
    from scripts import verify_export_audit_event_log as verify_log_script
    from scripts import verify_export_audit_manifest
    from scripts import write_export_audit_manifest

    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    state = ProjectState(id="event-log-project", name="Event Log Project")
    store.save(state)
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    log_path = tmp_path / "export_audit_events.jsonl"
    db_path = tmp_path / "export_audit_events.sqlite"

    write_exit = write_export_audit_manifest.main(
        [
            state.id,
            "--format",
            "markdown",
            "--artifact",
            str(report_path),
            "--output",
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--projects-dir",
            str(projects_dir),
            "--audit-log",
            str(log_path),
            "--audit-db",
            str(db_path),
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)

    verify_exit = verify_export_audit_manifest.main(
        [
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--project-id",
            state.id,
            "--projects-dir",
            str(projects_dir),
            "--audit-log",
            str(log_path),
            "--audit-db",
            str(db_path),
        ]
    )
    verify_payload = json.loads(capsys.readouterr().out)

    preflight_exit = export_publish_preflight.main(
        [
            "--manifest",
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--project-id",
            state.id,
            "--projects-dir",
            str(projects_dir),
            "--audit-log",
            str(log_path),
            "--audit-db",
            str(db_path),
        ]
    )
    preflight_payload = json.loads(capsys.readouterr().out)

    log_exit = verify_log_script.main([str(log_path)])
    log_report = json.loads(capsys.readouterr().out)
    db_report = verify_export_audit_event_db(db_path).model_dump(mode="json")
    events = _read_jsonl(log_path)

    assert write_exit == 0
    assert verify_exit == 0
    assert preflight_exit == 0
    assert write_payload["package_type"] == "export_audit_manifest"
    assert verify_payload["status"] == "verified"
    assert preflight_payload["status"] == "pass"
    assert [event["event_type"] for event in events] == [
        "manifest_written",
        "manifest_verified",
        "publish_preflight",
    ]
    assert events[0]["event_status"] == "success"
    assert events[1]["event_status"] == "verified"
    assert events[2]["event_status"] == "pass"
    assert events[1]["previous_event_sha256"] == events[0]["event_sha256"]
    assert events[2]["previous_event_sha256"] == events[1]["event_sha256"]
    assert log_exit == 0
    assert log_report["status"] == "verified"
    assert log_report["event_count"] == 3
    assert db_report["status"] == "verified"
    assert db_report["event_count"] == 3


def test_export_audit_scripts_reject_audit_db_without_log(tmp_path, capsys):
    from scripts import export_publish_preflight
    from scripts import verify_export_audit_manifest
    from scripts import write_export_audit_manifest

    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    state = ProjectState(id="event-db-project", name="Event DB Project")
    store.save(state)
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    db_path = tmp_path / "export_audit_events.sqlite"

    write_exit = write_export_audit_manifest.main(
        [
            state.id,
            "--format",
            "markdown",
            "--artifact",
            str(report_path),
            "--output",
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--projects-dir",
            str(projects_dir),
            "--audit-db",
            str(db_path),
        ]
    )
    write_payload = json.loads(capsys.readouterr().out)

    manifest_path.write_text(
        json.dumps({"package_type": "not_a_manifest"}),
        encoding="utf-8",
    )
    verify_exit = verify_export_audit_manifest.main(
        [
            str(manifest_path),
            "--audit-db",
            str(db_path),
        ]
    )
    verify_payload = json.loads(capsys.readouterr().out)

    preflight_exit = export_publish_preflight.main(
        [
            "--manifest",
            str(manifest_path),
            "--audit-db",
            str(db_path),
        ]
    )
    preflight_payload = json.loads(capsys.readouterr().out)

    assert write_exit == 1
    assert verify_exit == 1
    assert preflight_exit == 1
    assert "--audit-db requires --audit-log" in write_payload["error"]
    assert "--audit-db requires --audit-log" in verify_payload["error"]
    assert "--audit-db requires --audit-log" in preflight_payload["error"]
    assert not db_path.exists()


def _read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
