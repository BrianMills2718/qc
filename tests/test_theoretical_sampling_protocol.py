"""Tests for theoretical-sampling protocol package validation."""

from __future__ import annotations

import json

import pytest

from qc_clean.core.theoretical_sampling_protocol import (
    load_theoretical_sampling_protocol,
    validate_theoretical_sampling_protocol_payload,
)
from scripts import validate_theoretical_sampling_protocol


def test_valid_theoretical_sampling_protocol_loads(tmp_path):
    protocol_path = tmp_path / "sampling_protocol.json"
    protocol_path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")

    package = load_theoretical_sampling_protocol(protocol_path)

    assert package.schema_version == 1
    assert package.package_type == "qualitative_coding.theoretical_sampling_protocol"
    assert package.protocol_id == "ts-protocol-v1"
    assert package.project_id == "project-gt"
    assert package.target_gap_codes == ["TRUST", "ACCESS"]
    assert package.target_gap_types == ["needs_properties", "needs_dimensions"]
    assert package.thresholds.min_properties == 2
    assert package.thresholds.min_supporting_documents == 2


def test_theoretical_sampling_protocol_rejects_missing_target_gaps():
    payload = _valid_protocol()
    payload["target_gap_codes"] = []

    with pytest.raises(ValueError, match="target_gap_codes"):
        validate_theoretical_sampling_protocol_payload(payload)


def test_theoretical_sampling_protocol_rejects_duplicate_target_gap_codes():
    payload = _valid_protocol()
    payload["target_gap_codes"] = ["TRUST", "ACCESS", "TRUST"]

    with pytest.raises(ValueError, match="Duplicate theoretical sampling target_gap_code"):
        validate_theoretical_sampling_protocol_payload(payload)


def test_validate_theoretical_sampling_protocol_script_outputs_json(tmp_path, capsys):
    protocol_path = tmp_path / "sampling_protocol.json"
    protocol_path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")

    exit_code = validate_theoretical_sampling_protocol.main([str(protocol_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["package_type"] == "qualitative_coding.theoretical_sampling_protocol"
    assert output["target_gap_codes"] == ["TRUST", "ACCESS"]

    invalid = _valid_protocol()
    invalid["target_gap_codes"] = []
    protocol_path.write_text(json.dumps(invalid), encoding="utf-8")

    exit_code = validate_theoretical_sampling_protocol.main([str(protocol_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert "target_gap_codes" in output["error"]


def _valid_protocol() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.theoretical_sampling_protocol",
        "protocol_id": "ts-protocol-v1",
        "project_id": "project-gt",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "registered_before_sampling": True,
        "candidate_source": "mixed",
        "collection_mode": "mixed",
        "target_gap_codes": ["TRUST", "ACCESS"],
        "target_gap_types": ["needs_properties", "needs_dimensions"],
        "thresholds": {
            "min_properties": 2,
            "min_dimensions": 2,
            "min_supporting_applications": 3,
            "min_supporting_documents": 2,
        },
        "max_suggestions": 5,
        "collection_rules": [
            "Prioritize cases that can elaborate category properties or dimensions.",
            "Do not report saturation until the stopping rule is met.",
        ],
        "stopping_rule": (
            "Stop only after all targeted categories meet thresholds or the protocol "
            "records why further collection is infeasible."
        ),
        "success_criteria": [
            "Every targeted gap has an explicit sampling decision.",
            "Every selected case records which category gap it addresses.",
        ],
        "caution": (
            "Theoretical sampling protocol metadata is process infrastructure only; "
            "it is not sampling adequacy evidence or saturation proof."
        ),
        "notes": "Fixture protocol.",
    }
