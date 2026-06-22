"""Tests for adjudication response package preflight checks."""

import copy
import hashlib
import json

from qc_clean.core import adjudication_response_preflight
from scripts import preflight_adjudication_responses


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64


def test_response_preflight_accepts_matching_protocol_sample_and_responses(tmp_path):
    sample_path, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "pass"
    assert report.protocol_id == "study-heldout-v1"
    assert report.project_id == "project-alpha"
    assert report.sample_project_id == "project-alpha"
    assert report.response_project_id == "project-alpha"
    assert report.sample_package_sha256 == sample_hash
    assert report.sample_item_count == 2
    assert report.response_item_count == 2
    assert report.completed_response_count == 2
    assert report.required_target_item_types == ["code_application", "negative_case"]
    assert report.completed_counts_by_target_type["code_application"] == 1
    assert report.completed_counts_by_target_type["negative_case"] == 1
    assert not report.errors
    assert "not expert evidence" in report.caution
    assert sample_path.exists()


def test_response_preflight_propagates_protocol_sample_failures(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path, project_id="other-project")
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "protocol_sample_preflight.project_id" in _error_fields(report)


def test_response_preflight_rejects_incomplete_responses(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)
    responses["items"][0].pop("response")

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "response_validation.response" in _error_fields(report)
    assert report.completed_response_count == 1


def test_response_preflight_rejects_item_id_mismatch(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)
    responses["items"][0]["item_id"] = "code_application:unexpected"

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "item_ids" in _error_fields(report)


def test_response_preflight_rejects_response_hash_mismatch(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)
    responses["project_state_sha256"] = "c" * 64

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "project_state_sha256" in _error_fields(report)


def test_response_preflight_rejects_missing_required_target_type_responses(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)
    responses = _completed_responses(sample_payload)
    responses["items"] = [
        item for item in responses["items"] if item["target_type"] != "negative_case"
    ]

    report = adjudication_response_preflight.preflight_adjudication_responses_payloads(
        protocol,
        sample_payload,
        responses,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "item_ids" in _error_fields(report)
    assert "target_item_types.negative_case" in _error_fields(report)


def test_response_preflight_script_outputs_json(tmp_path, capsys):
    sample_path, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(_protocol_payload(sample_hash=sample_hash)), encoding="utf-8")

    responses_path = tmp_path / "responses.json"
    responses_path.write_text(json.dumps(_completed_responses(sample_payload)), encoding="utf-8")

    exit_code = preflight_adjudication_responses.main([
        str(protocol_path),
        str(sample_path),
        str(responses_path),
    ])

    assert exit_code == 0
    ok_output = json.loads(capsys.readouterr().out)
    assert ok_output["status"] == "pass"
    assert ok_output["completed_response_count"] == 2

    invalid_responses = _completed_responses(sample_payload)
    invalid_responses["items"][0]["item_id"] = "wrong:item"
    invalid_responses_path = tmp_path / "invalid_responses.json"
    invalid_responses_path.write_text(json.dumps(invalid_responses), encoding="utf-8")

    exit_code = preflight_adjudication_responses.main([
        str(protocol_path),
        str(sample_path),
        str(invalid_responses_path),
    ])

    assert exit_code == 1
    fail_output = json.loads(capsys.readouterr().out)
    assert fail_output["status"] == "fail"
    assert "item_ids" in [error["field"] for error in fail_output["errors"]]


def _error_fields(report) -> set[str]:
    return {error.field for error in report.errors}


def _write_sample(
    tmp_path,
    *,
    project_id: str = "project-alpha",
    target_item_types: list[str] | None = None,
) -> tuple:
    target_item_types = target_item_types or ["code_application", "negative_case"]
    payload = _sample_payload(project_id=project_id, target_item_types=target_item_types)
    path = tmp_path / "sample.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path, payload, hashlib.sha256(path.read_bytes()).hexdigest()


def _sample_payload(
    *,
    project_id: str = "project-alpha",
    target_item_types: list[str],
) -> dict:
    items = [_sample_item(target_type, index) for index, target_type in enumerate(target_item_types)]
    returned = {
        target_type: 0
        for target_type in [
            "code_application",
            "claim",
            "negative_case",
            "code_relationship",
            "entity_relationship",
        ]
    }
    for item in items:
        returned[item["target_type"]] += 1
    returned["total"] = len(items)
    return {
        "schema_version": 1,
        "package_type": "adjudication_sample",
        "created_at": "2026-06-22T00:00:00+00:00",
        "project_id": project_id,
        "project_name": "Project Alpha",
        "hash_algorithm": "sha256",
        "project_state_sha256": _STATE_HASH,
        "corpus_sha256": _CORPUS_HASH,
        "corpus_scope": None,
        "sample_policy": {
            "type_order": [
                "code_application",
                "claim",
                "negative_case",
                "code_relationship",
                "entity_relationship",
            ],
            "ordering": "fixture",
            "limit_per_type": 1,
            "context_chars": 40,
            "sampling": "fixture",
        },
        "item_counts": {"available": returned, "returned": returned},
        "caution": "Sample fixture; not evidence.",
        "items": items,
    }


def _sample_item(target_type: str, index: int) -> dict:
    return {
        "item_id": f"{target_type}:{index}",
        "target_type": target_type,
        "target_id": f"target-{index}",
        "title": target_type,
        "prompt": "Review this item.",
        "payload": {"id": f"target-{index}"},
        "source_context": None,
    }


def _completed_responses(sample_payload: dict) -> dict:
    responses = copy.deepcopy(sample_payload)
    for item in responses["items"]:
        item["response"] = {
            "validity": "valid",
            "rationale": "The sampled item is valid.",
            "corrected_value": None,
            "adjudicator_id": "expert-a",
        }
    return responses


def _protocol_payload(*, sample_hash: str, planned_sample_size: int = 2) -> dict:
    return {
        "schema_version": 1,
        "package_type": "adjudication_protocol",
        "protocol_id": "study-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Study held-out adjudication v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_labeling": True,
        "coder_count": 2,
        "adjudicator": "expert-panel-chair",
        "coder_qualification": "Qualified qualitative researchers.",
        "target_dimensions": ["d3_application_validity", "d7_disconfirmation"],
        "sampling_plan": {
            "sample_package_path": "sample.json",
            "sample_package_sha256": sample_hash,
            "target_item_types": ["code_application", "negative_case"],
            "sampling_method": "Fixture sample.",
            "planned_sample_size": planned_sample_size,
        },
        "success_criteria": [
            {
                "dimension": "d3_application_validity",
                "metric": "exact_f1",
                "pass_condition": "Report point estimate and CI.",
            },
            {
                "dimension": "d7_disconfirmation",
                "metric": "recall",
                "pass_condition": "Report recall/precision.",
            },
        ],
    }
