"""Tests for INV-7 live benchmark protocol packages."""

import json

import pytest

from qc_clean.core.inv7_live_protocol import validate_inv7_live_protocol_payload
from scripts import validate_inv7_live_protocol


def test_validate_inv7_live_protocol_accepts_held_out_package():
    package = validate_inv7_live_protocol_payload(_protocol_payload())

    assert package.protocol_id == "inv7-live-heldout-v1"
    assert package.split == "held_out"
    assert package.fixture_prompt_hashes == {"live-direct": "a" * 64}
    assert package.success_criteria[0].metric == "attack_success_rate"
    assert "not prompt-injection robustness evidence" in package.caution


def test_validate_inv7_live_protocol_requires_held_out_freeze_contamination_registration():
    cases = [
        ("prompt_frozen", False, "prompt_frozen=true"),
        ("contamination_checked", False, "contamination_checked=true"),
        ("registered_before_run", False, "registered_before_run=true"),
    ]
    for field, value, message in cases:
        payload = _protocol_payload()
        payload[field] = value
        with pytest.raises(ValueError, match=message):
            validate_inv7_live_protocol_payload(payload)


def test_validate_inv7_live_protocol_rejects_bad_prompt_hashes():
    payload = _protocol_payload()
    payload["fixture_prompt_hashes"] = {"live-direct": "not-a-sha256"}

    with pytest.raises(ValueError, match="SHA-256"):
        validate_inv7_live_protocol_payload(payload)

    payload = _protocol_payload()
    payload["fixture_prompt_hashes"] = {"": "a" * 64}

    with pytest.raises(ValueError, match="fixture_prompt_hashes fixture_id"):
        validate_inv7_live_protocol_payload(payload)


def test_validate_inv7_live_protocol_requires_success_criteria():
    payload = _protocol_payload()
    payload["success_criteria"] = []

    with pytest.raises(ValueError, match="success_criteria"):
        validate_inv7_live_protocol_payload(payload)


def test_validate_inv7_live_protocol_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "protocol.json"
    valid_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")

    exit_code = validate_inv7_live_protocol.main([str(valid_path)])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["valid"] is True
    assert valid_output["protocol_id"] == "inv7-live-heldout-v1"
    assert valid_output["fixture_count"] == 1

    invalid_path = tmp_path / "invalid_protocol.json"
    invalid_payload = _protocol_payload()
    invalid_payload["prompt_frozen"] = False
    invalid_path.write_text(json.dumps(invalid_payload), encoding="utf-8")

    exit_code = validate_inv7_live_protocol.main([str(invalid_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["valid"] is False
    assert "prompt_frozen=true" in invalid_output["error"]


def _protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "inv7_live_protocol",
        "protocol_id": "inv7-live-heldout-v1",
        "dataset_name": "INV-7 live held-out canary v1",
        "split": "held_out",
        "fixture_set_id": "built_in_inv7_live",
        "fixture_set_version": "1",
        "fixture_prompt_hashes": {"live-direct": "a" * 64},
        "model": "fake-live-model",
        "trace_id": "qualitative_coding/inv7-live-heldout-v1",
        "max_budget": 1.0,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "success_criteria": [
            {
                "metric": "attack_success_rate",
                "pass_condition": "Report attack success rate and Wilson interval.",
            }
        ],
    }
