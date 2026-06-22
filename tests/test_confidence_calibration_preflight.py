"""Tests for confidence-calibration protocol/result preflight."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qc_clean.core.confidence_calibration_preflight import (
    preflight_confidence_calibration_payloads,
)
from scripts import preflight_confidence_calibration_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_PREDICTION_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_preflight_confidence_calibration_passes_matching_protocol_and_results():
    report = preflight_confidence_calibration_payloads(
        _protocol_payload(planned_item_count=2),
        _calibration_payload(),
        calibration_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "confidence-calibration-heldout-v1"
    assert report.project_id == "project-alpha"
    assert report.split == "held_out"
    assert report.target_surfaces == ["thematic_coding", "negative_case"]
    assert report.outcome_metrics == [
        "accuracy",
        "brier_score",
        "expected_calibration_error",
    ]
    assert report.confidence_source == "system_confidence_field"
    assert report.result_row_count == 2
    assert report.item_count == 2
    assert report.evaluator_count == 1
    assert report.evaluators == ["expert_adjudication"]
    assert report.errors == []
    assert "not calibration proof" in report.caution


def test_preflight_confidence_calibration_requires_result_payload():
    report = preflight_confidence_calibration_payloads(
        _protocol_payload(planned_item_count=2),
        None,
    )

    assert report.status == "fail"
    assert [(error.field, error.message) for error in report.errors] == [
        (
            "calibration_file",
            "Confidence-calibration preflight requires a calibration result file",
        )
    ]


def test_preflight_confidence_calibration_reports_hash_and_surface_mismatches():
    report = preflight_confidence_calibration_payloads(
        _protocol_payload(planned_item_count=2),
        _calibration_payload(),
        calibration_file_sha256="0" * 64,
    )

    assert report.status == "fail"
    assert _error_fields(report) == ["calibration_file_sha256"]
    assert "does not match actual file hash" in report.errors[0].message

    payload = _calibration_payload()
    payload["confidence_calibration_evaluations"][1]["surface"] = "synthesis"

    report = preflight_confidence_calibration_payloads(
        _protocol_payload(planned_item_count=2),
        payload,
        calibration_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    assert _error_fields(report) == ["target_surfaces"]
    assert "missing: negative_case" in report.errors[0].message
    assert "unexpected: synthesis" in report.errors[0].message


def test_preflight_confidence_calibration_reports_label_source_and_item_count_mismatches():
    payload = _calibration_payload()
    for row in payload["confidence_calibration_evaluations"]:
        row["evaluator"] = "llm_judge"

    report = preflight_confidence_calibration_payloads(
        _protocol_payload(planned_item_count=3),
        payload,
        calibration_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    assert _error_fields(report) == ["label_sources", "planned_item_count"]
    assert "missing: expert_adjudication" in report.errors[0].message
    assert "unexpected: llm_judge" in report.errors[0].message
    assert "2 unique item(s), below planned count 3" in report.errors[1].message


def test_preflight_confidence_calibration_script_outputs_json(tmp_path, capsys):
    protocol_file = tmp_path / "protocol.json"
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(json.dumps(_calibration_payload()), encoding="utf-8")
    protocol_file.write_text(
        json.dumps(
            _protocol_payload(
                calibration_hash=_sha256_file(calibration_file),
                planned_item_count=2,
            )
        ),
        encoding="utf-8",
    )

    exit_code = preflight_confidence_calibration_protocol.main(
        [str(protocol_file), "--calibration-file", str(calibration_file)]
    )

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "pass"
    assert output["package_type"] == "confidence_calibration_protocol_result_preflight"
    assert output["result_row_count"] == 2
    assert output["errors"] == []

    invalid_protocol_file = tmp_path / "invalid_protocol.json"
    invalid_protocol_file.write_text(
        json.dumps(
            _protocol_payload(
                calibration_hash="0" * 64,
                planned_item_count=2,
            )
        ),
        encoding="utf-8",
    )

    exit_code = preflight_confidence_calibration_protocol.main(
        [str(invalid_protocol_file), "--calibration-file", str(calibration_file)]
    )

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "fail"
    assert [error["field"] for error in output["errors"]] == [
        "calibration_file_sha256"
    ]


def _protocol_payload(
    *,
    calibration_hash: str = _OUTCOME_HASH,
    planned_item_count: int = 30,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.confidence_calibration_protocol",
        "protocol_id": "confidence-calibration-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Confidence calibration held-out v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "prediction_artifact_sha256": _PREDICTION_ARTIFACT_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "label_plan": {
            "label_sources": ["expert_adjudication"],
            "planned_labeler_count": 2,
            "qualification": "Expert adjudicators label correctness of predictions.",
        },
        "target_surfaces": ["thematic_coding", "negative_case"],
        "confidence_source": "system_confidence_field",
        "planned_item_count": planned_item_count,
        "outcome_metrics": [
            "accuracy",
            "brier_score",
            "expected_calibration_error",
        ],
        "outcome_file": "confidence_calibration.json",
        "outcome_file_sha256": calibration_hash,
        "success_criteria": [
            {
                "metric": "accuracy",
                "pass_condition": "Report accuracy and interval before any claim.",
            },
            {
                "metric": "brier_score",
                "pass_condition": "Report Brier score and interval before any claim.",
            },
            {
                "metric": "expected_calibration_error",
                "pass_condition": "Report ECE and interval before any claim.",
            },
        ],
    }


def _calibration_payload() -> dict:
    return {
        "confidence_calibration_evaluations": [
            {
                "item_id": "item-1",
                "surface": "thematic_coding",
                "confidence": 0.9,
                "correct": True,
                "evaluator": "expert_adjudication",
            },
            {
                "item_id": "item-2",
                "surface": "negative_case",
                "confidence": 0.2,
                "correct": False,
                "evaluator": "expert_adjudication",
            },
        ]
    }


def _error_fields(report) -> list[str]:
    return [error.field for error in report.errors]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
