"""Tests for the product-gate evidence package writer script."""

import json

from scripts import verify_product_gate_package, write_product_gate_package


def test_write_product_gate_package_script_writes_output(tmp_path, capsys):
    reviewer = tmp_path / "reviewer_report.md"
    baseline = tmp_path / "report_baselines.json"
    output = tmp_path / "product_gate_package.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    baseline.write_text(json.dumps(_baseline_package("project-1")), encoding="utf-8")

    exit_code = write_product_gate_package.main([
        "project-1",
        "--reviewer-report",
        str(reviewer),
        "--baseline-package",
        str(baseline),
        "--output",
        str(output),
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.product_gate_evidence"
    assert [row["role"] for row in stdout_payload["artifacts"]] == [
        "reviewer_report",
        "baseline_package",
    ]


def test_write_product_gate_package_script_reports_invalid_json(tmp_path, capsys):
    reviewer = tmp_path / "reviewer_report.md"
    baseline = tmp_path / "report_baselines.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    baseline.write_text("{", encoding="utf-8")

    exit_code = write_product_gate_package.main([
        "project-1",
        "--reviewer-report",
        str(reviewer),
        "--baseline-package",
        str(baseline),
    ])

    assert exit_code == 1
    assert "error" in json.loads(capsys.readouterr().out)


def test_verify_product_gate_package_script_reports_hash_status(tmp_path, capsys):
    reviewer = tmp_path / "reviewer_report.md"
    package_path = tmp_path / "product_gate_package.json"
    report_path = tmp_path / "product_gate_verification.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    assert write_product_gate_package.main([
        "project-1",
        "--reviewer-report",
        str(reviewer),
        "--output",
        str(package_path),
    ]) == 0
    capsys.readouterr()

    exit_code = verify_product_gate_package.main([
        str(package_path),
        "--output",
        str(report_path),
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["ok"] is True


def test_verify_product_gate_package_script_returns_failure_on_mismatch(tmp_path, capsys):
    reviewer = tmp_path / "reviewer_report.md"
    package_path = tmp_path / "product_gate_package.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    assert write_product_gate_package.main([
        "project-1",
        "--reviewer-report",
        str(reviewer),
        "--output",
        str(package_path),
    ]) == 0
    capsys.readouterr()
    reviewer.write_text("# Changed\n", encoding="utf-8")

    exit_code = verify_product_gate_package.main([str(package_path)])

    assert exit_code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False


def _baseline_package(project_id: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_outputs",
        "report_baseline_run": {"project_id": project_id},
    }
