"""Tests for D6 bias-audit protocol package validation."""

import json

import pytest

from qc_clean.core.d6_bias_protocol import validate_d6_bias_protocol_payload
from scripts import validate_d6_bias_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_CASE_SET_HASH = "c" * 64
_STRATIFIED_HASH = "d" * 64
_COUNTERFACTUAL_HASH = "e" * 64


def test_validate_d6_bias_protocol_accepts_held_out_package():
    package = validate_d6_bias_protocol_payload(_protocol_payload())

    assert package.protocol_id == "d6-bias-heldout-v1"
    assert package.split == "held_out"
    assert package.dimensions == ["bias_stratified_d6", "bias_counterfactual_d6"]
    assert package.attribute_policy.attributes == ["role", "immigration_status"]
    assert package.stratified_strategy is not None
    assert package.stratified_strategy.minimum_group_size == 5
    assert package.counterfactual_strategy is not None
    assert package.counterfactual_strategy.identity_cues == [
        "manager",
        "single mother",
    ]
    assert "not a populated bias audit" in package.caution


def test_validate_d6_bias_protocol_requires_held_out_freeze_contamination_registration_and_state_hash():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_run", False, "registered_before_run=true"),
        ("project_state_sha256", None, "project_state_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_d6_bias_protocol_payload(payload)


def test_validate_d6_bias_protocol_rejects_missing_required_strategies():
    payload = _protocol_payload(dimensions=["bias_stratified_d6"])
    payload["stratified_strategy"] = None

    with pytest.raises(ValueError, match="stratified_strategy"):
        validate_d6_bias_protocol_payload(payload)

    payload = _protocol_payload(dimensions=["bias_counterfactual_d6"])
    payload["stratified_strategy"] = None
    payload["counterfactual_strategy"] = None

    with pytest.raises(ValueError, match="counterfactual_strategy"):
        validate_d6_bias_protocol_payload(payload)

    payload = _protocol_payload(dimensions=["bias_stratified_d6"])
    payload["attribute_policy"]["attributes"] = []

    with pytest.raises(ValueError, match="attributes"):
        validate_d6_bias_protocol_payload(payload)


def test_validate_d6_bias_protocol_rejects_duplicate_dimensions_and_bad_hashes():
    payload = _protocol_payload(
        dimensions=["bias_stratified_d6", "bias_stratified_d6"]
    )

    with pytest.raises(ValueError, match="Duplicate D6 bias dimension"):
        validate_d6_bias_protocol_payload(payload)

    payload = _protocol_payload()
    payload["corpus_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_d6_bias_protocol_payload(payload)

    payload = _protocol_payload()
    payload["case_set"]["case_set_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="case_set_sha256"):
        validate_d6_bias_protocol_payload(payload)


def test_validate_d6_bias_protocol_requires_success_criteria_for_each_dimension():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "dimension": "bias_stratified_d6",
            "metric": "max_error_rate_gap",
            "pass_condition": "Report gap and Wilson intervals by attribute.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_d6_bias_protocol_payload(payload)


def test_validate_d6_bias_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_d6_bias_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "d6-bias-heldout-v1"
    assert valid_output["dimensions"] == [
        "bias_stratified_d6",
        "bias_counterfactual_d6",
    ]
    assert valid_output["success_criteria_count"] == 2

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_d6_bias_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload(*, dimensions: list[str] | None = None) -> dict:
    dimensions = dimensions or ["bias_stratified_d6", "bias_counterfactual_d6"]
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d6_bias_protocol",
        "protocol_id": "d6-bias-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D6 held-out bias audit v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "dimensions": dimensions,
        "attribute_policy": {
            "attributes": ["role", "immigration_status"],
            "attribute_source": "Self-reported study metadata with manual review.",
            "ethical_review": "IRB-approved use for aggregate error diagnostics.",
            "use_permitted": True,
            "privacy_protection": "De-identified groups; no individual-level reporting.",
        },
        "case_set": {
            "case_set_id": "d6-heldout-cases-v1",
            "case_set_version": "1",
            "case_set_path": "d6_cases.json",
            "case_set_sha256": _CASE_SET_HASH,
            "planned_case_count": 60,
            "minimum_group_size": 5,
        },
        "stratified_strategy": {
            "attributes": ["role", "immigration_status"],
            "surfaces": ["application_validity", "claim_validity"],
            "correctness_label_source": "Blind expert adjudication package.",
            "outcome_file": "bias_stratified.json",
            "outcome_file_sha256": _STRATIFIED_HASH,
            "minimum_group_size": 5,
        },
        "counterfactual_strategy": {
            "identity_cues": ["manager", "single mother"],
            "invariant_text_policy": "Only identity cue phrase changes; substantive text fixed.",
            "generation_method": "Template-controlled identity-cue swap.",
            "outcome_file": "bias_counterfactual.json",
            "outcome_file_sha256": _COUNTERFACTUAL_HASH,
        },
        "success_criteria": [
            {
                "dimension": "bias_stratified_d6",
                "metric": "max_error_rate_gap",
                "pass_condition": "Report group gaps and Wilson intervals before any claim.",
            },
            {
                "dimension": "bias_counterfactual_d6",
                "metric": "code_change_rate",
                "pass_condition": "Report code-change rate and Wilson interval.",
            },
        ],
    }
