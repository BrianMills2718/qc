"""Tests for D8 GT-fidelity protocol package validation."""

import json

import pytest

from qc_clean.core.d8_gt_fidelity_protocol import (
    validate_d8_gt_fidelity_protocol_payload,
)
from scripts import validate_d8_gt_fidelity_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_GT_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_validate_d8_gt_fidelity_protocol_accepts_held_out_package():
    package = validate_d8_gt_fidelity_protocol_payload(_protocol_payload())

    assert package.protocol_id == "d8-gt-fidelity-heldout-v1"
    assert package.split == "held_out"
    assert package.rubric_metrics == [
        "constant_comparison",
        "category_development",
        "memo_quality",
        "saturation_justification",
    ]
    assert package.evaluator_plan.evaluator_types == ["human_expert", "llm_judge"]
    assert package.target_scopes == ["grounded_theory_pipeline", "category", "memo"]
    assert "not full grounded-theory evidence" in package.caution


def test_validate_d8_gt_fidelity_protocol_requires_held_out_gates():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_evaluation", False, "registered_before_evaluation=true"),
        ("project_state_sha256", None, "project_state_sha256"),
        ("gt_artifact_sha256", None, "gt_artifact_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_d8_gt_fidelity_protocol_payload(payload)


def test_validate_d8_gt_fidelity_protocol_requires_evaluator_plan_and_scopes():
    payload = _protocol_payload()
    payload["evaluator_plan"]["evaluator_types"] = []

    with pytest.raises(ValueError, match="evaluator_types"):
        validate_d8_gt_fidelity_protocol_payload(payload)

    payload = _protocol_payload()
    payload["evaluator_plan"]["planned_evaluator_count"] = 0

    with pytest.raises(ValueError, match="planned_evaluator_count"):
        validate_d8_gt_fidelity_protocol_payload(payload)

    payload = _protocol_payload()
    payload["target_scopes"] = []

    with pytest.raises(ValueError, match="target_scopes"):
        validate_d8_gt_fidelity_protocol_payload(payload)


def test_validate_d8_gt_fidelity_protocol_rejects_missing_metrics_and_bad_hashes():
    payload = _protocol_payload()
    payload["rubric_metrics"] = [
        "constant_comparison",
        "category_development",
        "memo_quality",
    ]

    with pytest.raises(ValueError, match="saturation_justification"):
        validate_d8_gt_fidelity_protocol_payload(payload)

    payload = _protocol_payload()
    payload["rubric_metrics"] = [
        "constant_comparison",
        "constant_comparison",
        "category_development",
        "memo_quality",
        "saturation_justification",
    ]

    with pytest.raises(ValueError, match="Duplicate D8 rubric metric"):
        validate_d8_gt_fidelity_protocol_payload(payload)

    payload = _protocol_payload()
    payload["corpus_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_d8_gt_fidelity_protocol_payload(payload)

    payload = _protocol_payload()
    payload["outcome_file_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="outcome_file_sha256"):
        validate_d8_gt_fidelity_protocol_payload(payload)


def test_validate_d8_gt_fidelity_protocol_requires_success_criteria_for_each_metric():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "metric": "constant_comparison",
            "pass_condition": "Report constant-comparison mean and interval.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_d8_gt_fidelity_protocol_payload(payload)


def test_validate_d8_gt_fidelity_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_d8_gt_fidelity_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "d8-gt-fidelity-heldout-v1"
    assert valid_output["rubric_metrics"] == [
        "constant_comparison",
        "category_development",
        "memo_quality",
        "saturation_justification",
    ]
    assert valid_output["success_criteria_count"] == 4

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_d8_gt_fidelity_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d8_gt_fidelity_protocol",
        "protocol_id": "d8-gt-fidelity-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D8 held-out GT fidelity v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "gt_artifact_sha256": _GT_ARTIFACT_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "evaluator_plan": {
            "evaluator_types": ["human_expert", "llm_judge"],
            "planned_evaluator_count": 3,
            "qualification": "GT-methods experts plus frozen LLM judge.",
        },
        "rubric_metrics": [
            "constant_comparison",
            "category_development",
            "memo_quality",
            "saturation_justification",
        ],
        "target_scopes": ["grounded_theory_pipeline", "category", "memo"],
        "outcome_file": "gt_fidelity.json",
        "outcome_file_sha256": _OUTCOME_HASH,
        "success_criteria": [
            {
                "metric": "constant_comparison",
                "pass_condition": "Report constant-comparison mean and interval.",
            },
            {
                "metric": "category_development",
                "pass_condition": "Report category-development mean and interval.",
            },
            {
                "metric": "memo_quality",
                "pass_condition": "Report memo-quality mean and interval.",
            },
            {
                "metric": "saturation_justification",
                "pass_condition": "Report saturation-justification mean and interval.",
            },
        ],
    }
