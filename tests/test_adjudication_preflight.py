"""Tests for adjudication protocol-to-sample preflight checks."""

import hashlib
import json

from qc_clean.core import adjudication_preflight
from scripts import preflight_adjudication_protocol_sample


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64


def test_preflight_accepts_matching_protocol_and_sample(tmp_path):
    sample_path, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash)

    report = adjudication_preflight.preflight_adjudication_protocol_sample_payloads(
        protocol,
        sample_payload,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "pass"
    assert report.protocol_id == "study-heldout-v1"
    assert report.sample_package_sha256 == sample_hash
    assert report.returned_counts["code_application"] == 1
    assert report.returned_counts["negative_case"] == 1
    assert report.total_returned_count == 2
    assert not report.errors
    assert "not expert evidence" in report.caution
    assert sample_path.exists()


def test_preflight_rejects_project_or_corpus_mismatch(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path, project_id="other-project")
    protocol = _protocol_payload(sample_hash=sample_hash)

    report = adjudication_preflight.preflight_adjudication_protocol_sample_payloads(
        protocol,
        sample_payload,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "project_id" in _error_fields(report)


def test_preflight_rejects_sample_file_hash_mismatch(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash="d" * 64)

    report = adjudication_preflight.preflight_adjudication_protocol_sample_payloads(
        protocol,
        sample_payload,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "sample_package_sha256" in _error_fields(report)


def test_preflight_rejects_missing_required_target_type(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path, target_item_types=["code_application"])
    protocol = _protocol_payload(sample_hash=sample_hash, planned_sample_size=1)

    report = adjudication_preflight.preflight_adjudication_protocol_sample_payloads(
        protocol,
        sample_payload,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "target_item_types.negative_case" in _error_fields(report)


def test_preflight_rejects_undersized_sample(tmp_path):
    _, sample_payload, sample_hash = _write_sample(tmp_path)
    protocol = _protocol_payload(sample_hash=sample_hash, planned_sample_size=3)

    report = adjudication_preflight.preflight_adjudication_protocol_sample_payloads(
        protocol,
        sample_payload,
        sample_file_sha256=sample_hash,
    )

    assert report.status == "fail"
    assert "planned_sample_size" in _error_fields(report)


def test_preflight_script_outputs_json(tmp_path, capsys):
    sample_path, _sample_payload, sample_hash = _write_sample(tmp_path)
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(_protocol_payload(sample_hash=sample_hash)), encoding="utf-8")

    exit_code = preflight_adjudication_protocol_sample.main([
        str(protocol_path),
        str(sample_path),
    ])

    assert exit_code == 0
    ok_output = json.loads(capsys.readouterr().out)
    assert ok_output["status"] == "pass"
    assert ok_output["sample_package_sha256"] == sample_hash

    invalid_protocol = _protocol_payload(sample_hash=sample_hash)
    invalid_protocol["project_id"] = "wrong-project"
    invalid_protocol_path = tmp_path / "invalid_protocol.json"
    invalid_protocol_path.write_text(json.dumps(invalid_protocol), encoding="utf-8")

    exit_code = preflight_adjudication_protocol_sample.main([
        str(invalid_protocol_path),
        str(sample_path),
    ])

    assert exit_code == 1
    fail_output = json.loads(capsys.readouterr().out)
    assert fail_output["status"] == "fail"
    assert "project_id" in [error["field"] for error in fail_output["errors"]]


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
    returned = {target_type: 0 for target_type in [
        "code_application",
        "claim",
        "negative_case",
        "code_relationship",
        "entity_relationship",
    ]}
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
