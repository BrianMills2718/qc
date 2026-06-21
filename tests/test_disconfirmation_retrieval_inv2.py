"""INV-2 regression tests for retrieval-first disconfirmation."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.claims import claims_for_negative_cases
from qc_clean.core.disconfirmation import (
    anchor_for_candidate,
    format_disconfirmation_candidates,
    retrieve_disconfirmation_candidates,
)
from qc_clean.core.grounding import verify_anchor
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.negative_case import (
    NegativeCase,
    NegativeCaseResponse,
    NegativeCaseStage,
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


def test_bm25_ranks_rare_specific_terms_above_repeated_generic_terms():
    state = _state_with_segments(
        "AI workflow updates improved speed.\n\n"
        "AI workflow updates stayed stable.\n\n"
        "AI workflow updates continued.\n\n"
        "Trust collapsed after the rollout."
    )
    target = _claim("claim-trust", "AI workflow trust across the corpus.")

    candidates = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=4)

    assert candidates[0].quote_text == "Trust collapsed after the rollout."
    assert candidates[0].matched_terms == ["trust"]
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


def test_negative_case_prompt_uses_retrieved_candidates_not_full_corpus():
    state = _state_with_segments(
        "AI failed for this team after repeated errors.\n\n"
        "This irrelevant paragraph should not be sent to the negative-case prompt."
    )
    state.claims = [_claim("claim-ai", "AI improves workflow across the corpus.")]
    captured_prompt = ""
    response = NegativeCaseResponse(
        negative_cases=[],
        overall_assessment="No retrieved candidate was sufficient.",
    )

    async def capture_prompt(prompt, *_args, **_kwargs):
        nonlocal captured_prompt
        captured_prompt = prompt
        return response

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(side_effect=capture_prompt)
        result = asyncio.run(
            NegativeCaseStage().execute(
                state,
                PipelineContext(disconfirmation_candidates_per_claim=1),
            )
        )

    assert "RETRIEVAL-FIRST SOURCE CANDIDATES" in captured_prompt
    assert "candidate_id=dc-0-1" in captured_prompt
    assert "DATA> AI failed for this team after repeated errors." in captured_prompt
    assert "irrelevant paragraph should not be sent" not in captured_prompt
    assert "INTERVIEW DATA:" not in captured_prompt
    assert result.memos[0].memo_type == "negative_case"
    assert "Retrieval-First Candidate Search" in result.memos[0].content
    assert "Retrieved 1 candidate passage(s) for 1 claim target(s)." in result.memos[0].content


def test_negative_case_candidate_id_creates_exact_contrary_anchor():
    state = _state_with_segments("AI failed for this team after repeated errors.")
    target = _claim("claim-ai", "AI improves workflow across the corpus.")
    state.claims = [target]
    candidate = retrieve_disconfirmation_candidates(state, [target], candidates_per_claim=1)[0]
    negative_case = NegativeCase(
        code_name="AI Use",
        target_claim_id="claim-ai",
        candidate_id=candidate.id,
        disconfirming_evidence="a paraphrase that does not appear literally",
        explanation="The retrieved source says AI failed.",
        implication="The improvement claim needs a failure boundary condition.",
    )

    claims = claims_for_negative_cases(
        state,
        [negative_case],
        candidate_anchors={candidate.id: anchor_for_candidate(candidate)},
    )

    anchor = claims[0].contrary_anchors[0]
    assert anchor.doc_id == candidate.doc_id
    assert anchor.segment_id == candidate.segment_id
    assert anchor.start_char == candidate.start_char
    assert anchor.end_char == candidate.end_char
    assert anchor.quote_text == candidate.quote_text
    assert claims[0].scope.claim_ids == ["claim-ai"]


def test_invalid_negative_case_candidate_id_fails_loud():
    state = _state_with_segments("AI failed for this team after repeated errors.")
    negative_case = NegativeCase(
        code_name="AI Use",
        candidate_id="missing-candidate",
        disconfirming_evidence="AI failed",
        explanation="The retrieved source says AI failed.",
        implication="The claim needs a boundary condition.",
    )

    with pytest.raises(ValueError, match="missing-candidate"):
        claims_for_negative_cases(state, [negative_case], candidate_anchors={})


def test_negative_case_uses_configured_disconfirmation_model():
    state = _state_with_segments("AI failed for this team after repeated errors.")
    state.claims = [_claim("claim-ai", "AI improves workflow across the corpus.")]
    response = NegativeCaseResponse(
        negative_cases=[],
        overall_assessment="No retrieved candidate was sufficient.",
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=response)
        result = asyncio.run(
            NegativeCaseStage().execute(
                state,
                PipelineContext(
                    model_name="primary-model",
                    disconfirmation_model_name="adversarial-reviewer-model",
                ),
            )
        )

    MockLLM.assert_called_once_with(model_name="adversarial-reviewer-model")
    assert "Interpretation model: adversarial-reviewer-model." in result.memos[0].content


def test_negative_case_defaults_to_pipeline_model_without_disconfirmation_override():
    state = _state_with_segments("AI failed for this team after repeated errors.")
    state.claims = [_claim("claim-ai", "AI improves workflow across the corpus.")]
    response = NegativeCaseResponse(
        negative_cases=[],
        overall_assessment="No retrieved candidate was sufficient.",
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=response)
        asyncio.run(
            NegativeCaseStage().execute(
                state,
                PipelineContext(model_name="primary-model"),
            )
        )

    MockLLM.assert_called_once_with(model_name="primary-model")


def test_negative_case_passes_bm25_retrieval_config():
    state = _state_with_segments("Trust collapsed after the rollout.")
    state.claims = [_claim("claim-trust", "AI workflow trust across the corpus.")]
    response = NegativeCaseResponse(
        negative_cases=[],
        overall_assessment="No retrieved candidate was sufficient.",
    )

    with (
        patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM,
        patch(
            "qc_clean.core.pipeline.stages.negative_case.retrieve_disconfirmation_candidates",
            return_value=[],
        ) as mock_retrieve,
    ):
        MockLLM.return_value.extract_structured = AsyncMock(return_value=response)
        asyncio.run(
            NegativeCaseStage().execute(
                state,
                PipelineContext(
                    disconfirmation_candidates_per_claim=2,
                    disconfirmation_bm25_k1=1.7,
                    disconfirmation_bm25_b=0.55,
                    disconfirmation_contrary_cue_weight=2.25,
                ),
            )
        )

    assert mock_retrieve.call_args.kwargs["candidates_per_claim"] == 2
    assert mock_retrieve.call_args.kwargs["bm25_k1"] == 1.7
    assert mock_retrieve.call_args.kwargs["bm25_b"] == 0.55
    assert mock_retrieve.call_args.kwargs["contrary_cue_weight"] == 2.25


def test_negative_case_prompt_uses_adversarial_reviewer_stance():
    state = _state_with_segments("AI failed for this team after repeated errors.")
    state.claims = [_claim("claim-ai", "AI improves workflow across the corpus.")]
    captured_prompt = ""
    response = NegativeCaseResponse(
        negative_cases=[],
        overall_assessment="No retrieved candidate was sufficient.",
    )

    async def capture_prompt(prompt, *_args, **_kwargs):
        nonlocal captured_prompt
        captured_prompt = prompt
        return response

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(side_effect=capture_prompt)
        asyncio.run(NegativeCaseStage().execute(state, PipelineContext()))

    assert "adversarial qualitative methods reviewer" in captured_prompt
    assert "skeptical and evidence-bound" in captured_prompt
    assert "do not fabricate evidence" in captured_prompt
    assert "do not overstate weak candidates" in captured_prompt


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
