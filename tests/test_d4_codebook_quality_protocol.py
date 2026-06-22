"""Tests for D4 codebook-quality protocol package validation."""

import json

import pytest

from qc_clean.core.d4_codebook_quality_protocol import (
    validate_d4_codebook_quality_protocol_payload,
)
from scripts import validate_d4_codebook_quality_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_CODEBOOK_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_validate_d4_codebook_quality_protocol_accepts_held_out_package():
    package = validate_d4_codebook_quality_protocol_payload(_protocol_payload())

    assert package.protocol_id == "d4-codebook-quality-heldout-v1"
    assert package.split == "held_out"
    assert package.rubric_metrics == [
        "clarity",
        "specificity",
        "usefulness",
        "grounding",
    ]
    assert package.evaluator_plan.evaluator_types == ["human_expert", "llm_judge"]
    assert package.blinding.raters_blinded_to_origin is True
    assert "not blind expert evidence" in package.caution


def test_validate_d4_codebook_quality_protocol_requires_held_out_gates():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_evaluation", False, "registered_before_evaluation=true"),
        ("project_state_sha256", None, "project_state_sha256"),
        ("codebook_artifact_sha256", None, "codebook_artifact_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_d4_codebook_quality_protocol_payload(payload)


def test_validate_d4_codebook_quality_protocol_requires_blinding_and_evaluators():
    payload = _protocol_payload()
    payload["blinding"]["raters_blinded_to_origin"] = False

    with pytest.raises(ValueError, match="raters_blinded_to_origin=true"):
        validate_d4_codebook_quality_protocol_payload(payload)

    payload = _protocol_payload()
    payload["evaluator_plan"]["evaluator_types"] = []

    with pytest.raises(ValueError, match="evaluator_types"):
        validate_d4_codebook_quality_protocol_payload(payload)

    payload = _protocol_payload()
    payload["evaluator_plan"]["planned_evaluator_count"] = 0

    with pytest.raises(ValueError, match="planned_evaluator_count"):
        validate_d4_codebook_quality_protocol_payload(payload)


def test_validate_d4_codebook_quality_protocol_rejects_missing_metrics_and_bad_hashes():
    payload = _protocol_payload()
    payload["rubric_metrics"] = ["clarity", "specificity", "usefulness"]

    with pytest.raises(ValueError, match="grounding"):
        validate_d4_codebook_quality_protocol_payload(payload)

    payload = _protocol_payload()
    payload["rubric_metrics"] = ["clarity", "clarity", "specificity", "usefulness", "grounding"]

    with pytest.raises(ValueError, match="Duplicate D4 rubric metric"):
        validate_d4_codebook_quality_protocol_payload(payload)

    payload = _protocol_payload()
    payload["corpus_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_d4_codebook_quality_protocol_payload(payload)

    payload = _protocol_payload()
    payload["outcome_file_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="outcome_file_sha256"):
        validate_d4_codebook_quality_protocol_payload(payload)


def test_validate_d4_codebook_quality_protocol_requires_success_criteria_for_each_metric():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "metric": "clarity",
            "pass_condition": "Report clarity mean and interval.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_d4_codebook_quality_protocol_payload(payload)


def test_validate_d4_codebook_quality_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_d4_codebook_quality_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "d4-codebook-quality-heldout-v1"
    assert valid_output["rubric_metrics"] == [
        "clarity",
        "specificity",
        "usefulness",
        "grounding",
    ]
    assert valid_output["success_criteria_count"] == 4

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_d4_codebook_quality_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d4_codebook_quality_protocol",
        "protocol_id": "d4-codebook-quality-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D4 held-out codebook quality v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "codebook_artifact_sha256": _CODEBOOK_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "blinding": {
            "raters_blinded_to_origin": True,
            "source_labels_masked": True,
            "blinding_method": "Human experts receive anonymized codebooks without system labels.",
        },
        "evaluator_plan": {
            "evaluator_types": ["human_expert", "llm_judge"],
            "planned_evaluator_count": 3,
            "qualification": "Qualified qualitative researchers plus frozen LLM judge.",
        },
        "rubric_metrics": ["clarity", "specificity", "usefulness", "grounding"],
        "target_scopes": ["codebook", "individual_code"],
        "outcome_file": "quality.json",
        "outcome_file_sha256": _OUTCOME_HASH,
        "success_criteria": [
            {
                "metric": "clarity",
                "pass_condition": "Report clarity mean and bootstrap interval.",
            },
            {
                "metric": "specificity",
                "pass_condition": "Report specificity mean and bootstrap interval.",
            },
            {
                "metric": "usefulness",
                "pass_condition": "Report usefulness mean and bootstrap interval.",
            },
            {
                "metric": "grounding",
                "pass_condition": "Report grounding mean and bootstrap interval.",
            },
        ],
    }
