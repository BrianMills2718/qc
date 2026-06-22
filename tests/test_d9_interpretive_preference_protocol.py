"""Tests for D9 interpretive-preference protocol package validation."""

import json

import pytest

from qc_clean.core.d9_interpretive_preference_protocol import (
    validate_d9_interpretive_preference_protocol_payload,
)
from scripts import validate_d9_interpretive_preference_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_COMPARISON_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_validate_d9_interpretive_preference_protocol_accepts_held_out_package():
    package = validate_d9_interpretive_preference_protocol_payload(
        _protocol_payload()
    )

    assert package.protocol_id == "d9-interpretive-preference-heldout-v1"
    assert package.split == "held_out"
    assert package.non_inferiority_margin == 0.1
    assert package.outcome_metrics == [
        "system_minus_human_preference_rate",
        "system_preference_rate",
        "tie_rate",
    ]
    assert package.target_criteria == ["interpretive_depth", "latent_meaning"]
    assert package.target_surfaces == ["codebook", "themes"]
    assert package.evaluator_plan.evaluator_types == ["human_expert"]
    assert package.planned_case_count == 24
    assert "not blind expert-parity evidence" in package.caution


def test_validate_d9_interpretive_preference_protocol_requires_held_out_gates():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_evaluation", False, "registered_before_evaluation=true"),
        ("blinded", False, "blinded=true"),
        ("project_state_sha256", None, "project_state_sha256"),
        ("comparison_artifact_sha256", None, "comparison_artifact_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_d9_interpretive_preference_protocol_payload(payload)


def test_validate_d9_interpretive_preference_protocol_requires_evaluator_plan_and_case_design():
    payload = _protocol_payload()
    payload["evaluator_plan"]["evaluator_types"] = []

    with pytest.raises(ValueError, match="evaluator_types"):
        validate_d9_interpretive_preference_protocol_payload(payload)

    payload = _protocol_payload()
    payload["evaluator_plan"]["planned_evaluator_count"] = 0

    with pytest.raises(ValueError, match="planned_evaluator_count"):
        validate_d9_interpretive_preference_protocol_payload(payload)

    payload = _protocol_payload()
    payload["planned_case_count"] = 0

    with pytest.raises(ValueError, match="planned_case_count"):
        validate_d9_interpretive_preference_protocol_payload(payload)

    payload = _protocol_payload()
    payload["target_criteria"] = []

    with pytest.raises(ValueError, match="target_criteria"):
        validate_d9_interpretive_preference_protocol_payload(payload)

    payload = _protocol_payload()
    payload["target_surfaces"] = []

    with pytest.raises(ValueError, match="target_surfaces"):
        validate_d9_interpretive_preference_protocol_payload(payload)

    payload = _protocol_payload()
    payload["non_inferiority_margin"] = 0

    with pytest.raises(ValueError, match="non_inferiority_margin"):
        validate_d9_interpretive_preference_protocol_payload(payload)


def test_validate_d9_interpretive_preference_protocol_rejects_bad_hashes():
    cases = [
        "corpus_sha256",
        "project_state_sha256",
        "comparison_artifact_sha256",
        "outcome_file_sha256",
    ]
    for field in cases:
        payload = _protocol_payload()
        payload[field] = "not-a-sha256"
        with pytest.raises(ValueError, match=field):
            validate_d9_interpretive_preference_protocol_payload(payload)


def test_validate_d9_interpretive_preference_protocol_requires_success_criteria_for_each_metric():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "metric": "system_minus_human_preference_rate",
            "pass_condition": "Lower CI bound must be above the pre-registered margin.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_d9_interpretive_preference_protocol_payload(payload)


def test_validate_d9_interpretive_preference_protocol_script_outputs_json(
    tmp_path,
    capsys,
):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_d9_interpretive_preference_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "d9-interpretive-preference-heldout-v1"
    assert valid_output["non_inferiority_margin"] == 0.1
    assert valid_output["outcome_metrics"] == [
        "system_minus_human_preference_rate",
        "system_preference_rate",
        "tie_rate",
    ]
    assert valid_output["target_criteria"] == ["interpretive_depth", "latent_meaning"]
    assert valid_output["target_surfaces"] == ["codebook", "themes"]
    assert valid_output["planned_case_count"] == 24
    assert valid_output["success_criteria_count"] == 3

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["blinded"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_d9_interpretive_preference_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "blinded=true" in invalid_output["error"]


def _protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d9_interpretive_preference_protocol",
        "protocol_id": "d9-interpretive-preference-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D9 held-out interpretive preference v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "comparison_artifact_sha256": _COMPARISON_ARTIFACT_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "blinded": True,
        "evaluator_plan": {
            "evaluator_types": ["human_expert"],
            "planned_evaluator_count": 3,
            "qualification": "Blind qualitative-methods expert panel.",
        },
        "target_criteria": ["interpretive_depth", "latent_meaning"],
        "target_surfaces": ["codebook", "themes"],
        "planned_case_count": 24,
        "non_inferiority_margin": 0.1,
        "outcome_metrics": [
            "system_minus_human_preference_rate",
            "system_preference_rate",
            "tie_rate",
        ],
        "outcome_file": "interpretive_preference.json",
        "outcome_file_sha256": _OUTCOME_HASH,
        "success_criteria": [
            {
                "metric": "system_minus_human_preference_rate",
                "pass_condition": "Lower CI bound must be above the margin.",
            },
            {
                "metric": "system_preference_rate",
                "pass_condition": "Report non-tie system preference rate and interval.",
            },
            {
                "metric": "tie_rate",
                "pass_condition": "Report tie rate and interval.",
            },
        ],
    }
