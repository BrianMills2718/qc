"""Tests for D8 GT-fidelity protocol/result preflight."""

import hashlib
import json

from qc_clean.core.d8_gt_fidelity_preflight import (
    preflight_d8_gt_fidelity_payloads,
)
from scripts import preflight_d8_gt_fidelity_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_GT_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_preflight_d8_gt_fidelity_accepts_matching_protocol_and_rows():
    report = preflight_d8_gt_fidelity_payloads(
        _protocol_payload(),
        _gt_fidelity_payload(),
        gt_fidelity_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "d8-gt-fidelity-heldout-v1"
    assert report.result_row_count == 2
    assert report.evaluator_count == 2
    assert report.evaluator_types == ["human_expert", "llm_judge"]
    assert report.target_scopes == ["grounded_theory_pipeline", "category"]
    assert report.artifact_count == 1
    assert report.errors == []
    assert "not expert-rubric acceptance" in report.caution


def test_preflight_d8_gt_fidelity_requires_result_file():
    report = preflight_d8_gt_fidelity_payloads(_protocol_payload(), None)

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["gt_fidelity_file"]
    assert "requires a GT-fidelity result file" in report.errors[0].message


def test_preflight_d8_gt_fidelity_rejects_hash_lock_mismatch():
    report = preflight_d8_gt_fidelity_payloads(
        _protocol_payload(),
        _gt_fidelity_payload(),
        gt_fidelity_file_sha256="e" * 64,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["gt_fidelity_file_sha256"]
    assert "does not match actual file hash" in report.errors[0].message


def test_preflight_d8_gt_fidelity_rejects_evaluator_and_scope_drift():
    payload = _gt_fidelity_payload()
    payload["gt_fidelity_evaluations"] = [
        {
            **payload["gt_fidelity_evaluations"][0],
            "evaluator_type": "student",
            "scope": "memo",
            "artifact_id": "memo-1",
        }
    ]

    report = preflight_d8_gt_fidelity_payloads(
        _protocol_payload(),
        payload,
        gt_fidelity_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    fields = {error.field for error in report.errors}
    assert {"evaluator_types", "evaluator_count", "target_scopes"} <= fields


def test_preflight_d8_gt_fidelity_requires_artifact_ids_for_targeted_scopes():
    payload = _gt_fidelity_payload()
    payload["gt_fidelity_evaluations"][1]["artifact_id"] = None

    report = preflight_d8_gt_fidelity_payloads(
        _protocol_payload(),
        payload,
        gt_fidelity_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["targeted_scope_artifact_id"]
    assert "artifact_id" in report.errors[0].message


def test_preflight_d8_gt_fidelity_script_outputs_json(tmp_path, capsys):
    gt_payload = _gt_fidelity_payload()
    gt_path = tmp_path / "gt_fidelity.json"
    gt_path.write_text(json.dumps(gt_payload), encoding="utf-8")
    gt_hash = hashlib.sha256(gt_path.read_bytes()).hexdigest()

    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(
        json.dumps(_protocol_payload(outcome_file_sha256=gt_hash)),
        encoding="utf-8",
    )

    exit_code = preflight_d8_gt_fidelity_protocol.main(
        [str(protocol_path), "--gt-fidelity-file", str(gt_path)]
    )

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["status"] == "pass"
    assert valid_output["result_row_count"] == 2
    assert valid_output["artifact_count"] == 1

    exit_code = preflight_d8_gt_fidelity_protocol.main([str(protocol_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["status"] == "fail"
    assert invalid_output["errors"][0]["field"] == "gt_fidelity_file"


def _protocol_payload(*, outcome_file_sha256: str | None = _OUTCOME_HASH) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d8_gt_fidelity_protocol",
        "protocol_id": "d8-gt-fidelity-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D8 held-out GT fidelity v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "gt_artifact_sha256": _GT_ARTIFACT_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "evaluator_plan": {
            "evaluator_types": ["human_expert", "llm_judge"],
            "planned_evaluator_count": 2,
            "qualification": "GT-methods experts plus frozen LLM judge.",
        },
        "rubric_metrics": [
            "constant_comparison",
            "category_development",
            "memo_quality",
            "saturation_justification",
        ],
        "target_scopes": ["grounded_theory_pipeline", "category"],
        "outcome_file": "gt_fidelity.json",
        "outcome_file_sha256": outcome_file_sha256,
        "success_criteria": [
            {
                "metric": "constant_comparison",
                "pass_condition": "Report constant-comparison mean and interval.",
            },
            {
                "metric": "category_development",
                "pass_condition": "Report category-development mean and interval.",
            },
            {
                "metric": "memo_quality",
                "pass_condition": "Report memo-quality mean and interval.",
            },
            {
                "metric": "saturation_justification",
                "pass_condition": "Report saturation-justification mean and interval.",
            },
        ],
    }


def _gt_fidelity_payload() -> dict:
    return {
        "gt_fidelity_evaluations": [
            {
                "evaluator": "expert-1",
                "evaluator_type": "human_expert",
                "constant_comparison": 0.8,
                "category_development": 0.7,
                "memo_quality": 0.75,
                "saturation_justification": 0.65,
                "scope": "grounded_theory_pipeline",
            },
            {
                "evaluator": "judge-1",
                "evaluator_type": "llm_judge",
                "constant_comparison": 0.7,
                "category_development": 0.8,
                "memo_quality": 0.7,
                "saturation_justification": 0.6,
                "scope": "category",
                "artifact_id": "category-1",
            },
        ]
    }
