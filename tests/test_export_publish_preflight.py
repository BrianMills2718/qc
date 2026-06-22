"""Tests for strict export publish preflight."""

import json

from qc_clean.core.export.audit_manifest import (
    build_export_audit_manifest,
    write_export_audit_manifest,
)
from qc_clean.core.export.publish_preflight import run_export_publish_preflight
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import ProjectState


def test_export_publish_preflight_passes_with_verified_manifest(tmp_path):
    state = ProjectState(id="preflight-project", name="Preflight Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = _write_manifest(state, report_path, tmp_path)

    report = run_export_publish_preflight(
        manifest_path,
        base_dir=tmp_path,
        state=state,
    ).model_dump(mode="json")

    assert report["status"] == "pass"
    assert report["manifest_path"] == str(manifest_path)
    assert report["verification"]["status"] == "verified"
    assert report["failure_count"] == 0
    assert report["failures"] == []
    assert "not signing" in report["caveat"]


def test_export_publish_preflight_fails_when_artifact_changes(tmp_path):
    state = ProjectState(id="preflight-project", name="Preflight Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = _write_manifest(state, report_path, tmp_path)
    report_path.write_text("# Changed\n", encoding="utf-8")

    report = run_export_publish_preflight(
        manifest_path,
        base_dir=tmp_path,
    ).model_dump(mode="json")

    assert report["status"] == "fail"
    assert report["verification"]["status"] == "invalid"
    assert any(failure["code"] == "artifact_sha256_mismatch" for failure in report["failures"])


def test_export_publish_preflight_fails_missing_manifest(tmp_path):
    missing = tmp_path / "missing.manifest.json"

    report = run_export_publish_preflight(missing, base_dir=tmp_path).model_dump(mode="json")

    assert report["status"] == "fail"
    assert report["manifest_path"] == str(missing)
    assert report["failure_count"] == 1
    assert report["failures"][0]["code"] == "manifest_missing"


def test_export_publish_preflight_checks_project_state_when_supplied(tmp_path):
    original = ProjectState(id="preflight-project", name="Preflight Project")
    changed = ProjectState(id="preflight-project", name="Changed Project")
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = _write_manifest(original, report_path, tmp_path)

    report = run_export_publish_preflight(
        manifest_path,
        base_dir=tmp_path,
        state=changed,
    ).model_dump(mode="json")

    assert report["status"] == "fail"
    assert any(
        failure["code"] == "project_state_sha256_mismatch" for failure in report["failures"]
    )


def test_export_publish_preflight_script_exit_codes(tmp_path, capsys):
    from scripts import export_publish_preflight

    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    state = ProjectState(id="preflight-project", name="Preflight Project")
    store.save(state)
    report_path = tmp_path / "report.md"
    report_path.write_text("# Report\n", encoding="utf-8")
    manifest_path = _write_manifest(state, report_path, tmp_path)

    pass_exit = export_publish_preflight.main(
        [
            "--manifest",
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--project-id",
            state.id,
            "--projects-dir",
            str(projects_dir),
        ]
    )
    pass_payload = json.loads(capsys.readouterr().out)

    assert pass_exit == 0
    assert pass_payload["status"] == "pass"

    report_path.write_text("# Changed\n", encoding="utf-8")
    fail_exit = export_publish_preflight.main(
        [
            "--manifest",
            str(manifest_path),
            "--base-dir",
            str(tmp_path),
            "--project-id",
            state.id,
            "--projects-dir",
            str(projects_dir),
        ]
    )
    fail_payload = json.loads(capsys.readouterr().out)

    assert fail_exit == 1
    assert fail_payload["status"] == "fail"


def _write_manifest(state: ProjectState, report_path, base_dir):
    manifest = build_export_audit_manifest(
        state,
        export_format="markdown",
        artifact_paths=[report_path],
        base_dir=base_dir,
    )
    manifest_path = base_dir / "report.manifest.json"
    write_export_audit_manifest(manifest, manifest_path)
    return manifest_path
