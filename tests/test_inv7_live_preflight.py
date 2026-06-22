"""Tests for INV-7 live protocol-to-result preflight."""

import json

from qc_clean.core import inv7_live_preflight
from scripts import preflight_inv7_live_package


def test_inv7_live_preflight_accepts_matching_protocol_and_package():
    report = inv7_live_preflight.preflight_inv7_live_payloads(
        _protocol_payload(),
        _package_payload(),
    )

    assert report.status == "pass"
    assert report.protocol_id == "inv7-live-heldout-v1"
    assert report.package_id == "inv7-live-result-v1"
    assert report.fixture_count == 1
    assert not report.errors
    assert "not prompt-injection robustness evidence" in report.caution


def test_inv7_live_preflight_rejects_metadata_mismatch():
    package = _package_payload()
    package["model"] = "other-model"

    report = inv7_live_preflight.preflight_inv7_live_payloads(_protocol_payload(), package)

    assert report.status == "fail"
    assert "model" in _error_fields(report)


def test_inv7_live_preflight_rejects_prompt_hash_mismatch():
    package = _package_payload()
    package["fixture_prompt_hashes"] = {"live-direct": "b" * 64}

    report = inv7_live_preflight.preflight_inv7_live_payloads(_protocol_payload(), package)

    assert report.status == "fail"
    assert "fixture_prompt_hashes" in _error_fields(report)


def test_inv7_live_preflight_rejects_non_live_result_package():
    package = _package_payload()
    package["mode"] = "structural"

    report = inv7_live_preflight.preflight_inv7_live_payloads(_protocol_payload(), package)

    assert report.status == "fail"
    assert "mode" in _error_fields(report)


def test_inv7_live_preflight_script_outputs_json(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(_protocol_payload()), encoding="utf-8")
    package_path = tmp_path / "package.json"
    package_path.write_text(json.dumps(_package_payload()), encoding="utf-8")

    exit_code = preflight_inv7_live_package.main([
        str(protocol_path),
        str(package_path),
    ])

    assert exit_code == 0
    ok_output = json.loads(capsys.readouterr().out)
    assert ok_output["status"] == "pass"
    assert ok_output["fixture_count"] == 1

    invalid_package = _package_payload()
    invalid_package["trace_id"] = "wrong-trace"
    invalid_path = tmp_path / "invalid_package.json"
    invalid_path.write_text(json.dumps(invalid_package), encoding="utf-8")

    exit_code = preflight_inv7_live_package.main([
        str(protocol_path),
        str(invalid_path),
    ])

    assert exit_code == 1
    fail_output = json.loads(capsys.readouterr().out)
    assert fail_output["status"] == "fail"
    assert "trace_id" in [error["field"] for error in fail_output["errors"]]


def _error_fields(report) -> set[str]:
    return {error.field for error in report.errors}


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


def _package_payload() -> dict:
    return {
        "schema_version": 1,
        "package_id": "inv7-live-result-v1",
        "mode": "live_model",
        "split": "held_out",
        "fixture_set_id": "built_in_inv7_live",
        "fixture_set_version": "1",
        "prompt_frozen": True,
        "contamination_checked": True,
        "evaluator": "live_model_canary",
        "model": "fake-live-model",
        "trace_id": "qualitative_coding/inv7-live-heldout-v1",
        "max_budget": 0.5,
        "fixture_prompt_hashes": {"live-direct": "a" * 64},
        "note": "Canary package only; not robustness evidence.",
        "prompt_injection_evaluations": [
            {
                "fixture_id": "live-direct",
                "surface": "thematic_coding",
                "attack_type": "direct_instruction_override",
                "attack_succeeded": False,
                "failure_mode": None,
                "evaluator": "live_model_canary",
                "notes": "No canary emitted.",
                "response_excerpt": "Participant wanted support.",
            }
        ],
    }
