"""Tests for versioned INV-7 prompt-injection package validation."""

import json

import pytest

from qc_clean.core.inv7_package import (
    prompt_injection_payload_for_scorecard,
    validate_inv7_prompt_injection_package_payload,
)
from scripts import validate_inv7_prompt_injection_package


def test_valid_live_inv7_package_validates():
    payload = _valid_live_package()

    package = validate_inv7_prompt_injection_package_payload(payload)

    assert package.schema_version == 1
    assert package.package_id == "inv7-live-canary"
    assert package.mode == "live_model"
    assert package.model == "fake-live-model"
    assert package.total_fixtures == 1
    assert package.failed == 0


def test_live_inv7_package_requires_model_metadata():
    payload = _valid_live_package()
    payload["model"] = None

    with pytest.raises(ValueError, match="live_model.*model"):
        validate_inv7_prompt_injection_package_payload(payload)


def test_inv7_package_rejects_duplicate_fixture_ids():
    payload = _valid_live_package()
    payload["prompt_injection_evaluations"].append(
        dict(payload["prompt_injection_evaluations"][0])
    )

    with pytest.raises(ValueError, match="Duplicate INV-7 fixture_id"):
        validate_inv7_prompt_injection_package_payload(payload)


def test_prompt_injection_payload_for_scorecard_accepts_versioned_package():
    payload = _valid_live_package()

    evaluations = prompt_injection_payload_for_scorecard(payload)

    assert len(evaluations) == 1
    assert evaluations[0]["fixture_id"] == "live-direct"
    assert evaluations[0]["response_excerpt"] == "Participant wanted support."


def test_validate_inv7_package_script_emits_summary(tmp_path, capsys):
    package_path = tmp_path / "inv7_package.json"
    package_path.write_text(json.dumps(_valid_live_package()), encoding="utf-8")

    exit_code = validate_inv7_prompt_injection_package.main([str(package_path)])

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "ok": True,
        "package_id": "inv7-live-canary",
        "mode": "live_model",
        "split": "canary",
        "fixture_set_id": "built-in-live",
        "fixture_set_version": "1",
        "total_fixtures": 1,
        "failed": 0,
        "passed": 1,
    }


def _valid_live_package() -> dict:
    return {
        "schema_version": 1,
        "package_id": "inv7-live-canary",
        "mode": "live_model",
        "split": "canary",
        "fixture_set_id": "built-in-live",
        "fixture_set_version": "1",
        "prompt_frozen": True,
        "contamination_checked": False,
        "evaluator": "live_model_canary",
        "model": "fake-live-model",
        "trace_id": "trace-live",
        "max_budget": 0.5,
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
