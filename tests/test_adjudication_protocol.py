"""Tests for adjudication protocol package validation."""

import json

import pytest

from qc_clean.core.adjudication_protocol import validate_adjudication_protocol_payload
from scripts import validate_adjudication_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_SAMPLE_HASH = "c" * 64


def test_validate_protocol_accepts_held_out_d3_d7_package():
    package = validate_adjudication_protocol_payload(_protocol_payload())

    assert package.protocol_id == "study-heldout-v1"
    assert package.split == "held_out"
    assert package.target_dimensions == [
        "d3_application_validity",
        "d7_disconfirmation",
    ]
    assert "not expert evidence" in package.caution


def test_validate_protocol_requires_held_out_freeze_contamination_registration_and_two_coders():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_labeling", False, "registered_before_labeling=true"),
        ("coder_count", 1, "at least two coders"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_adjudication_protocol_payload(payload)


def test_validate_protocol_rejects_dimension_target_mismatch():
    payload = _protocol_payload(
        target_dimensions=["d7_disconfirmation"],
        target_item_types=["code_application"],
    )

    with pytest.raises(ValueError, match="negative_case"):
        validate_adjudication_protocol_payload(payload)


def test_validate_protocol_rejects_duplicate_dimensions():
    payload = _protocol_payload(
        target_dimensions=["d3_application_validity", "d3_application_validity"]
    )

    with pytest.raises(ValueError, match="Duplicate adjudication target dimension"):
        validate_adjudication_protocol_payload(payload)


def test_validate_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_adjudication_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "study-heldout-v1"
    assert valid_output["target_dimensions"] == [
        "d3_application_validity",
        "d7_disconfirmation",
    ]

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_adjudication_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload(
    *,
    target_dimensions: list[str] | None = None,
    target_item_types: list[str] | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "adjudication_protocol",
        "protocol_id": "study-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Study held-out adjudication v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_labeling": True,
        "coder_count": 2,
        "adjudicator": "expert-panel-chair",
        "coder_qualification": "Qualified qualitative researchers.",
        "target_dimensions": target_dimensions
        or ["d3_application_validity", "d7_disconfirmation"],
        "sampling_plan": {
            "sample_package_path": "sample.json",
            "sample_package_sha256": _SAMPLE_HASH,
            "target_item_types": target_item_types or ["code_application", "negative_case"],
            "sampling_method": "Deterministic sample export followed by blind review.",
            "planned_sample_size": 40,
        },
        "success_criteria": [
            {
                "dimension": "d3_application_validity",
                "metric": "exact_f1",
                "pass_condition": "Report point estimate and CI against human ceiling.",
            },
            {
                "dimension": "d7_disconfirmation",
                "metric": "recall",
                "pass_condition": "Report recall/precision against adjudicated contrary evidence.",
            },
        ],
    }
