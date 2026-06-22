"""Tests for confidence-calibration protocol package validation."""

import json

import pytest

from qc_clean.core.confidence_calibration_protocol import (
    validate_confidence_calibration_protocol_payload,
)
from scripts import validate_confidence_calibration_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_PREDICTION_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_validate_confidence_calibration_protocol_accepts_held_out_package():
    package = validate_confidence_calibration_protocol_payload(_protocol_payload())

    assert package.protocol_id == "confidence-calibration-heldout-v1"
    assert package.split == "held_out"
    assert package.outcome_metrics == [
        "accuracy",
        "brier_score",
        "expected_calibration_error",
    ]
    assert package.target_surfaces == ["thematic_coding", "negative_case"]
    assert package.label_plan.label_sources == ["expert_adjudication"]
    assert package.confidence_source == "system_confidence_field"
    assert package.planned_item_count == 30
    assert "not calibration proof" in package.caution


def test_validate_confidence_calibration_protocol_requires_held_out_gates():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_evaluation", False, "registered_before_evaluation=true"),
        ("project_state_sha256", None, "project_state_sha256"),
        ("prediction_artifact_sha256", None, "prediction_artifact_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_confidence_calibration_protocol_payload(payload)


def test_validate_confidence_calibration_protocol_requires_label_plan_and_case_design():
    payload = _protocol_payload()
    payload["label_plan"]["label_sources"] = []

    with pytest.raises(ValueError, match="label_sources"):
        validate_confidence_calibration_protocol_payload(payload)

    payload = _protocol_payload()
    payload["label_plan"]["planned_labeler_count"] = 0

    with pytest.raises(ValueError, match="planned_labeler_count"):
        validate_confidence_calibration_protocol_payload(payload)

    payload = _protocol_payload()
    payload["planned_item_count"] = 0

    with pytest.raises(ValueError, match="planned_item_count"):
        validate_confidence_calibration_protocol_payload(payload)

    payload = _protocol_payload()
    payload["target_surfaces"] = []

    with pytest.raises(ValueError, match="target_surfaces"):
        validate_confidence_calibration_protocol_payload(payload)

    payload = _protocol_payload()
    payload["confidence_source"] = " "

    with pytest.raises(ValueError, match="confidence_source"):
        validate_confidence_calibration_protocol_payload(payload)

    payload = _protocol_payload()
    payload["outcome_metrics"] = []

    with pytest.raises(ValueError, match="outcome_metrics"):
        validate_confidence_calibration_protocol_payload(payload)


def test_validate_confidence_calibration_protocol_rejects_bad_hashes():
    cases = [
        "corpus_sha256",
        "project_state_sha256",
        "prediction_artifact_sha256",
        "outcome_file_sha256",
    ]
    for field in cases:
        payload = _protocol_payload()
        payload[field] = "not-a-sha256"
        with pytest.raises(ValueError, match=field):
            validate_confidence_calibration_protocol_payload(payload)


def test_validate_confidence_calibration_protocol_requires_success_criteria_for_each_metric():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "metric": "accuracy",
            "pass_condition": "Report accuracy before any claim.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_confidence_calibration_protocol_payload(payload)


def test_validate_confidence_calibration_protocol_script_outputs_json(
    tmp_path,
    capsys,
):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_confidence_calibration_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "confidence-calibration-heldout-v1"
    assert valid_output["outcome_metrics"] == [
        "accuracy",
        "brier_score",
        "expected_calibration_error",
    ]
    assert valid_output["target_surfaces"] == ["thematic_coding", "negative_case"]
    assert valid_output["label_sources"] == ["expert_adjudication"]
    assert valid_output["confidence_source"] == "system_confidence_field"
    assert valid_output["planned_item_count"] == 30
    assert valid_output["success_criteria_count"] == 3

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_confidence_calibration_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload() -> dict:
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
        "planned_item_count": 30,
        "outcome_metrics": [
            "accuracy",
            "brier_score",
            "expected_calibration_error",
        ],
        "outcome_file": "confidence_calibration.json",
        "outcome_file_sha256": _OUTCOME_HASH,
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
