"""Tests for export audit hash manifests."""

import hashlib
import json
from pathlib import Path

import pytest

from qc_clean.core.export.audit_manifest import (
    build_export_audit_manifest,
    verify_export_audit_manifest_payload,
    write_export_audit_manifest,
)
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import ProjectState


def test_build_export_audit_manifest_hashes_single_artifact(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n\nBounded to these documents.\n", encoding="utf-8")

    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    )
    payload = manifest.model_dump(mode="json")

    assert payload["schema_version"] == 1
    assert payload["package_type"] == "export_audit_manifest"
    assert payload["export_format"] == "markdown"
    assert payload["project_id"] == "manifest-project"
    assert payload["project_name"] == "Manifest Project"
    assert payload["hash_algorithm"] == "sha256"
    assert payload["project_state_sha256"] == _sha256_jsonable(state.model_dump(mode="json"))
    assert payload["artifact_count"] == 1
    assert payload["artifacts"][0]["path"] == "report.md"
    assert payload["artifacts"][0]["size_bytes"] == report_path.stat().st_size
    assert payload["artifacts"][0]["sha256"] == _sha256_bytes(report_path.read_bytes())
    assert len(payload["manifest_sha256"]) == 64
    assert payload["manifest_sha256"] == _manifest_hash(payload)
    assert "not a complete tamper-evident audit log" in payload["caveat"]


def test_build_export_audit_manifest_hashes_multiple_csv_artifacts(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    b_path = tmp_path / "b.csv"
    a_path = tmp_path / "a.csv"
    b_path.write_text("b\n", encoding="utf-8")
    a_path.write_text("a\n", encoding="utf-8")

    manifest = build_export_audit_manifest(
        state,
        export_format="csv",
        artifact_paths=[b_path, a_path],
        base_dir=tmp_path,
    ).model_dump(mode="json")

    assert manifest["artifact_count"] == 2
    assert [artifact["path"] for artifact in manifest["artifacts"]] == ["a.csv", "b.csv"]
    assert [artifact["sha256"] for artifact in manifest["artifacts"]] == [
        _sha256_bytes(a_path.read_bytes()),
        _sha256_bytes(b_path.read_bytes()),
    ]


def test_build_export_audit_manifest_rejects_missing_artifact(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")

    with pytest.raises(ValueError, match="does not exist"):
        build_export_audit_manifest(
            state,
            export_format="json",
            artifact_paths=[tmp_path / "missing.json"],
            base_dir=tmp_path,
        )


def test_write_export_audit_manifest_script(tmp_path, capsys):
    from scripts import write_export_audit_manifest as script

    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    state = ProjectState(id="manifest-project", name="Manifest Project")
    store.save(state)

    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    output_path = tmp_path / "manifest.json"

    ok_exit = script.main(
        [
            "manifest-project",
            "--format",
            "markdown",
            "--artifact",
            str(report_path),
            "--output",
            str(output_path),
            "--base-dir",
            str(tmp_path),
            "--projects-dir",
            str(projects_dir),
        ]
    )
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert ok_exit == 0
    assert stdout_payload == file_payload
    assert stdout_payload["artifact_count"] == 1
    assert stdout_payload["artifacts"][0]["path"] == "report.md"

    bad_exit = script.main(
        [
            "manifest-project",
            "--format",
            "markdown",
            "--artifact",
            str(tmp_path / "missing.md"),
            "--output",
            str(output_path),
            "--projects-dir",
            str(projects_dir),
        ]
    )
    error_payload = json.loads(capsys.readouterr().out)

    assert bad_exit == 1
    assert error_payload["status"] == "error"
    assert "does not exist" in error_payload["error"]


def test_verify_export_audit_manifest_accepts_matching_files(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    )

    report = verify_export_audit_manifest_payload(
        manifest.model_dump(mode="json"),
        base_dir=tmp_path,
        state=state,
    ).model_dump(mode="json")

    assert report["status"] == "verified"
    assert report["manifest_self_hash_status"] == "verified"
    assert report["project_state_hash_status"] == "verified"
    assert report["artifact_count"] == 1
    assert report["checked_artifact_count"] == 1
    assert report["failure_count"] == 0
    assert report["failures"] == []
    assert "not a signed or append-only audit log" in report["caveat"]


def test_verify_export_audit_manifest_detects_artifact_hash_mismatch(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("abc", encoding="utf-8")
    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    )
    report_path.write_text("xyz", encoding="utf-8")

    report = verify_export_audit_manifest_payload(
        manifest.model_dump(mode="json"),
        base_dir=tmp_path,
    ).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert report["project_state_hash_status"] == "not_checked"
    assert any(failure["code"] == "artifact_sha256_mismatch" for failure in report["failures"])


def test_verify_export_audit_manifest_detects_manifest_hash_mismatch(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    payload = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    ).model_dump(mode="json")
    payload["project_name"] = "Tampered Project"

    report = verify_export_audit_manifest_payload(payload, base_dir=tmp_path).model_dump(
        mode="json"
    )

    assert report["status"] == "invalid"
    assert report["manifest_self_hash_status"] == "invalid"
    assert any(failure["code"] == "manifest_sha256_mismatch" for failure in report["failures"])


def test_verify_export_audit_manifest_detects_project_state_mismatch(tmp_path):
    state = ProjectState(id="manifest-project", name="Manifest Project")
    changed_state = ProjectState(id="manifest-project", name="Changed Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    )

    report = verify_export_audit_manifest_payload(
        manifest.model_dump(mode="json"),
        base_dir=tmp_path,
        state=changed_state,
    ).model_dump(mode="json")

    assert report["status"] == "invalid"
    assert report["project_state_hash_status"] == "invalid"
    assert any(
        failure["code"] == "project_state_sha256_mismatch" for failure in report["failures"]
    )


def test_verify_export_audit_manifest_script(tmp_path, capsys):
    from scripts import verify_export_audit_manifest as script

    state = ProjectState(id="manifest-project", name="Manifest Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=tmp_path,
    )
    manifest_path = tmp_path / "manifest.json"
    write_export_audit_manifest(manifest, manifest_path)

    ok_exit = script.main([str(manifest_path), "--base-dir", str(tmp_path)])
    ok_report = json.loads(capsys.readouterr().out)

    assert ok_exit == 0
    assert ok_report["status"] == "verified"

    report_path.write_text("Changed\n", encoding="utf-8")

    bad_exit = script.main([str(manifest_path), "--base-dir", str(tmp_path)])
    bad_report = json.loads(capsys.readouterr().out)

    assert bad_exit == 1
    assert bad_report["status"] == "invalid"
    assert any(failure["code"] == "artifact_sha256_mismatch" for failure in bad_report["failures"])


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_jsonable(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()


def _manifest_hash(payload: dict) -> str:
    manifest_without_hash = dict(payload)
    manifest_without_hash["manifest_sha256"] = ""
    return _sha256_jsonable(manifest_without_hash)
