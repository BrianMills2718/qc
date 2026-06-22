"""Tests for opt-in live D7 candidate-selection baseline export."""

from __future__ import annotations

import copy
import json

import pytest

from qc_clean.core.d7_live_baseline import (
    D7LiveCandidateSelection,
    export_d7_live_candidate_baseline_async,
)
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
from scripts.bench_phase0 import load_d7_baselines_file


@pytest.mark.asyncio
async def test_live_candidate_baseline_exports_selected_candidate_package(tmp_path):
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    calls = []

    async def fake_selector(*, target_claim, candidates, prompt, model_name, trace_id, max_budget):
        calls.append({
            "target_claim_id": target_claim.id,
            "candidate_ids": [candidate.id for candidate in candidates],
            "prompt": prompt,
            "model_name": model_name,
            "trace_id": trace_id,
            "max_budget": max_budget,
        })
        return D7LiveCandidateSelection(
            selected_candidate_ids=[candidates[0].id],
            rationale="Candidate directly contradicts the claim.",
        )

    package = await export_d7_live_candidate_baseline_async(
        state,
        model_name="fake-live-model",
        trace_id="trace-live",
        max_budget=0.5,
        candidates_per_claim=1,
        candidate_selector=fake_selector,
    )

    assert package["schema_version"] == 1
    assert package["package_type"] == "qualitative_coding.d7_live_baseline_predictions"
    metadata = package["live_baseline_run"]
    assert metadata["project_id"] == state.id
    assert metadata["baseline_mode"] == "live_candidate_selector"
    assert metadata["model"] == "fake-live-model"
    assert metadata["trace_id"] == "trace-live"
    assert metadata["max_budget"] == 0.5
    assert metadata["target_claim_count"] == 1
    assert metadata["candidate_count"] == 1
    assert metadata["selected_candidate_count"] == 1
    assert set(metadata["prompt_hashes"]) == {"claim-ai"}
    assert calls[0]["target_claim_id"] == "claim-ai"
    assert calls[0]["candidate_ids"] == ["dc-0-1"]
    assert "candidate_id=dc-0-1" in calls[0]["prompt"]
    assert calls[0]["trace_id"] == "trace-live/claim-ai"

    baseline = package["disconfirmation_baselines"][0]
    anchor = baseline["contrary_evidence"][0]
    assert baseline["name"] == "live_candidate_selector_fake_live_model_lexical_bm25_top1"
    assert anchor["target_claim_id"] == "claim-ai"
    assert anchor["doc_id"] == "d1"
    assert anchor["start_char"] == 0
    assert anchor["end_char"] == len("AI failed badly after rollout.")
    assert anchor["quote_text"] == "AI failed badly after rollout."
    assert package["selection_records"][0]["selected_candidate_ids"] == ["dc-0-1"]

    package_path = tmp_path / "live_baseline.json"
    package_path.write_text(json.dumps(package), encoding="utf-8")
    assert load_d7_baselines_file(package_path) == package["disconfirmation_baselines"]


@pytest.mark.asyncio
async def test_live_candidate_baseline_rejects_unknown_candidate_id():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")

    async def fake_selector(**_kwargs):
        return D7LiveCandidateSelection(
            selected_candidate_ids=["missing-candidate"],
            rationale="Invented ID.",
        )

    with pytest.raises(ValueError, match="unknown candidate_id"):
        await export_d7_live_candidate_baseline_async(
            state,
            model_name="fake-live-model",
            candidates_per_claim=1,
            candidate_selector=fake_selector,
        )


@pytest.mark.asyncio
async def test_live_candidate_baseline_does_not_mutate_project_state():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    before = copy.deepcopy(state.model_dump(mode="json"))

    async def fake_selector(*, candidates, **_kwargs):
        return D7LiveCandidateSelection(
            selected_candidate_ids=[candidates[0].id],
            rationale="Candidate directly contradicts the claim.",
        )

    await export_d7_live_candidate_baseline_async(
        state,
        model_name="fake-live-model",
        candidates_per_claim=1,
        candidate_selector=fake_selector,
    )

    assert state.model_dump(mode="json") == before


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project-d7-live",
        name="D7 live baseline test",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="AI_USE",
                name="AI Use",
                description="Use of AI in workflow",
            )
        ]),
        claims=[_claim(claim_text)],
    )
    state.segments = segment_corpus(state.corpus.documents)
    return state


def _claim(text: str) -> AnalyticClaim:
    return AnalyticClaim(
        id="claim-ai",
        claim_kind=ClaimKind.SYNTHESIS_FINDING,
        source_stage="synthesis",
        claim_text=text,
        scope=ClaimScope(corpus_level=True, code_ids=["AI_USE"]),
        origin_object_type="synthesis",
        origin_object_id="finding:0",
    )
