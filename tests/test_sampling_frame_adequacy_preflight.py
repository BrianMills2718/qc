"""Tests for sampling-frame adequacy protocol/result preflight."""

import hashlib
import json

from qc_clean.core.sampling_frame_adequacy_preflight import (
    preflight_sampling_frame_adequacy_payloads,
)
from scripts import preflight_sampling_frame_adequacy_protocol


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64
_SCOPE_HASH = "c" * 64
_OUTCOME_HASH = "d" * 64
_DIMENSIONS = [
    "population_alignment",
    "frame_coverage",
    "recruitment_selection_fit",
    "inclusion_exclusion_fit",
    "transferability_limits",
]


def test_preflight_sampling_frame_adequacy_accepts_matching_protocol_and_rows():
    report = preflight_sampling_frame_adequacy_payloads(
        _protocol_payload(),
        _result_payload(),
        adequacy_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "pass"
    assert report.protocol_id == "sampling-frame-heldout-v1"
    assert report.result_row_count == len(_DIMENSIONS)
    assert report.reviewer_count == 2
    assert report.reviewer_types == ["domain_expert", "methodologist"]
    assert report.ratings == ["adequate", "partial"]
    assert report.errors == []
    assert "not sampling-frame adequacy evidence" in report.caution


def test_preflight_sampling_frame_adequacy_requires_result_file():
    report = preflight_sampling_frame_adequacy_payloads(_protocol_payload(), None)

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["adequacy_file"]
    assert "requires a result package" in report.errors[0].message


def test_preflight_sampling_frame_adequacy_rejects_hash_lock_mismatch():
    report = preflight_sampling_frame_adequacy_payloads(
        _protocol_payload(),
        _result_payload(),
        adequacy_file_sha256="e" * 64,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["adequacy_file_sha256"]
    assert "does not match actual file hash" in report.errors[0].message


def test_preflight_sampling_frame_adequacy_rejects_reviewer_and_dimension_drift():
    payload = _result_payload()
    payload["evaluations"] = [
        {
            **payload["evaluations"][0],
            "reviewer_type": "student",
            "dimension": "population_alignment",
        }
    ]

    report = preflight_sampling_frame_adequacy_payloads(
        _protocol_payload(),
        payload,
        adequacy_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    fields = {error.field for error in report.errors}
    assert {"reviewer_types", "reviewer_count", "dimensions"} <= fields


def test_preflight_sampling_frame_adequacy_rejects_protocol_metadata_drift():
    payload = _result_payload()
    payload["project_id"] = "other-project"

    report = preflight_sampling_frame_adequacy_payloads(
        _protocol_payload(),
        payload,
        adequacy_file_sha256=_OUTCOME_HASH,
    )

    assert report.status == "fail"
    assert [error.field for error in report.errors] == ["project_id"]


def test_preflight_sampling_frame_adequacy_script_outputs_json(tmp_path, capsys):
    result_payload = _result_payload()
    result_path = tmp_path / "sampling_frame_adequacy.json"
    result_path.write_text(json.dumps(result_payload), encoding="utf-8")
    result_hash = hashlib.sha256(result_path.read_bytes()).hexdigest()

    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(
        json.dumps(_protocol_payload(outcome_file_sha256=result_hash)),
        encoding="utf-8",
    )

    exit_code = preflight_sampling_frame_adequacy_protocol.main(
        [str(protocol_path), "--adequacy-file", str(result_path)]
    )

    assert exit_code == 0
    valid_output = json.loads(capsys.readouterr().out)
    assert valid_output["status"] == "pass"
    assert valid_output["result_row_count"] == len(_DIMENSIONS)
    assert valid_output["reviewer_count"] == 2

    exit_code = preflight_sampling_frame_adequacy_protocol.main([str(protocol_path)])

    assert exit_code == 1
    invalid_output = json.loads(capsys.readouterr().out)
    assert invalid_output["status"] == "fail"
    assert invalid_output["errors"][0]["field"] == "adequacy_file"


def _protocol_payload(*, outcome_file_sha256: str | None = _OUTCOME_HASH) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.sampling_frame_adequacy_protocol",
        "protocol_id": "sampling-frame-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Sampling-frame adequacy held-out v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "corpus_scope_sha256": _SCOPE_HASH,
        "scope_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "reviewer_plan": {
            "reviewer_types": ["methodologist", "domain_expert"],
            "planned_reviewer_count": 2,
            "qualification": "Qualitative-methods reviewer and domain reviewer.",
        },
        "dimensions": list(_DIMENSIONS),
        "outcome_file": "sampling_frame_adequacy.json",
        "outcome_file_sha256": outcome_file_sha256,
        "success_criteria": [
            {
                "dimension": dimension,
                "pass_condition": f"Report {dimension} rating and rationale.",
            }
            for dimension in _DIMENSIONS
        ],
    }


def _result_payload() -> dict:
    evaluations = []
    for index, dimension in enumerate(_DIMENSIONS):
        reviewer = "methodologist-1" if index % 2 == 0 else "domain-1"
        reviewer_type = "methodologist" if index % 2 == 0 else "domain_expert"
        rating = "adequate" if index < 2 else "partial"
        evaluations.append({
            "reviewer": reviewer,
            "reviewer_type": reviewer_type,
            "dimension": dimension,
            "rating": rating,
            "rationale": f"{dimension} rationale.",
            "evidence_refs": ["corpus_scope", "recruitment_notes"],
            "recommendation": "Report caveats with exported claims.",
        })
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.sampling_frame_adequacy_results",
        "protocol_id": "sampling-frame-heldout-v1",
        "project_id": "project-alpha",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "corpus_scope_sha256": _SCOPE_HASH,
        "evaluations": evaluations,
    }
