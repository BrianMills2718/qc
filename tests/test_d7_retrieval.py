"""Tests for D7 retrieval-mode prediction export."""

from __future__ import annotations

import hashlib
import json

import pytest

from qc_clean.core.d7_retrieval import (
    compare_d7_retrieval_predictions,
    export_d7_retrieval_baseline,
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


def test_export_records_project_hash_trace_and_budget_provenance():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")

    package = export_d7_retrieval_baseline(
        state,
        candidates_per_claim=1,
        trace_id="qualitative_coding/d7-retrieval/project-d7",
        max_budget=0.75,
    )

    metadata = package["retrieval_run"]
    assert metadata["project_id"] == state.id
    assert metadata["project_state_sha256"] == _sha256_jsonable(state.model_dump(mode="json"))
    assert metadata["corpus_sha256"] == _sha256_jsonable(state.corpus.model_dump(mode="json"))
    assert metadata["trace_id"] == "qualitative_coding/d7-retrieval/project-d7"
    assert metadata["max_budget"] == 0.75


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


def test_compares_retrieval_prediction_packages_against_gold():
    content = "AI failed badly after rollout.\n\nAI only succeeded elsewhere."
    state = _state_with_claim(content, "AI improves workflow.")
    good_package = export_d7_retrieval_baseline(
        state,
        name="good_retrieval",
        candidates_per_claim=1,
    )
    empty_package = {
        "disconfirmation_baselines": [
            {
                "name": "empty_retrieval",
                "description": "No candidates.",
                "contrary_evidence": [],
            }
        ]
    }
    gold = [
        {
            "target_claim_id": "claim-ai",
            "doc_id": "d1",
            "start_char": 0,
            "end_char": len("AI failed badly after rollout."),
        }
    ]

    report = compare_d7_retrieval_predictions(
        state,
        gold_payload=gold,
        prediction_packages=[good_package, empty_package],
    )

    baselines = report["disconfirmation_d7"]["baselines"]
    assert report["report_type"] == "qualitative_coding.d7_retrieval_comparison"
    assert report["package_count"] == 2
    assert report["baseline_count"] == 2
    assert baselines["good_retrieval"]["recall"] == 1.0
    assert baselines["good_retrieval"]["precision"] == 1.0
    assert baselines["empty_retrieval"]["recall"] == 0.0
    assert baselines["empty_retrieval"]["precision"] == 0.0


def test_comparison_report_includes_baseline_span_overlap():
    content = "0123456789abcdefghij0123456789"
    state = _state_with_claim(content, "AI improves workflow.")
    package = {
        "disconfirmation_baselines": [
            {
                "name": "near_retrieval",
                "description": "Near-boundary retrieval baseline.",
                "contrary_evidence": [
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": "d1",
                        "start_char": 15,
                        "end_char": 25,
                    }
                ],
            }
        ]
    }
    gold = [
        {
            "target_claim_id": "claim-ai",
            "doc_id": "d1",
            "start_char": 10,
            "end_char": 20,
        }
    ]

    report = compare_d7_retrieval_predictions(
        state,
        gold_payload=gold,
        prediction_packages=[package],
    )

    overlap = report["disconfirmation_d7"]["baselines"]["near_retrieval"]["span_overlap"]

    assert overlap["status"] == "scored"
    assert overlap["mean_best_gold_iou"] == pytest.approx(5 / 15)
    assert overlap["gold_best_overlaps"][0]["best_predicted_key"] == "claim-ai|d1|15:25"


def test_comparison_fails_loud_on_duplicate_baseline_names():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    package = export_d7_retrieval_baseline(
        state,
        name="duplicate",
        candidates_per_claim=1,
    )
    gold = [
        {
            "target_claim_id": "claim-ai",
            "doc_id": "d1",
            "start_char": 0,
            "end_char": len("AI failed badly after rollout."),
        }
    ]

    with pytest.raises(ValueError, match="Duplicate D7 baseline"):
        compare_d7_retrieval_predictions(
            state,
            gold_payload=gold,
            prediction_packages=[package, package],
        )


def test_comparison_does_not_mutate_project_state():
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    before = state.model_dump(mode="json")
    package = export_d7_retrieval_baseline(state, candidates_per_claim=1)
    gold = [
        {
            "target_claim_id": "claim-ai",
            "doc_id": "d1",
            "start_char": 0,
            "end_char": len("AI failed badly after rollout."),
        }
    ]

    compare_d7_retrieval_predictions(
        state,
        gold_payload=gold,
        prediction_packages=[package],
    )

    assert state.model_dump(mode="json") == before


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project-d7",
        name="D7 retrieval test",
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


def _sha256_jsonable(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
