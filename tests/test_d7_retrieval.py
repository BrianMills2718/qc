"""Tests for D7 retrieval-mode prediction export."""

from __future__ import annotations

import json

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
from scripts.bench_phase0 import load_d7_baselines_file


def test_exports_lexical_retrieval_candidates_as_d7_baseline_package():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")

    package = export_d7_retrieval_baseline(
        state,
        name="lexical_candidates",
        candidates_per_claim=1,
    )

    baseline = package["disconfirmation_baselines"][0]
    anchor = baseline["contrary_evidence"][0]
    assert package["package_type"] == "qualitative_coding.d7_retrieval_predictions"
    assert package["retrieval_run"]["retrieval_mode"] == "lexical_bm25"
    assert package["retrieval_run"]["target_claim_count"] == 1
    assert package["retrieval_run"]["candidate_count"] == 1
    assert baseline["name"] == "lexical_candidates"
    assert anchor["target_claim_id"] == "claim-ai"
    assert anchor["doc_id"] == "d1"
    assert anchor["start_char"] == 0
    assert anchor["end_char"] == len("AI failed badly after rollout.")
    assert anchor["quote_text"] == "AI failed badly after rollout."


def test_embedding_hybrid_export_can_use_injected_embedding_provider():
    state = _state_with_claim(
        "The participant preferred phone calls after long wait times.",
        "Automation improves service.",
    )

    def fake_embeddings(_texts, **_kwargs):
        return [[1.0, 0.0], [1.0, 0.0]]

    package = export_d7_retrieval_baseline(
        state,
        retrieval_mode="embedding_hybrid",
        embedding_model="fake-embedding-model",
        embedding_dimensions=2,
        expanded_term_weight=0.0,
        embedding_provider=fake_embeddings,
        candidates_per_claim=1,
    )

    baseline = package["disconfirmation_baselines"][0]
    anchor = baseline["contrary_evidence"][0]
    assert package["retrieval_run"]["retrieval_mode"] == "embedding_hybrid"
    assert package["retrieval_run"]["embedding_model"] == "fake-embedding-model"
    assert baseline["name"] == "retrieval_embedding_hybrid_top1_fake_embedding_model"
    assert anchor["target_claim_id"] == "claim-ai"
    assert anchor["quote_text"] == "The participant preferred phone calls after long wait times."


def test_export_does_not_mutate_project_state():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    state.segments = []
    before = state.model_dump(mode="json")

    export_d7_retrieval_baseline(state, candidates_per_claim=1)

    assert state.model_dump(mode="json") == before


def test_export_package_is_accepted_by_phase0_baseline_loader(tmp_path):
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    package = export_d7_retrieval_baseline(state, candidates_per_claim=1)
    path = tmp_path / "retrieval_predictions.json"
    path.write_text(json.dumps(package), encoding="utf-8")

    loaded = load_d7_baselines_file(path)

    assert loaded == package["disconfirmation_baselines"]


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
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
