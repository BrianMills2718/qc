"""Tests for product-gate evidence package construction."""

import json

import pytest

from qc_clean.core.product_gate_package import build_product_gate_package


def test_build_product_gate_package_hashes_artifacts_and_validates_project_ids(tmp_path):
    reviewer = tmp_path / "reviewer_report.md"
    baseline = tmp_path / "report_baselines.json"
    comparison = tmp_path / "report_baseline_comparison.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    baseline.write_text(json.dumps(_baseline_package("project-1")), encoding="utf-8")
    comparison.write_text(json.dumps(_comparison_package("project-1")), encoding="utf-8")

    package = build_product_gate_package(
        project_id="project-1",
        reviewer_report=reviewer,
        baseline_package=baseline,
        baseline_comparison=comparison,
    )

    assert package["package_type"] == "qualitative_coding.product_gate_evidence"
    assert package["project_id"] == "project-1"
    roles = {artifact["role"]: artifact for artifact in package["artifacts"]}
    assert set(roles) == {"reviewer_report", "baseline_package", "baseline_comparison"}
    assert roles["reviewer_report"]["sha256"]
    assert roles["reviewer_report"]["byte_size"] == len("# Reviewer\n")
    assert roles["baseline_package"]["package_type"] == (
        "qualitative_coding.report_baseline_outputs"
    )
    assert "not a SOTA" in package["caution"]


def test_build_product_gate_package_fails_on_mismatched_known_project_id(tmp_path):
    reviewer = tmp_path / "reviewer_report.md"
    baseline = tmp_path / "report_baselines.json"
    reviewer.write_text("# Reviewer\n", encoding="utf-8")
    baseline.write_text(json.dumps(_baseline_package("other-project")), encoding="utf-8")

    with pytest.raises(ValueError, match="baseline_package artifact project_id"):
        build_product_gate_package(
            project_id="project-1",
            reviewer_report=reviewer,
            baseline_package=baseline,
        )


def _baseline_package(project_id: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_outputs",
        "report_baseline_run": {
            "project_id": project_id,
            "project_name": "Report Baseline Test",
            "generated_at": "2026-06-26T00:00:00Z",
            "model_name": "fake-model",
            "baseline_modes": ["direct_report"],
            "corpus_document_count": 1,
            "max_chars_per_doc": None,
            "notes": "",
        },
        "report_baselines": [],
        "caution": "comparison only",
    }


def _comparison_package(project_id: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_comparison",
        "comparison": {
            "generated_at": "2026-06-26T00:00:00Z",
            "rubric_id": "rubric",
            "structured_report_path": "reviewer_report.md",
            "baseline_package_path": "report_baselines.json",
            "baseline_project_id": project_id,
        },
        "artifact_scores": [],
        "ranking": [],
        "caution": "comparison only",
    }
