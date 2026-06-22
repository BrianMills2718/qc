"""Tests for theoretical-sampling result package export."""

from __future__ import annotations

import pytest

from qc_clean.core.theoretical_sampling_preflight import (
    preflight_theoretical_sampling_payloads,
)
from qc_clean.core.theoretical_sampling_results import (
    export_theoretical_sampling_results,
)


def test_exports_preflight_ready_result_package():
    protocol = _valid_protocol()
    candidates = _valid_candidates()

    package = export_theoretical_sampling_results(
        protocol,
        candidates,
        selected_candidate_ids=["candidate-1"],
        success_criteria_met=[
            "Every targeted gap has an explicit sampling decision.",
        ],
    )
    report = preflight_theoretical_sampling_payloads(protocol, candidates, package)

    assert package["schema_version"] == 1
    assert package["package_type"] == "qualitative_coding.theoretical_sampling_results"
    assert package["protocol_id"] == "ts-protocol-v1"
    assert package["selected_candidate_ids"] == ["candidate-1"]
    assert package["addressed_gap_codes"] == ["TRUST"]
    assert package["addressed_gap_types"] == ["needs_properties"]
    assert package["stopped_by_rule"] is False
    assert report.status == "pass"


def test_result_export_rejects_unknown_selected_candidate():
    with pytest.raises(ValueError, match="unknown candidate ID"):
        export_theoretical_sampling_results(
            _valid_protocol(),
            _valid_candidates(),
            selected_candidate_ids=["missing-candidate"],
            success_criteria_met=[
                "Every targeted gap has an explicit sampling decision.",
            ],
        )


def test_result_export_rejects_unregistered_success_criterion():
    with pytest.raises(ValueError, match="unregistered success criteria"):
        export_theoretical_sampling_results(
            _valid_protocol(),
            _valid_candidates(),
            selected_candidate_ids=["candidate-1"],
            success_criteria_met=["Unregistered criterion"],
        )


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
        ],
        "stopping_rule": "Stop only after gap-specific sampling decisions are recorded.",
        "success_criteria": [
            "Every targeted gap has an explicit sampling decision.",
            "Every selected case records which category gap it addresses.",
        ],
        "caution": "Protocol metadata only; not saturation evidence.",
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
