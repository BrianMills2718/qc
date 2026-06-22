"""Tests for D7 comparison artifact verification."""

from __future__ import annotations

import hashlib
import json

from scripts import verify_d7_comparison_artifact


def test_verify_d7_comparison_artifact_accepts_matching_package(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)

    exit_code = verify_d7_comparison_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "verified"
    assert output["artifact_type"] == "qualitative_coding.d7_retrieval_comparison"
    assert output["project_id"] == "project-d7"
    assert output["checked_report_count"] == 1
    assert output["failure_count"] == 0
    assert output["failures"] == []
    assert "not held-out D7 evidence" in output["caveat"]


def test_verify_d7_comparison_artifact_accepts_manifest_path(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)

    exit_code = verify_d7_comparison_artifact.main([str(run_dir / "manifest.json")])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "verified"
    assert output["manifest_path"] == str(run_dir / "manifest.json")
    assert output["report_path"] == str(run_dir / "report.json")


def test_verify_d7_comparison_artifact_detects_report_hash_mismatch(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)
    report_path = run_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["report_type"] = "tampered"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    exit_code = verify_d7_comparison_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    assert any(failure["code"] == "report_sha256_mismatch" for failure in output["failures"])


def test_verify_d7_comparison_artifact_detects_metadata_mismatch(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["input_hashes"]["gold_file_sha256"] = "0" * 64
    manifest["command"]["gold_file"] = "other_gold.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    exit_code = verify_d7_comparison_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    failure_codes = {failure["code"] for failure in output["failures"]}
    assert "input_hashes_mismatch" in failure_codes
    assert "command_mismatch" in failure_codes


def test_verify_d7_comparison_artifact_detects_missing_report(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)
    (run_dir / "report.json").unlink()

    exit_code = verify_d7_comparison_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    assert output["checked_report_count"] == 0
    assert any(failure["code"] == "report_file_missing" for failure in output["failures"])


def _artifact_package(tmp_path):
    run_dir = tmp_path / "20260622T000000000000Z-project-d7-d7-comparison"
    run_dir.mkdir()
    report = {
        "report_type": "qualitative_coding.d7_retrieval_comparison",
        "disconfirmation_d7": {"status": "available"},
        "_meta": {
            "input_hashes": {
                "hash_algorithm": "sha256",
                "project_id": "project-d7",
                "project_state_sha256": "1" * 64,
                "corpus_sha256": "2" * 64,
                "gold_file_sha256": "3" * 64,
                "prediction_files": [
                    {"path": "predictions.json", "sha256": "4" * 64}
                ],
                "protocol_file_sha256": "5" * 64,
            },
            "command": {
                "project_id": "project-d7",
                "gold_file": "gold.json",
                "prediction_files": ["predictions.json"],
                "protocol_package": "protocol.json",
                "output": "report.json",
                "artifact_dir": "artifacts",
            },
        },
    }
    report_text = json.dumps(report, indent=2)
    report_path = run_dir / "report.json"
    report_path.write_text(report_text, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.d7_retrieval_comparison",
        "generated_at": "2026-06-22T00:00:00Z",
        "project_id": "project-d7",
        "project_name": "D7 test",
        "report_file": "report.json",
        "report_sha256": hashlib.sha256(report_text.encode("utf-8")).hexdigest(),
        "input_hashes": report["_meta"]["input_hashes"],
        "command": report["_meta"]["command"],
        "claim_discipline": {
            "caveat": (
                "This D7 comparison artifact is local provenance/accounting "
                "metadata only; it is not held-out D7 evidence."
            )
        },
        "prompt_eval": {
            "status": "not_run",
            "owner": "prompt_eval",
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return run_dir
