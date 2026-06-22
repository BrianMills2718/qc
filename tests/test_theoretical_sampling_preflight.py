"""Tests for theoretical-sampling protocol/candidate/result preflight."""

from __future__ import annotations

import json

from qc_clean.core.theoretical_sampling_preflight import (
    preflight_theoretical_sampling_payloads,
)
from scripts import preflight_theoretical_sampling_protocol


def test_theoretical_sampling_preflight_passes_for_matching_candidates():
    report = preflight_theoretical_sampling_payloads(
        _valid_protocol(),
        _valid_candidates(),
    )

    assert report.status == "pass"
    assert report.protocol_id == "ts-protocol-v1"
    assert report.project_id == "project-gt"
    assert report.candidate_count == 2
    assert report.result_selected_count == 0
    assert report.target_gap_codes == ["TRUST", "ACCESS"]
    assert report.covered_gap_codes == ["ACCESS", "TRUST"]
    assert report.errors == []


def test_theoretical_sampling_preflight_rejects_protocol_candidate_drift():
    candidates = _valid_candidates()
    candidates["project_id"] = "other-project"
    candidates["candidate_source"] = "external_recruitment_pool"
    candidates["candidates"][0]["source_kind"] = "external_case"

    report = preflight_theoretical_sampling_payloads(
        _valid_protocol(),
        candidates,
    )

    assert report.status == "fail"
    messages = {error.field: error.message for error in report.errors}
    assert "project_id" in messages
    assert "candidate_source" in messages


def test_theoretical_sampling_preflight_rejects_missing_target_gap_coverage():
    candidates = _valid_candidates()
    candidates["candidates"] = [candidates["candidates"][0]]

    report = preflight_theoretical_sampling_payloads(
        _valid_protocol(),
        candidates,
    )

    assert report.status == "fail"
    assert any(
        error.field == "target_gap_codes" and "ACCESS" in error.message
        for error in report.errors
    )


def test_theoretical_sampling_preflight_rejects_unknown_selected_candidate():
    results = _valid_results()
    results["selected_candidate_ids"] = ["candidate-1", "missing-candidate"]

    report = preflight_theoretical_sampling_payloads(
        _valid_protocol(),
        _valid_candidates(),
        results,
    )

    assert report.status == "fail"
    assert any(
        error.field == "selected_candidate_ids"
        and "missing-candidate" in error.message
        for error in report.errors
    )


def test_preflight_theoretical_sampling_script_outputs_json(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    candidates_path = tmp_path / "candidates.json"
    results_path = tmp_path / "results.json"
    protocol_path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")
    candidates_path.write_text(json.dumps(_valid_candidates()), encoding="utf-8")
    results_path.write_text(json.dumps(_valid_results()), encoding="utf-8")

    exit_code = preflight_theoretical_sampling_protocol.main(
        [
            str(protocol_path),
            "--candidates-file",
            str(candidates_path),
            "--results-file",
            str(results_path),
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["package_type"] == "theoretical_sampling_protocol_preflight"
    assert output["status"] == "pass"
    assert output["result_selected_count"] == 2

    invalid_candidates = _valid_candidates()
    invalid_candidates["candidates"] = []
    candidates_path.write_text(json.dumps(invalid_candidates), encoding="utf-8")

    exit_code = preflight_theoretical_sampling_protocol.main(
        [str(protocol_path), "--candidates-file", str(candidates_path)]
    )

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "fail"
    assert output["errors"]


def _valid_protocol() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.theoretical_sampling_protocol",
        "protocol_id": "ts-protocol-v1",
        "project_id": "project-gt",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "registered_before_sampling": True,
        "candidate_source": "mixed",
        "collection_mode": "mixed",
        "target_gap_codes": ["TRUST", "ACCESS"],
        "target_gap_types": ["needs_properties", "needs_dimensions"],
        "thresholds": {
            "min_properties": 2,
            "min_dimensions": 2,
            "min_supporting_applications": 3,
            "min_supporting_documents": 2,
        },
        "max_suggestions": 5,
        "collection_rules": [
            "Prioritize cases that can elaborate category properties or dimensions.",
            "Do not report saturation until the stopping rule is met.",
        ],
        "stopping_rule": (
            "Stop only after all targeted categories meet thresholds or the protocol "
            "records why further collection is infeasible."
        ),
        "success_criteria": [
            "Every targeted gap has an explicit sampling decision.",
            "Every selected case records which category gap it addresses.",
        ],
        "caution": (
            "Theoretical sampling protocol metadata is process infrastructure only; "
            "it is not sampling adequacy evidence or saturation proof."
        ),
    }


def _valid_candidates() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.theoretical_sampling_candidates",
        "protocol_id": "ts-protocol-v1",
        "project_id": "project-gt",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "candidate_source": "mixed",
        "collection_mode": "mixed",
        "candidates": [
            {
                "candidate_id": "candidate-1",
                "source_kind": "loaded_document",
                "doc_id": "doc-1",
                "doc_name": "Interview 1",
                "gap_codes": ["TRUST"],
                "gap_types": ["needs_properties"],
                "priority_score": 2.0,
                "rationale": "Adds property evidence for TRUST.",
            },
            {
                "candidate_id": "candidate-2",
                "source_kind": "external_case",
                "doc_id": None,
                "doc_name": "Recruitment case A",
                "gap_codes": ["ACCESS"],
                "gap_types": ["needs_dimensions"],
                "priority_score": 1.0,
                "rationale": "Adds dimensional contrast for ACCESS.",
            },
        ],
        "caution": "Candidate pools are provenance metadata, not saturation evidence.",
    }


def _valid_results() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.theoretical_sampling_results",
        "protocol_id": "ts-protocol-v1",
        "project_id": "project-gt",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "selected_candidate_ids": ["candidate-1", "candidate-2"],
        "addressed_gap_codes": ["TRUST", "ACCESS"],
        "addressed_gap_types": ["needs_properties", "needs_dimensions"],
        "stopped_by_rule": False,
        "success_criteria_met": [
            "Every targeted gap has an explicit sampling decision.",
        ],
        "caution": "Sampling results are provenance metadata, not saturation evidence.",
    }
