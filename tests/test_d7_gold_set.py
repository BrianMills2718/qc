"""Tests for D7 held-out gold-set package validation."""

import json

import pytest

from qc_clean.core.d7_gold import load_d7_gold_set, validate_d7_gold_set_payload
from scripts import validate_d7_gold_set


def test_validate_d7_gold_set_accepts_held_out_package(tmp_path):
    path = tmp_path / "d7_gold.json"
    path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    package = load_d7_gold_set(path)

    assert package.schema_version == 1
    assert package.gold_set_id == "d7-heldout-v1"
    assert package.split == "held_out"
    assert package.prompt_frozen is True
    assert package.contamination_checked is True
    assert len(package.contrary_evidence) == 1


def test_validate_d7_gold_set_rejects_duplicate_anchor_keys():
    payload = _valid_package()
    payload["contrary_evidence"].append(dict(payload["contrary_evidence"][0]))

    with pytest.raises(ValueError, match="Duplicate D7 gold anchor key"):
        validate_d7_gold_set_payload(payload)


def test_validate_d7_gold_set_requires_held_out_freeze_and_adjudication():
    payload = _valid_package()
    payload["prompt_frozen"] = False

    with pytest.raises(ValueError, match="prompt_frozen=true"):
        validate_d7_gold_set_payload(payload)

    payload = _valid_package()
    payload["contamination_checked"] = False

    with pytest.raises(ValueError, match="contamination_checked=true"):
        validate_d7_gold_set_payload(payload)

    payload = _valid_package()
    payload["adjudication"]["coder_count"] = 1

    with pytest.raises(ValueError, match="at least two coders"):
        validate_d7_gold_set_payload(payload)


def test_validate_d7_gold_set_script_outputs_json(tmp_path, capsys):
    valid_path = tmp_path / "valid_gold.json"
    valid_path.write_text(json.dumps(_valid_package()), encoding="utf-8")

    exit_code = validate_d7_gold_set.main([str(valid_path)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is True
    assert output["gold_set_id"] == "d7-heldout-v1"
    assert output["contrary_evidence_count"] == 1

    invalid = _valid_package()
    invalid["contrary_evidence"].append(dict(invalid["contrary_evidence"][0]))
    invalid_path = tmp_path / "invalid_gold.json"
    invalid_path.write_text(json.dumps(invalid), encoding="utf-8")

    exit_code = validate_d7_gold_set.main([str(invalid_path)])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["valid"] is False
    assert "Duplicate D7 gold anchor key" in output["error"]


def _valid_package():
    return {
        "schema_version": 1,
        "gold_set_id": "d7-heldout-v1",
        "dataset_name": "Held-out interview contrary evidence v1",
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
        "contrary_evidence": [
            {
                "target_claim_id": "claim-ai",
                "doc_id": "doc-1",
                "start_char": 10,
                "end_char": 42,
                "quote_text": "AI failed in this case.",
            }
        ],
    }
