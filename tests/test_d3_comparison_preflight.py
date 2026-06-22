"""Tests for D3 baseline comparison protocol preflight."""

from __future__ import annotations

import hashlib
import json

from qc_clean.core.d3_comparison_preflight import preflight_d3_comparison_payloads
from scripts import preflight_d3_comparison


def test_d3_comparison_preflight_accepts_matching_protocol_gold_and_predictions():
    report = preflight_d3_comparison_payloads(
        _valid_protocol(prediction_file_sha256="c" * 64),
        _valid_gold_package(),
        [_valid_baseline_package()],
        prediction_file_sha256_by_baseline={"single_prompt_baseline": "c" * 64},
    )

    assert report.status == "pass"
    assert report.protocol_id == "d3-heldout-comparison-v1"
    assert report.gold_set_id == "d3-heldout-v1"
    assert report.expected_prediction_count == 1
    assert report.prediction_package_count == 1
    assert report.baseline_count == 1
    assert report.errors == []


def test_d3_comparison_preflight_rejects_gold_mismatch():
    gold = _valid_gold_package()
    gold["gold_set_id"] = "different-gold"

    report = preflight_d3_comparison_payloads(
        _valid_protocol(),
        gold,
        [_valid_baseline_package()],
    )

    assert report.status == "fail"
    assert any(error.field == "gold_set_id" for error in report.errors)


def test_d3_comparison_preflight_rejects_prediction_config_mismatch():
    package = _valid_baseline_package()
    package["application_baseline_run"]["baseline_mode"] = "different_mode"
    package["application_baseline_run"]["model_name"] = "different-model"
    package["application_baseline_run"]["application_count"] = 2
    package["application_baselines"][0]["code_applications"].append({
        "code_id": "AI_USE",
        "doc_id": "d1",
        "start_char": 10,
        "end_char": 20,
    })

    report = preflight_d3_comparison_payloads(
        _valid_protocol(),
        _valid_gold_package(),
        [package],
    )

    fields = {error.field for error in report.errors}
    assert report.status == "fail"
    assert "baseline_mode" in fields
    assert "model_name" in fields
    assert "application_count" in fields


def test_d3_comparison_preflight_rejects_prediction_file_hash_mismatch():
    report = preflight_d3_comparison_payloads(
        _valid_protocol(prediction_file_sha256="c" * 64),
        _valid_gold_package(),
        [_valid_baseline_package()],
        prediction_file_sha256_by_baseline={"single_prompt_baseline": "d" * 64},
    )

    assert report.status == "fail"
    assert any(error.field == "prediction_file_sha256" for error in report.errors)


def test_d3_comparison_preflight_script_outputs_json(tmp_path, capsys):
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(json.dumps(_valid_gold_package()), encoding="utf-8")
    prediction_file = tmp_path / "prediction.json"
    prediction_file.write_text(json.dumps(_valid_baseline_package()), encoding="utf-8")
    protocol = _valid_protocol(prediction_file_sha256=_sha256_file(prediction_file))
    protocol_file = tmp_path / "protocol.json"
    protocol_file.write_text(json.dumps(protocol), encoding="utf-8")

    exit_code = preflight_d3_comparison.main([
        str(protocol_file),
        str(gold_file),
        str(prediction_file),
    ])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "pass"
    assert output["prediction_package_count"] == 1


def test_d3_comparison_preflight_script_reports_failure_json(tmp_path, capsys):
    gold_file = tmp_path / "gold.json"
    gold = _valid_gold_package()
    gold["corpus_sha256"] = "d" * 64
    gold_file.write_text(json.dumps(gold), encoding="utf-8")
    prediction_file = tmp_path / "prediction.json"
    prediction_file.write_text(json.dumps(_valid_baseline_package()), encoding="utf-8")
    protocol_file = tmp_path / "protocol.json"
    protocol_file.write_text(json.dumps(_valid_protocol()), encoding="utf-8")

    exit_code = preflight_d3_comparison.main([
        str(protocol_file),
        str(gold_file),
        str(prediction_file),
    ])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "fail"
    assert output["errors"][0]["field"] == "corpus_sha256"


def _valid_protocol(*, prediction_file_sha256: str | None = None) -> dict:
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
                "application_count": 1,
                "trace_id": "qualitative_coding/d3-baseline/project-d3",
                "max_budget": 1.0,
                "prediction_file_sha256": prediction_file_sha256,
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


def _valid_gold_package() -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "d3-heldout-v1",
        "dataset_name": "Held-out D3 comparison v1",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "expert-panel",
            "protocol": "Independent coding followed by adjudication.",
            "human_human_agreement": None,
            "notes": "",
        },
        "application_gold": [
            {
                "code_id": "AI_USE",
                "doc_id": "d1",
                "start_char": 0,
                "end_char": 9,
            }
        ],
    }


def _valid_baseline_package() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_predictions",
        "application_baseline_run": {
            "project_id": "project-d3",
            "baseline_mode": "single_prompt",
            "generated_at": "2026-06-22T00:00:00Z",
            "model_name": "generic-baseline-model",
            "application_count": 1,
            "notes": "",
        },
        "application_baselines": [
            {
                "name": "single_prompt_baseline",
                "description": "Single-prompt application baseline.",
                "code_applications": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": "d1",
                        "start_char": 0,
                        "end_char": 9,
                    }
                ],
            }
        ],
    }


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
