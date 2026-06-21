"""Tests for D3 held-out gold-set package validation."""

import json

import pytest

from qc_clean.core.d3_gold import load_d3_gold_set, validate_d3_gold_set_payload
from scripts import validate_d3_gold_set


def test_validate_d3_gold_set_accepts_held_out_package(tmp_path):
    path = tmp_path / "d3_gold.json"
    path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    package = load_d3_gold_set(path)

    assert package.schema_version == 1
    assert package.gold_set_id == "d3-heldout-v1"
    assert package.split == "held_out"
    assert package.prompt_frozen is True
    assert package.contamination_checked is True
    assert len(package.application_gold) == 1


def test_validate_d3_gold_set_rejects_duplicate_anchor_keys():
    payload = _valid_package()
    payload["application_gold"].append(dict(payload["application_gold"][0]))

    with pytest.raises(ValueError, match="Duplicate D3 application gold anchor key"):
        validate_d3_gold_set_payload(payload)


def test_validate_d3_gold_set_requires_held_out_freeze_and_adjudication():
    payload = _valid_package()
    payload["prompt_frozen"] = False

    with pytest.raises(ValueError, match="prompt_frozen=true"):
        validate_d3_gold_set_payload(payload)

    payload = _valid_package()
    payload["contamination_checked"] = False

    with pytest.raises(ValueError, match="contamination_checked=true"):
        validate_d3_gold_set_payload(payload)

    payload = _valid_package()
    payload["adjudication"]["coder_count"] = 1

    with pytest.raises(ValueError, match="at least two coders"):
        validate_d3_gold_set_payload(payload)


def test_validate_d3_gold_set_requires_valid_hashes():
    payload = _valid_package()
    payload["corpus_sha256"] = "not-a-sha"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_d3_gold_set_payload(payload)

    payload = _valid_package()
    payload["project_state_sha256"] = "not-a-sha"

    with pytest.raises(ValueError, match="project_state_sha256"):
        validate_d3_gold_set_payload(payload)


def test_validate_d3_gold_set_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "valid_gold.json"
    valid_path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    exit_code = validate_d3_gold_set.main([str(valid_path)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["gold_set_id"] == "d3-heldout-v1"
    assert output["application_gold_count"] == 1

    invalid = _valid_package()
    invalid["application_gold"].append(dict(invalid["application_gold"][0]))
    invalid_path = tmp_path / "invalid_gold.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")

    exit_code = validate_d3_gold_set.main([str(invalid_path)])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is False
    assert "Duplicate D3 application gold anchor key" in output["error"]


def _valid_package():
    return {
        "schema_version": 1,
        "gold_set_id": "d3-heldout-v1",
        "dataset_name": "Held-out interview application gold v1",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": None,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "redacted",
            "protocol": "Independent coding followed by adjudication.",
            "human_human_agreement": None,
            "notes": "",
        },
        "application_gold": [
            {
                "code_id": "AI_USE",
                "doc_id": "doc-1",
                "start_char": 10,
                "end_char": 42,
                "quote_text": "AI helped here.",
            }
        ],
    }
