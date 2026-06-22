"""Tests for D9 interpretive-preference protocol/result preflight."""

import hashlib
import json

from qc_clean.core.d9_interpretive_preference_preflight import (
    preflight_d9_interpretive_preference_payloads,
)
from scripts import preflight_d9_interpretive_preference_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_COMPARISON_ARTIFACT_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64


def test_preflight_d9_interpretive_preference_accepts_matching_protocol_and_rows():
    report = preflight_d9_interpretive_preference_payloads(
        _protocol_payload(),
        _preference_payload(),
        preference_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "d9-interpretive-preference-heldout-v1"
    assert report.result_row_count == 2
    assert report.case_count == 2
    assert report.evaluator_count == 2
    assert report.evaluator_types == ["human_expert"]
    assert report.target_criteria == ["interpretive_depth", "latent_meaning"]
    assert report.target_surfaces == ["codebook", "themes"]
    assert report.non_inferiority_margin == 0.1
    assert report.errors == []
    assert "not blind expert-parity evidence" in report.caution


def test_preflight_d9_interpretive_preference_requires_result_file():
    report = preflight_d9_interpretive_preference_payloads(_protocol_payload(), None)

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["preference_file"]
    assert "requires a preference result file" in report.errors[0].message


def test_preflight_d9_interpretive_preference_rejects_hash_lock_mismatch():
    report = preflight_d9_interpretive_preference_payloads(
        _protocol_payload(),
        _preference_payload(),
        preference_file_sha256="e" * 64,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["preference_file_sha256"]
    assert "does not match actual file hash" in report.errors[0].message


def test_preflight_d9_interpretive_preference_rejects_evaluator_criterion_and_surface_drift():
    payload = _preference_payload()
    payload["interpretive_preference_evaluations"] = [
        {
            **payload["interpretive_preference_evaluations"][0],
            "evaluator_type": "student",
            "criterion": "clarity",
            "surface": "memo",
        }
    ]

    report = preflight_d9_interpretive_preference_payloads(
        _protocol_payload(),
        payload,
        preference_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    fields = {error.field for error in report.errors}
    assert {"evaluator_types", "evaluator_count", "target_criteria", "target_surfaces"} <= fields


def test_preflight_d9_interpretive_preference_requires_planned_case_count():
    protocol = _protocol_payload()
    protocol["planned_case_count"] = 3

    report = preflight_d9_interpretive_preference_payloads(
        protocol,
        _preference_payload(),
        preference_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["planned_case_count"]
    assert "below planned count" in report.errors[0].message


def test_preflight_d9_interpretive_preference_script_outputs_json(tmp_path, capsys):
    preference_payload = _preference_payload()
    preference_path = tmp_path / "preference.json"
    preference_path.write_text(json.dumps(preference_payload), encoding="utf-8")
    preference_hash = hashlib.sha256(preference_path.read_bytes()).hexdigest()

    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(
        json.dumps(_protocol_payload(outcome_file_sha256=preference_hash)),
        encoding="utf-8",
    )

    exit_code = preflight_d9_interpretive_preference_protocol.main(
        [str(protocol_path), "--preference-file", str(preference_path)]
    )

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["status"] == "pass"
    assert valid_output["result_row_count"] == 2
    assert valid_output["case_count"] == 2

    exit_code = preflight_d9_interpretive_preference_protocol.main([str(protocol_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["status"] == "fail"
    assert invalid_output["errors"][0]["field"] == "preference_file"


def _protocol_payload(*, outcome_file_sha256: str | None = _OUTCOME_HASH) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d9_interpretive_preference_protocol",
        "protocol_id": "d9-interpretive-preference-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D9 held-out interpretive preference v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "comparison_artifact_sha256": _COMPARISON_ARTIFACT_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "blinded": True,
        "evaluator_plan": {
            "evaluator_types": ["human_expert"],
            "planned_evaluator_count": 2,
            "qualification": "Blind qualitative-methods expert panel.",
        },
        "target_criteria": ["interpretive_depth", "latent_meaning"],
        "target_surfaces": ["codebook", "themes"],
        "planned_case_count": 2,
        "non_inferiority_margin": 0.1,
        "outcome_metrics": [
            "system_minus_human_preference_rate",
            "system_preference_rate",
            "tie_rate",
        ],
        "outcome_file": "interpretive_preference.json",
        "outcome_file_sha256": outcome_file_sha256,
        "success_criteria": [
            {
                "metric": "system_minus_human_preference_rate",
                "pass_condition": "Lower CI bound must be above the margin.",
            },
            {
                "metric": "system_preference_rate",
                "pass_condition": "Report non-tie system preference rate and interval.",
            },
            {
                "metric": "tie_rate",
                "pass_condition": "Report tie rate and interval.",
            },
        ],
    }


def _preference_payload() -> dict:
    return {
        "interpretive_preference_evaluations": [
            {
                "case_id": "case-1",
                "evaluator": "expert-1",
                "evaluator_type": "human_expert",
                "preferred": "system",
                "criterion": "interpretive_depth",
                "surface": "codebook",
            },
            {
                "case_id": "case-2",
                "evaluator": "expert-2",
                "evaluator_type": "human_expert",
                "preferred": "human",
                "criterion": "latent_meaning",
                "surface": "themes",
            },
        ]
    }
