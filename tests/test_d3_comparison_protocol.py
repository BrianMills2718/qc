"""Tests for D3 baseline comparison protocol validation."""

from __future__ import annotations

import json

import pytest

from qc_clean.core.d3_comparison_protocol import (
    validate_d3_comparison_protocol_payload,
)
from scripts import validate_d3_comparison_protocol


def test_validate_d3_comparison_protocol_accepts_held_out_package(tmp_path, capsys):
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")

    package = validate_d3_comparison_protocol_payload(
        json.loads(path.read_text(encoding="utf-8"))
    )
    exit_code = validate_d3_comparison_protocol.main([str(path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert package.protocol_id == "d3-heldout-comparison-v1"
    assert output["status"] == "valid"
    assert output["protocol_id"] == "d3-heldout-comparison-v1"
    assert output["expected_baseline_count"] == 1
    assert output["metric_criteria_count"] == 0


def test_validate_d3_comparison_protocol_accepts_metric_criteria(tmp_path, capsys):
    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "baseline-recall-floor",
            "baseline_name": "single_prompt_baseline",
            "metric": "recall",
            "operator": ">=",
            "threshold": 0.8,
            "rationale": "Application baseline should recover most adjudicated anchors.",
        },
        {
            "criterion_id": "baseline-span-iou-floor",
            "baseline_name": "single_prompt_baseline",
            "metric": "mean_best_gold_iou",
            "operator": ">=",
            "threshold": 0.5,
            "rationale": "Boundary diagnostics should show useful overlap.",
        },
    ]
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    package = validate_d3_comparison_protocol_payload(payload)
    exit_code = validate_d3_comparison_protocol.main([str(path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert len(package.metric_criteria) == 2
    assert package.metric_criteria[0].criterion_id == "baseline-recall-floor"
    assert output["metric_criteria_count"] == 2


def test_validate_d3_comparison_protocol_rejects_unknown_metric_criterion_baseline():
    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "unknown-baseline",
            "baseline_name": "missing_baseline",
            "metric": "recall",
            "operator": ">=",
            "threshold": 0.8,
            "rationale": "This should fail because the baseline is not expected.",
        }
    ]

    with pytest.raises(ValueError, match="unknown baseline"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_duplicate_metric_criteria():
    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "duplicate-id",
            "baseline_name": "single_prompt_baseline",
            "metric": "recall",
            "operator": ">=",
            "threshold": 0.8,
            "rationale": "First criterion.",
        },
        {
            "criterion_id": "duplicate-id",
            "baseline_name": "single_prompt_baseline",
            "metric": "precision",
            "operator": ">=",
            "threshold": 0.8,
            "rationale": "Second criterion.",
        },
    ]

    with pytest.raises(ValueError, match="Duplicate D3 metric criterion"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_invalid_metric_threshold():
    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "bad-iou-threshold",
            "baseline_name": "single_prompt_baseline",
            "metric": "mean_best_gold_iou",
            "operator": ">=",
            "threshold": 1.5,
            "rationale": "IoU thresholds must stay in the proportion range.",
        }
    ]

    with pytest.raises(ValueError, match="threshold"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "bad-operator",
            "baseline_name": "single_prompt_baseline",
            "metric": "recall",
            "operator": "approximately",
            "threshold": 0.8,
            "rationale": "Operators must be from the supported deterministic set.",
        }
    ]

    with pytest.raises(ValueError, match="operator"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["metric_criteria"] = [
        {
            "criterion_id": "empty-rationale",
            "baseline_name": "single_prompt_baseline",
            "metric": "recall",
            "operator": ">=",
            "threshold": 0.8,
            "rationale": " ",
        }
    ]

    with pytest.raises(ValueError, match="rationale"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_invalid_held_out_flags():
    payload = _valid_protocol()
    payload["prompt_frozen"] = False

    with pytest.raises(ValueError, match="held_out.*prompt_frozen"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["contamination_checked"] = False

    with pytest.raises(ValueError, match="held_out.*contamination_checked"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["registered_before_run"] = False

    with pytest.raises(ValueError, match="held_out.*registered_before_run"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["project_state_sha256"] = None

    with pytest.raises(ValueError, match="held_out.*project_state_sha256"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_duplicate_expected_baselines():
    payload = _valid_protocol()
    payload["expected_predictions"].append(dict(payload["expected_predictions"][0]))

    with pytest.raises(ValueError, match="Duplicate D3 expected baseline"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_bad_hashes():
    payload = _valid_protocol()
    payload["corpus_sha256"] = "not-a-sha"

    with pytest.raises(ValueError, match="corpus_sha256"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["expected_predictions"][0]["prediction_file_sha256"] = "not-a-sha"

    with pytest.raises(ValueError, match="prediction_file_sha256"):
        validate_d3_comparison_protocol_payload(payload)


def test_validate_d3_comparison_protocol_rejects_invalid_expected_baseline():
    payload = _valid_protocol()
    payload["expected_predictions"][0]["baseline_mode"] = " "

    with pytest.raises(ValueError, match="baseline_mode"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["expected_predictions"][0]["application_count"] = -1

    with pytest.raises(ValueError, match="application_count"):
        validate_d3_comparison_protocol_payload(payload)

    payload = _valid_protocol()
    payload["expected_predictions"][0]["max_budget"] = -0.1

    with pytest.raises(ValueError, match="max_budget"):
        validate_d3_comparison_protocol_payload(payload)


def _valid_protocol() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_comparison_protocol",
        "protocol_id": "d3-heldout-comparison-v1",
        "project_id": "project-d3",
        "dataset_name": "Held-out D3 comparison v1",
        "split": "held_out",
        "gold_set_id": "d3-heldout-v1",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "expected_predictions": [
            {
                "baseline_name": "single_prompt_baseline",
                "baseline_mode": "single_prompt",
                "model_name": "generic-baseline-model",
                "application_count": 12,
                "trace_id": "qualitative_coding/d3-baseline/project-d3",
                "max_budget": 1.0,
                "prediction_file_sha256": "c" * 64,
            }
        ],
        "success_criteria": [
            "Score application baselines against the same held-out D3 gold."
        ],
        "caution": (
            "D3 comparison protocol validation is process metadata only; it is not "
            "held-out D3 evidence, expert-parity evidence, or superiority evidence."
        ),
    }
