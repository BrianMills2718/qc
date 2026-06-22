"""Tests for standalone D7 baseline package validation."""

from __future__ import annotations

import json

import pytest

from qc_clean.core.d7_baseline_package import (
    build_d7_baseline_package_report,
    d7_baselines_payload_for_scorecard,
    validate_d7_baseline_package_payload,
)
from qc_clean.core.d7_live_baseline import (
    D7LiveCandidateSelection,
    export_d7_live_candidate_baseline_async,
)
from qc_clean.core.d7_retrieval import export_d7_retrieval_baseline
from qc_clean.core.segmentation import segment_corpus
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    Code,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
from scripts import validate_d7_baseline_package
from scripts.bench_phase0 import load_d7_baselines_file


def test_validate_d7_baseline_package_accepts_retrieval_package():
    """Retrieval prediction packages validate at their own boundary."""
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    package = export_d7_retrieval_baseline(state, candidates_per_claim=1)

    validated = validate_d7_baseline_package_payload(package)
    report = build_d7_baseline_package_report(validated)

    assert validated.package_type == "qualitative_coding.d7_retrieval_predictions"
    assert report.status == "pass"
    assert report.prediction_package_type == "qualitative_coding.d7_retrieval_predictions"
    assert report.project_id == state.id
    assert report.baseline_count == 1
    assert report.candidate_count == 1
    assert report.baseline_names == ["retrieval_lexical_bm25_top1"]
    assert "not held-out D7 evidence" in report.caution


@pytest.mark.asyncio
async def test_validate_d7_baseline_package_accepts_live_package():
    """Live candidate-selection packages validate through the same boundary."""
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")

    async def fake_selector(*, candidates, **_kwargs):
        return D7LiveCandidateSelection(
            selected_candidate_ids=[candidates[0].id],
            rationale="Candidate directly contradicts the claim.",
        )

    package = await export_d7_live_candidate_baseline_async(
        state,
        model_name="fake-live-model",
        candidates_per_claim=1,
        candidate_selector=fake_selector,
    )

    validated = validate_d7_baseline_package_payload(package)
    report = build_d7_baseline_package_report(validated)

    assert validated.package_type == "qualitative_coding.d7_live_baseline_predictions"
    assert report.status == "pass"
    assert report.prediction_package_type == "qualitative_coding.d7_live_baseline_predictions"
    assert report.baseline_mode == "live_candidate_selector"
    assert report.project_id == state.id
    assert report.baseline_count == 1
    assert report.candidate_count == 1
    assert report.selected_candidate_count == 1


def test_validate_d7_baseline_package_rejects_malformed_versioned_package():
    """Recognized versioned packages fail when required metadata is missing."""
    malformed = {
        "schema_version": 1,
        "package_type": "qualitative_coding.d7_retrieval_predictions",
        "disconfirmation_baselines": [
            {"name": "empty", "description": "", "contrary_evidence": []}
        ],
    }

    with pytest.raises(ValueError, match="Invalid D7 baseline package"):
        validate_d7_baseline_package_payload(malformed)


def test_validate_d7_baseline_package_script_outputs_json(tmp_path, capsys):
    """The validator CLI emits machine-readable pass/fail output."""
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    package = export_d7_retrieval_baseline(state, candidates_per_claim=1)
    package_path = tmp_path / "d7_baseline.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")

    exit_code = validate_d7_baseline_package.main([str(package_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "pass"
    assert output["baseline_count"] == 1
    assert output["candidate_count"] == 1

    malformed_path = tmp_path / "malformed.json"
    malformed_path.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d7_retrieval_predictions",
            "disconfirmation_baselines": [],
        }),
        encoding="utf-8",
    )

    exit_code = validate_d7_baseline_package.main([str(malformed_path)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "fail"
    assert "Invalid D7 baseline package" in output["error"]


def test_phase0_d7_baselines_loader_rejects_invalid_versioned_package(tmp_path):
    """The direct BASELINES= loader validates recognized versioned packages."""
    malformed_path = tmp_path / "malformed_d7_package.json"
    malformed_path.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d7_retrieval_predictions",
            "disconfirmation_baselines": [
                {"name": "empty", "description": "", "contrary_evidence": []}
            ],
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid D7 baseline package"):
        load_d7_baselines_file(malformed_path)


def test_phase0_d7_baselines_loader_preserves_raw_list_compatibility(tmp_path):
    """Legacy raw baseline lists still feed the Phase 0 scorecard path."""
    raw_baselines = [
        {"name": "empty", "description": "No candidates.", "contrary_evidence": []}
    ]
    path = tmp_path / "raw_baselines.json"
    path.write_text(json.dumps(raw_baselines), encoding="utf-8")

    assert load_d7_baselines_file(path) == raw_baselines
    assert d7_baselines_payload_for_scorecard(raw_baselines) == raw_baselines


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    """Return a small project with one source-backed claim."""
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project-d7-baselines",
        name="D7 Baseline Project",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(id="AI_USE", name="AI use", description="AI-related claims"),
        ]),
        claims=[
            AnalyticClaim(
                id="claim-ai",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text=claim_text,
                scope=ClaimScope(corpus_level=True, code_ids=["AI_USE"]),
                origin_object_type="synthesis",
                origin_object_id="finding:0",
            )
        ],
    )
    state.segments = segment_corpus(state.corpus.documents)
    return state
