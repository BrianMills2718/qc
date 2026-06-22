"""Tests for D4 codebook-quality protocol/result preflight."""

import hashlib
import json

from qc_clean.core.d4_codebook_quality_preflight import (
    preflight_d4_codebook_quality_payloads,
)
from scripts import preflight_d4_codebook_quality_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_CODEBOOK_HASH = "c" * 64
_QUALITY_HASH = "d" * 64


def test_preflight_d4_codebook_quality_passes_matching_protocol_and_results():
    report = preflight_d4_codebook_quality_payloads(
        _protocol_payload(),
        _quality_payload(),
        quality_file_sha256=_QUALITY_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "d4-codebook-quality-heldout-v1"
    assert report.project_id == "project-alpha"
    assert report.rubric_metrics == [
        "clarity",
        "specificity",
        "usefulness",
        "grounding",
    ]
    assert report.target_scopes == ["codebook", "individual_code"]
    assert report.result_row_count == 2
    assert report.evaluator_count == 2
    assert report.evaluator_types == ["human_expert", "llm_judge"]
    assert report.errors == []
    assert "not blind expert-panel evidence" in report.caution


def test_preflight_d4_codebook_quality_fails_missing_or_invalid_results():
    report = preflight_d4_codebook_quality_payloads(_protocol_payload(), None)

    assert report.status == "fail"
    assert any(error.field == "quality_file" for error in report.errors)

    report = preflight_d4_codebook_quality_payloads(
        _protocol_payload(),
        {"codebook_quality_evaluations": []},
    )

    assert report.status == "fail"
    assert any(error.field == "quality_file" for error in report.errors)

    quality = _quality_payload()
    quality["codebook_quality_evaluations"][0]["clarity"] = 2.0

    report = preflight_d4_codebook_quality_payloads(_protocol_payload(), quality)

    assert report.status == "fail"
    assert any(error.field == "quality_file" for error in report.errors)


def test_preflight_d4_codebook_quality_fails_hash_and_evaluator_mismatches():
    protocol = _protocol_payload(planned_evaluator_count=3)
    quality = _quality_payload()
    quality["codebook_quality_evaluations"][0]["evaluator_type"] = "student_rater"

    report = preflight_d4_codebook_quality_payloads(
        protocol,
        quality,
        quality_file_sha256="0" * 64,
    )

    assert report.status == "fail"
    assert any(error.field == "quality_file_sha256" for error in report.errors)
    assert any(error.field == "evaluator_types" for error in report.errors)
    assert any(error.field == "evaluator_count" for error in report.errors)


def test_preflight_d4_codebook_quality_fails_scope_and_code_id_mismatches():
    quality = _quality_payload()
    quality["codebook_quality_evaluations"][0]["scope"] = "unregistered_scope"
    quality["codebook_quality_evaluations"][1].pop("code_id")

    report = preflight_d4_codebook_quality_payloads(_protocol_payload(), quality)

    assert report.status == "fail"
    assert any(error.field == "target_scopes" for error in report.errors)
    assert any(error.field == "individual_code_code_id" for error in report.errors)


def test_preflight_d4_codebook_quality_script_outputs_json(tmp_path, capsys):
    quality_path = tmp_path / "quality.json"
    quality_path.write_text(json.dumps(_quality_payload()), encoding="utf-8")

    protocol = _protocol_payload(quality_hash=_sha256_file(quality_path))
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")

    exit_code = preflight_d4_codebook_quality_protocol.main([
        str(protocol_path),
        "--quality-file",
        str(quality_path),
    ])

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["status"] == "pass"
    assert valid_output["result_row_count"] == 2
    assert valid_output["evaluator_count"] == 2

    exit_code = preflight_d4_codebook_quality_protocol.main([str(protocol_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["status"] == "fail"
    assert any(error["field"] == "quality_file" for error in invalid_output["errors"])


def _protocol_payload(
    *,
    quality_hash: str = _QUALITY_HASH,
    planned_evaluator_count: int = 2,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d4_codebook_quality_protocol",
        "protocol_id": "d4-codebook-quality-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D4 held-out codebook quality v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "codebook_artifact_sha256": _CODEBOOK_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "blinding": {
            "raters_blinded_to_origin": True,
            "source_labels_masked": True,
            "blinding_method": "Anonymized codebooks without origin labels.",
        },
        "evaluator_plan": {
            "evaluator_types": ["human_expert", "llm_judge"],
            "planned_evaluator_count": planned_evaluator_count,
            "qualification": "Expert qualitative rater plus frozen LLM judge.",
        },
        "rubric_metrics": ["clarity", "specificity", "usefulness", "grounding"],
        "target_scopes": ["codebook", "individual_code"],
        "outcome_file": "quality.json",
        "outcome_file_sha256": quality_hash,
        "success_criteria": [
            {
                "metric": "clarity",
                "pass_condition": "Report clarity mean and interval.",
            },
            {
                "metric": "specificity",
                "pass_condition": "Report specificity mean and interval.",
            },
            {
                "metric": "usefulness",
                "pass_condition": "Report usefulness mean and interval.",
            },
            {
                "metric": "grounding",
                "pass_condition": "Report grounding mean and interval.",
            },
        ],
    }


def _quality_payload() -> dict:
    return {
        "codebook_quality_evaluations": [
            {
                "evaluator": "expert-a",
                "evaluator_type": "human_expert",
                "clarity": 0.8,
                "specificity": 0.7,
                "usefulness": 0.9,
                "grounding": 1.0,
                "scope": "codebook",
            },
            {
                "evaluator": "judge-a",
                "evaluator_type": "llm_judge",
                "clarity": 0.9,
                "specificity": 0.8,
                "usefulness": 0.9,
                "grounding": 0.8,
                "scope": "individual_code",
                "code_id": "C-001",
            },
        ]
    }


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
