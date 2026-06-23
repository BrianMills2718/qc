"""Tests for sampling-frame adequacy protocol package validation."""

import json

import pytest

from qc_clean.core.sampling_frame_adequacy_protocol import (
    validate_sampling_frame_adequacy_protocol_payload,
)
from scripts import validate_sampling_frame_adequacy_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_SCOPE_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64
_DIMENSIONS = [
    "population_alignment",
    "frame_coverage",
    "recruitment_selection_fit",
    "inclusion_exclusion_fit",
    "transferability_limits",
]


def test_validate_sampling_frame_adequacy_protocol_accepts_held_out_package():
    package = validate_sampling_frame_adequacy_protocol_payload(_protocol_payload())

    assert package.protocol_id == "sampling-frame-heldout-v1"
    assert package.split == "held_out"
    assert package.dimensions == _DIMENSIONS
    assert package.reviewer_plan.reviewer_types == ["methodologist", "domain_expert"]
    assert "not sampling-frame adequacy evidence" in package.caution


def test_validate_sampling_frame_adequacy_protocol_requires_held_out_gates():
    cases = [
        ("scope_frozen", False, "scope_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_evaluation", False, "registered_before_evaluation=true"),
        ("project_state_sha256", None, "project_state_sha256"),
        ("corpus_scope_sha256", None, "corpus_scope_sha256"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_sampling_frame_adequacy_protocol_payload(payload)


def test_validate_sampling_frame_adequacy_protocol_rejects_missing_dimensions_and_bad_hashes():
    payload = _protocol_payload()
    payload["dimensions"] = _DIMENSIONS[:-1]

    with pytest.raises(ValueError, match="transferability_limits"):
        validate_sampling_frame_adequacy_protocol_payload(payload)

    payload = _protocol_payload()
    payload["dimensions"] = [_DIMENSIONS[0], _DIMENSIONS[0], *_DIMENSIONS[1:]]

    with pytest.raises(ValueError, match="Duplicate sampling-frame adequacy dimension"):
        validate_sampling_frame_adequacy_protocol_payload(payload)

    payload = _protocol_payload()
    payload["corpus_sha256"] = "not-a-sha256"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_sampling_frame_adequacy_protocol_payload(payload)


def test_validate_sampling_frame_adequacy_protocol_requires_success_criteria():
    payload = _protocol_payload()
    payload["success_criteria"] = [
        {
            "dimension": "population_alignment",
            "pass_condition": "Report population-alignment rating.",
        }
    ]

    with pytest.raises(ValueError, match="missing success criteria"):
        validate_sampling_frame_adequacy_protocol_payload(payload)


def test_validate_sampling_frame_adequacy_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_sampling_frame_adequacy_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "sampling-frame-heldout-v1"
    assert valid_output["dimensions"] == _DIMENSIONS
    assert valid_output["success_criteria_count"] == len(_DIMENSIONS)

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["scope_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_sampling_frame_adequacy_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "scope_frozen=true" in invalid_output["error"]


def _protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.sampling_frame_adequacy_protocol",
        "protocol_id": "sampling-frame-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Sampling-frame adequacy held-out v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "corpus_scope_sha256": _SCOPE_HASH,
        "scope_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "reviewer_plan": {
            "reviewer_types": ["methodologist", "domain_expert"],
            "planned_reviewer_count": 2,
            "qualification": "Qualitative-methods reviewer and domain reviewer.",
        },
        "dimensions": list(_DIMENSIONS),
        "outcome_file": "sampling_frame_adequacy.json",
        "outcome_file_sha256": _OUTCOME_HASH,
        "success_criteria": [
            {
                "dimension": dimension,
                "pass_condition": f"Report {dimension} rating and rationale.",
            }
            for dimension in _DIMENSIONS
        ],
    }
