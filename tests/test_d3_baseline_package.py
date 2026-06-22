"""Tests for standalone D3 baseline package validation."""

from __future__ import annotations

import json

import pytest

from qc_clean.core.d3_baseline_package import (
    build_d3_baseline_package_report,
    d3_baselines_payload_for_scorecard,
    validate_d3_baseline_package_payload,
)
from scripts import validate_d3_baseline_package
from scripts.bench_phase0 import load_d3_baselines_file


def test_validate_d3_baseline_package_accepts_application_package():
    """Versioned D3 baseline packages validate at their own boundary."""
    package = _valid_package()

    validated = validate_d3_baseline_package_payload(package)
    report = build_d3_baseline_package_report(validated)

    assert validated.package_type == "qualitative_coding.d3_application_baseline_predictions"
    assert report.status == "pass"
    assert report.prediction_package_type == "qualitative_coding.d3_application_baseline_predictions"
    assert report.project_id == "project-d3-baselines"
    assert report.baseline_mode == "single_prompt"
    assert report.baseline_count == 1
    assert report.baseline_names == ["single_prompt"]
    assert report.application_count == 1
    assert "not held-out D3 evidence" in report.caution


def test_validate_d3_baseline_package_rejects_malformed_versioned_package():
    """Recognized versioned packages fail when required metadata is missing."""
    malformed = {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_predictions",
        "application_baselines": [
            {
                "name": "single_prompt",
                "description": "",
                "code_applications": [_anchor()],
            }
        ],
    }

    with pytest.raises(ValueError, match="Invalid D3 baseline package"):
        validate_d3_baseline_package_payload(malformed)


def test_validate_d3_baseline_package_script_outputs_json(tmp_path, capsys):
    """The validator CLI emits machine-readable pass/fail output."""
    package_path = tmp_path / "d3_baseline.json"
    package_path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    exit_code = validate_d3_baseline_package.main([str(package_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "pass"
    assert output["baseline_count"] == 1
    assert output["application_count"] == 1

    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d3_application_baseline_predictions",
            "application_baselines": [],
        }),
        encoding="utf-8",
    )

    exit_code = validate_d3_baseline_package.main([str(malformed_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "fail"
    assert "Invalid D3 baseline package" in output["error"]


def test_phase0_d3_baselines_loader_validates_versioned_package(tmp_path):
    """The direct D3_BASELINES= loader validates recognized versioned packages."""
    package_path = tmp_path / "d3_package.json"
    package_path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    loaded = load_d3_baselines_file(package_path)

    assert loaded[0]["name"] == "single_prompt"
    assert loaded[0]["code_applications"][0]["code_id"] == "C1"
    assert loaded[0]["code_applications"][0]["segment_id"] is None

    malformed_path = tmp_path / "malformed_d3_package.json"
    malformed_path.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d3_application_baseline_predictions",
            "application_baselines": [
                {
                    "name": "single_prompt",
                    "description": "",
                    "code_applications": [_anchor()],
                }
            ],
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid D3 baseline package"):
        load_d3_baselines_file(malformed_path)


def test_phase0_d3_baselines_loader_preserves_legacy_inputs(tmp_path):
    """Legacy raw list and object inputs still feed the Phase 0 scorecard path."""
    raw_baselines = [
        {
            "name": "single_prompt",
            "description": "One baseline application.",
            "code_applications": [_anchor()],
        }
    ]
    raw_path = tmp_path / "raw_d3_baselines.json"
    raw_path.write_text(json.dumps(raw_baselines), encoding="utf-8")

    wrapped_path = tmp_path / "wrapped_d3_baselines.json"
    wrapped_path.write_text(
        json.dumps({"application_baselines": raw_baselines}),
        encoding="utf-8",
    )

    assert load_d3_baselines_file(raw_path) == raw_baselines
    assert load_d3_baselines_file(wrapped_path) == raw_baselines
    assert d3_baselines_payload_for_scorecard(raw_baselines) == raw_baselines


def _valid_package() -> dict:
    """Return a minimal valid versioned D3 baseline package."""
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_predictions",
        "application_baseline_run": {
            "project_id": "project-d3-baselines",
            "baseline_mode": "single_prompt",
            "generated_at": "2026-06-22T00:00:00Z",
            "model_name": "baseline-model",
            "application_count": 1,
            "notes": "Fixture package.",
        },
        "application_baselines": [
            {
                "name": "single_prompt",
                "description": "One baseline application.",
                "code_applications": [_anchor()],
            }
        ],
    }


def _anchor() -> dict:
    """Return a minimal scoreable D3 application anchor."""
    return {
        "code_id": "C1",
        "doc_id": "d1",
        "start_char": 0,
        "end_char": 5,
        "quote_text": "hello",
    }
