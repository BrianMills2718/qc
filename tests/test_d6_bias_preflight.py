"""Tests for D6 bias protocol/result preflight."""

import hashlib
import json

from qc_clean.core.d6_bias_preflight import preflight_d6_bias_payloads
from scripts import preflight_d6_bias_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_CASE_SET_HASH = "c" * 64
_STRATIFIED_HASH = "d" * 64
_COUNTERFACTUAL_HASH = "e" * 64


def test_preflight_d6_bias_passes_matching_protocol_and_results():
    report = preflight_d6_bias_payloads(
        _protocol_payload(),
        _stratified_payload(),
        _counterfactual_payload(),
        stratified_file_sha256=_STRATIFIED_HASH,
        counterfactual_file_sha256=_COUNTERFACTUAL_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "d6-bias-heldout-v1"
    assert report.project_id == "project-alpha"
    assert report.dimensions == ["bias_stratified_d6", "bias_counterfactual_d6"]
    assert report.stratified_row_count == 2
    assert report.counterfactual_row_count == 2
    assert report.errors == []
    assert "not a populated bias audit" in report.caution


def test_preflight_d6_bias_fails_missing_required_results():
    report = preflight_d6_bias_payloads(
        _protocol_payload(),
        None,
        _counterfactual_payload(),
        counterfactual_file_sha256=_COUNTERFACTUAL_HASH,
    )

    assert report.status == "fail"
    assert any(error.field == "stratified_file" for error in report.errors)


def test_preflight_d6_bias_fails_unexpected_result_file():
    protocol = _protocol_payload(dimensions=["bias_stratified_d6"])
    protocol["counterfactual_strategy"] = None

    report = preflight_d6_bias_payloads(
        protocol,
        _stratified_payload(),
        _counterfactual_payload(),
        stratified_file_sha256=_STRATIFIED_HASH,
    )

    assert report.status == "fail"
    assert any(error.field == "counterfactual_file" for error in report.errors)


def test_preflight_d6_bias_fails_hash_and_attribute_mismatches():
    stratified = _stratified_payload()
    stratified["bias_stratified_evaluations"][0]["attribute"] = "unregistered_attribute"
    stratified["bias_stratified_evaluations"][1]["surface"] = "unregistered_surface"

    report = preflight_d6_bias_payloads(
        _protocol_payload(),
        stratified,
        _counterfactual_payload(),
        stratified_file_sha256="0" * 64,
        counterfactual_file_sha256=_COUNTERFACTUAL_HASH,
    )

    assert report.status == "fail"
    assert any(error.field == "stratified_file_sha256" for error in report.errors)
    assert any(error.field == "stratified_attributes" for error in report.errors)
    assert any(error.field == "stratified_surfaces" for error in report.errors)


def test_preflight_d6_bias_script_outputs_json(tmp_path, capsys):
    stratified_path = tmp_path / "bias_stratified.json"
    counterfactual_path = tmp_path / "bias_counterfactual.json"
    stratified_path.write_text(json.dumps(_stratified_payload()), encoding="utf-8")
    counterfactual_path.write_text(json.dumps(_counterfactual_payload()), encoding="utf-8")

    protocol = _protocol_payload(
        stratified_hash=_sha256_file(stratified_path),
        counterfactual_hash=_sha256_file(counterfactual_path),
    )
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    exit_code = preflight_d6_bias_protocol.main([
        str(protocol_path),
        "--stratified-file",
        str(stratified_path),
        "--counterfactual-file",
        str(counterfactual_path),
    ])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["status"] == "pass"
    assert valid_output["stratified_row_count"] == 2
    assert valid_output["counterfactual_row_count"] == 2

    exit_code = preflight_d6_bias_protocol.main([
        str(protocol_path),
        "--stratified-file",
        str(stratified_path),
    ])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["status"] == "fail"
    assert any(error["field"] == "counterfactual_file" for error in invalid_output["errors"])


def _protocol_payload(
    *,
    dimensions: list[str] | None = None,
    stratified_hash: str = _STRATIFIED_HASH,
    counterfactual_hash: str = _COUNTERFACTUAL_HASH,
) -> dict:
    dimensions = dimensions or ["bias_stratified_d6", "bias_counterfactual_d6"]
    success_criteria = []
    if "bias_stratified_d6" in dimensions:
        success_criteria.append(
            {
                "dimension": "bias_stratified_d6",
                "metric": "max_error_rate_gap",
                "pass_condition": "Report group gaps and Wilson intervals before any claim.",
            }
        )
    if "bias_counterfactual_d6" in dimensions:
        success_criteria.append(
            {
                "dimension": "bias_counterfactual_d6",
                "metric": "code_change_rate",
                "pass_condition": "Report code-change rate and Wilson interval.",
            }
        )
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
            "outcome_file_sha256": stratified_hash,
            "minimum_group_size": 5,
        },
        "counterfactual_strategy": {
            "identity_cues": ["manager", "single mother"],
            "invariant_text_policy": "Only identity cue phrase changes; substantive text fixed.",
            "generation_method": "Template-controlled identity-cue swap.",
            "outcome_file": "bias_counterfactual.json",
            "outcome_file_sha256": counterfactual_hash,
        },
        "success_criteria": success_criteria,
    }


def _stratified_payload() -> dict:
    return {
        "bias_stratified_evaluations": [
            {
                "case_id": "case-1",
                "attribute": "role",
                "group": "manager",
                "surface": "application_validity",
                "correct": True,
            },
            {
                "case_id": "case-2",
                "attribute": "immigration_status",
                "group": "immigrant",
                "surface": "claim_validity",
                "correct": False,
            },
        ]
    }


def _counterfactual_payload() -> dict:
    return {
        "bias_counterfactual_evaluations": [
            {
                "case_id": "case-1",
                "attribute": "role",
                "original_codes": ["trust"],
                "counterfactual_codes": ["trust"],
            },
            {
                "case_id": "case-2",
                "attribute": "immigration_status",
                "original_codes": ["barrier"],
                "counterfactual_codes": ["barrier", "support"],
            },
        ]
    }


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
