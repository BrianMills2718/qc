"""Tests for D7 retrieval comparison protocol validation."""

from __future__ import annotations

import json

import pytest

from qc_clean.core.d7_comparison_protocol import (
    validate_d7_comparison_protocol_payload,
)
from scripts import validate_d7_comparison_protocol


def test_validate_d7_comparison_protocol_accepts_held_out_package(tmp_path, capsys):
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")

    package = validate_d7_comparison_protocol_payload(json.loads(path.read_text(encoding="utf-8")))
    exit_code = validate_d7_comparison_protocol.main([str(path)])

    output = json.loads(capsys.readouterr().out)
    assert package.protocol_id == "d7-heldout-comparison-v1"
    assert output["status"] == "valid"
    assert output["protocol_id"] == "d7-heldout-comparison-v1"
    assert output["expected_prediction_count"] == 1


def test_validate_d7_comparison_protocol_rejects_invalid_held_out_flags():
    payload = _valid_protocol()
    payload["prompt_frozen"] = False

    with pytest.raises(ValueError, match="held_out.*prompt_frozen"):
        validate_d7_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["contamination_checked"] = False

    with pytest.raises(ValueError, match="held_out.*contamination_checked"):
        validate_d7_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["registered_before_run"] = False

    with pytest.raises(ValueError, match="held_out.*registered_before_run"):
        validate_d7_comparison_protocol_payload(payload)


def test_validate_d7_comparison_protocol_rejects_duplicate_expected_baselines():
    payload = _valid_protocol()
    payload["expected_predictions"].append(dict(payload["expected_predictions"][0]))

    with pytest.raises(ValueError, match="Duplicate D7 expected baseline"):
        validate_d7_comparison_protocol_payload(payload)


def test_validate_d7_comparison_protocol_rejects_incomplete_embedding_expectation():
    payload = _valid_protocol()
    expected = payload["expected_predictions"][0]
    expected["baseline_name"] = "retrieval_embedding_hybrid_top1"
    expected["retrieval_mode"] = "embedding_hybrid"
    expected["embedding_model"] = None

    with pytest.raises(ValueError, match="embedding_model"):
        validate_d7_comparison_protocol_payload(payload)


def test_validate_d7_comparison_protocol_rejects_bad_hashes():
    payload = _valid_protocol()
    payload["expected_predictions"][0]["prediction_file_sha256"] = "not-a-sha"

    with pytest.raises(ValueError, match="prediction_file_sha256"):
        validate_d7_comparison_protocol_payload(payload)


def _valid_protocol() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d7_retrieval_comparison_protocol",
        "protocol_id": "d7-heldout-comparison-v1",
        "project_id": "project-d7",
        "dataset_name": "Held-out D7 comparison v1",
        "split": "held_out",
        "gold_set_id": "d7-heldout-v1",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "expected_predictions": [
            {
                "baseline_name": "retrieval_lexical_bm25_top1",
                "retrieval_mode": "lexical_bm25",
                "candidates_per_claim": 1,
                "max_targets": 50,
                "embedding_model": None,
                "embedding_dimensions": None,
                "trace_id": "qualitative_coding/d7-retrieval/project-d7",
                "max_budget": 1.0,
                "prediction_file_sha256": "c" * 64,
            }
        ],
        "success_criteria": [
            "Score lexical and embedding retrieval predictions against the same held-out D7 gold."
        ],
        "caution": (
            "D7 comparison protocol validation is process metadata only; it is not "
            "held-out D7 evidence, live-baseline evidence, or superiority evidence."
        ),
    }
