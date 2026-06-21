"""INV-2 regression tests for retrieval-first disconfirmation."""

from qc_clean.core.disconfirmation import (
    anchor_for_candidate,
    format_disconfirmation_candidates,
    retrieve_disconfirmation_candidates,
)
from qc_clean.core.grounding import verify_anchor
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


def test_retrieves_claim_relevant_segments_with_source_anchors():
    state = _state_with_segments(
        "AI improved workflow for the team.\n\n"
        "After errors, the team abandoned AI and returned to spreadsheets."
    )
    target = _claim("claim-ai", "AI improves workflow across the corpus.")

    candidates = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=3)

    assert candidates
    candidate = candidates[0]
    assert candidate.target_claim_id == "claim-ai"
    assert candidate.doc_id == "d1"
    assert candidate.start_char is not None
    assert candidate.end_char is not None
    assert candidate.quote_text == state.corpus.documents[0].content[
        candidate.start_char:candidate.end_char
    ]
    assert candidate.quote_hash is not None
    assert verify_anchor(
        state.corpus.documents[0].content,
        candidate.start_char,
        candidate.end_char,
        candidate.quote_hash,
    )


def test_retrieval_scores_contrary_cues_above_plain_mentions():
    state = _state_with_segments(
        "AI improves workflow every day.\n\n"
        "AI caused workflow errors, failed repeatedly, and made delivery worse."
    )
    target = _claim("claim-ai", "AI improves workflow across the corpus.")

    candidates = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=2)

    assert candidates[0].quote_text.startswith("AI caused workflow errors")
    assert {"errors", "failed", "worse"}.issubset(set(candidates[0].contrary_cues))
    assert candidates[0].score > candidates[1].score


def test_candidate_format_includes_ids_and_untrusted_data_boundaries():
    state = _state_with_segments("AI failed for this team.")
    target = _claim("claim-ai", "AI improves workflow across the corpus.")
    candidate = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=1)[0]

    formatted = format_disconfirmation_candidates([candidate])

    assert f"candidate_id={candidate.id}" in formatted
    assert "claim_id=claim-ai" in formatted
    assert f"span={candidate.start_char}:{candidate.end_char}" in formatted
    assert "BEGIN UNTRUSTED DATA BLOCK" in formatted
    assert "DATA> AI failed for this team." in formatted


def test_anchor_for_candidate_preserves_exact_source_span():
    state = _state_with_segments("AI failed for this team.")
    target = _claim("claim-ai", "AI improves workflow across the corpus.")
    candidate = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=1)[0]

    anchor = anchor_for_candidate(candidate)

    assert anchor.doc_id == candidate.doc_id
    assert anchor.segment_id == candidate.segment_id
    assert anchor.start_char == candidate.start_char
    assert anchor.end_char == candidate.end_char
    assert anchor.quote_text == candidate.quote_text
    assert anchor.quote_hash == candidate.quote_hash


def _state_with_segments(content: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="AI_USE",
                name="AI Use",
                description="Use of AI in workflow",
            ),
        ]),
    )
    state.segments = segment_corpus(state.corpus.documents)
    return state


def _claim(claim_id: str, text: str) -> AnalyticClaim:
    return AnalyticClaim(
        id=claim_id,
        claim_kind=ClaimKind.SYNTHESIS_FINDING,
        source_stage="synthesis",
        claim_text=text,
        scope=ClaimScope(corpus_level=True, code_ids=["AI_USE"]),
        origin_object_type="synthesis",
        origin_object_id="finding:0",
    )
