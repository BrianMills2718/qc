"""Tests for the theoretical-sampling result export script."""

from __future__ import annotations

import json

from scripts import export_theoretical_sampling_results


def test_export_theoretical_sampling_results_writes_output_and_stdout(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    candidates_path = tmp_path / "candidates.json"
    output_file = tmp_path / "results.json"
    protocol_path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")
    candidates_path.write_text(json.dumps(_valid_candidates()), encoding="utf-8")

    exit_code = export_theoretical_sampling_results.main([
        str(protocol_path),
        "--candidates-file",
        str(candidates_path),
        "--selected-candidate-id",
        "candidate-1",
        "--success-criterion-met",
        "Every targeted gap has an explicit sampling decision.",
        "--output",
        str(output_file),
    ])

    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.theoretical_sampling_results"
    assert stdout_payload["selected_candidate_ids"] == ["candidate-1"]


def test_export_theoretical_sampling_results_returns_json_error(tmp_path, capsys):
    protocol_path = tmp_path / "protocol.json"
    candidates_path = tmp_path / "candidates.json"
    protocol_path.write_text(json.dumps(_valid_protocol()), encoding="utf-8")
    candidates_path.write_text(json.dumps(_valid_candidates()), encoding="utf-8")

    exit_code = export_theoretical_sampling_results.main([
        str(protocol_path),
        "--candidates-file",
        str(candidates_path),
        "--selected-candidate-id",
        "missing-candidate",
        "--success-criterion-met",
        "Every targeted gap has an explicit sampling decision.",
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "missing-candidate" in output["error"]


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
