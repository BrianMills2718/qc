"""Tests for manifest-driven D7 comparison package execution."""

from __future__ import annotations

import json
from types import SimpleNamespace

from scripts import (
    compare_d7_retrieval,
    run_d7_comparison_package,
    verify_d7_comparison_artifact,
)


def test_d7_comparison_package_forwards_relative_inputs(tmp_path, monkeypatch):
    captured = {}

    def fake_compare_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(compare_d7_retrieval, "main", fake_compare_main)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_path = _write_package(
        package_dir,
        {
            "schema_version": 1,
            "project_id": "project-d7",
            "gold_file": "gold.json",
            "prediction_files": ["lexical.json", "embedding.json"],
            "protocol_package": "protocol.json",
            "output": "comparison.json",
            "artifact_dir": "artifacts",
        },
    )

    exit_code = run_d7_comparison_package.main([str(package_path)])

    assert exit_code == 0
    assert captured["argv"] == [
        "project-d7",
        "--gold-file",
        str(package_dir / "gold.json"),
        "--predictions-file",
        str(package_dir / "lexical.json"),
        "--predictions-file",
        str(package_dir / "embedding.json"),
        "--output",
        str(package_dir / "comparison.json"),
        "--protocol-package",
        str(package_dir / "protocol.json"),
        "--artifact-dir",
        str(package_dir / "artifacts"),
    ]


def test_d7_comparison_package_rejects_invalid_manifest(tmp_path, monkeypatch, capsys):
    def fail_if_called(_argv):
        raise AssertionError("comparison should not run for invalid package")

    monkeypatch.setattr(compare_d7_retrieval, "main", fail_if_called)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_path = _write_package(
        package_dir,
        {
            "schema_version": 1,
            "project_id": "project-d7",
            "gold_file": "gold.json",
            "prediction_files": [],
        },
    )

    exit_code = run_d7_comparison_package.main([str(package_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "prediction_files" in output["error"]


def test_d7_comparison_package_verifies_created_artifact_when_requested(
    tmp_path,
    monkeypatch,
):
    captured = {}
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    artifact_root = package_dir / "artifacts"

    def fake_compare_main(argv):
        captured["compare_argv"] = argv
        (artifact_root / "created-run").mkdir(parents=True)
        return 0

    def fake_verify_artifact(path):
        captured["verify_path"] = path
        return SimpleNamespace(status="verified")

    monkeypatch.setattr(compare_d7_retrieval, "main", fake_compare_main)
    monkeypatch.setattr(
        verify_d7_comparison_artifact,
        "verify_d7_comparison_artifact",
        fake_verify_artifact,
    )
    package_path = _write_package(
        package_dir,
        {
            "schema_version": 1,
            "project_id": "project-d7",
            "gold_file": "gold.json",
            "prediction_files": ["lexical.json"],
            "artifact_dir": "artifacts",
            "verify_artifact": True,
        },
    )

    exit_code = run_d7_comparison_package.main([str(package_path)])

    assert exit_code == 0
    assert captured["compare_argv"][-2:] == ["--artifact-dir", str(artifact_root)]
    assert captured["verify_path"] == artifact_root / "created-run"


def _write_package(package_dir, payload):
    path = package_dir / "d7_comparison_package.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
