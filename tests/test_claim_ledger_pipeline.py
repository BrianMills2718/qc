"""Pipeline-stage wiring tests for the INV-9 claim ledger."""

import asyncio
from unittest.mock import AsyncMock, patch

from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.cross_interview import CrossInterviewStage
from qc_clean.core.pipeline.stages.negative_case import (
    NegativeCase,
    NegativeCaseResponse,
    NegativeCaseStage,
)
from qc_clean.schemas.analysis_schemas import (
    AnalysisRecommendation,
    AnalysisSynthesis,
    CodeHierarchy,
    EntityMapping,
    EntityRelationship,
    ParticipantProfile,
    PerspectiveMapEntry,
    SpeakerAnalysis,
    ThematicCode,
    ThemeConfidence,
)
from qc_clean.schemas.domain import (
    ClaimKind,
    ClaimSupportStatus,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)


def _state() -> ProjectState:
    return ProjectState(
        corpus=Corpus(documents=[
            Document(
                id="d1",
                name="interview.txt",
                content="Jane: We use AI for everything now. It changed our workflow completely.",
                detected_speakers=["Jane"],
            )
        ])
    )


def _code_response() -> CodeHierarchy:
    return CodeHierarchy(
        codes=[
            ThematicCode(
                id="AI_USE",
                name="AI Use",
                description="Using AI tools at work",
                semantic_definition="References to using AI",
                level=0,
                example_quotes=["We use AI for everything now"],
                mention_count=1,
                discovery_confidence=0.8,
            )
        ],
        total_codes=1,
        analysis_confidence=0.8,
    )


def test_thematic_stage_emits_code_and_application_claims_without_duplicates():
    from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

    state = _state()
    ctx = PipelineContext()

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        instance = MockLLM.return_value
        instance.extract_structured = AsyncMock(return_value=_code_response())
        result = asyncio.run(ThematicCodingStage().execute(state, ctx))
        result = asyncio.run(ThematicCodingStage().execute(result, ctx))

    assert [claim.source_stage for claim in result.claims] == [
        "thematic_coding",
        "thematic_coding",
    ]
    assert {claim.claim_kind for claim in result.claims} == {
        ClaimKind.CODE,
        ClaimKind.CODE_APPLICATION,
    }
    assert all(claim.support_status == ClaimSupportStatus.SUPPORTED for claim in result.claims)


def test_perspective_stage_emits_perspective_claims():
    from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

    state = _state()
    ctx = PipelineContext(phase1_json="{}")
    response = SpeakerAnalysis(
        participants=[
            ParticipantProfile(
                name="Jane",
                role="Manager",
                perspective_summary="Jane sees AI as transformative.",
                codes_emphasized=["AI_USE"],
            )
        ],
        consensus_themes=["AI is useful"],
        divergent_viewpoints=[],
        perspective_mapping=[PerspectiveMapEntry(participant_name="Jane", code_ids=["AI_USE"])],
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        instance = MockLLM.return_value
        instance.extract_structured = AsyncMock(return_value=response)
        result = asyncio.run(PerspectiveStage().execute(state, ctx))

    assert result.claims
    assert {claim.claim_kind for claim in result.claims} == {ClaimKind.PERSPECTIVE}
    assert any(claim.scope.participant_names == ["Jane"] for claim in result.claims)


def test_relationship_stage_emits_relationship_claims():
    from qc_clean.core.pipeline.stages.relationship import RelationshipStage

    state = _state()
    ctx = PipelineContext(phase1_json="{}", phase2_json="{}")
    response = EntityMapping(
        entities=["AI", "Workflow"],
        relationships=[
            EntityRelationship(
                entity_1="AI",
                entity_2="Workflow",
                relationship_type="changes",
                strength=0.8,
                supporting_evidence=["It changed our workflow completely"],
            )
        ],
        cause_effect_chains=["AI use -> workflow change"],
        conceptual_connections=[],
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        instance = MockLLM.return_value
        instance.extract_structured = AsyncMock(return_value=response)
        result = asyncio.run(RelationshipStage().execute(state, ctx))

    relationship_claims = [c for c in result.claims if c.source_stage == "relationship"]
    assert relationship_claims
    assert all(claim.claim_kind == ClaimKind.RELATIONSHIP for claim in relationship_claims)


def test_synthesis_stage_emits_synthesis_claims():
    from qc_clean.core.pipeline.stages.synthesis import SynthesisStage

    state = _state()
    state.codebook = Codebook(codes=[Code(id="AI_USE", name="AI Use")])
    ctx = PipelineContext(phase1_json="{}", phase2_json="{}", phase3_json="{}")
    response = AnalysisSynthesis(
        executive_summary="AI changes workflow.",
        key_findings=["AI changes workflow."],
        cross_cutting_patterns=["Technology drives work redesign."],
        actionable_recommendations=[
            AnalysisRecommendation(
                title="Train staff",
                description="Train staff on AI tools.",
                priority="high",
                supporting_themes=["AI_USE"],
            )
        ],
        confidence_assessment=[ThemeConfidence(theme="AI_USE", level="high", score=0.8)],
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        instance = MockLLM.return_value
        instance.extract_structured = AsyncMock(return_value=response)
        result = asyncio.run(SynthesisStage().execute(state, ctx))

    assert result.claims
    assert {claim.claim_kind for claim in result.claims} == {ClaimKind.SYNTHESIS_FINDING}
    assert any(claim.scope.code_ids == ["AI_USE"] for claim in result.claims)


def test_cross_interview_stage_emits_supported_cross_case_claims():
    docs = [
        Document(id="d1", name="a.txt", content="AI helps."),
        Document(id="d2", name="b.txt", content="AI helps again."),
    ]
    state = ProjectState(
        corpus=Corpus(documents=docs),
        codebook=Codebook(codes=[Code(id="AI_USE", name="AI Use")]),
        code_applications=[
            CodeApplication(
                id="a1", code_id="AI_USE", doc_id="d1", quote_text="AI helps",
                start_char=0, end_char=8, quote_hash="h1",
            ),
            CodeApplication(
                id="a2", code_id="AI_USE", doc_id="d2", quote_text="AI helps again",
                start_char=0, end_char=14, quote_hash="h2",
            ),
        ],
    )

    result = asyncio.run(CrossInterviewStage().execute(state, PipelineContext()))

    assert result.claims
    assert {claim.claim_kind for claim in result.claims} == {ClaimKind.CROSS_CASE}
    assert any(claim.support_status == ClaimSupportStatus.SUPPORTED for claim in result.claims)


def test_negative_case_stage_emits_negative_case_claims():
    state = ProjectState(
        corpus=Corpus(documents=[
            Document(id="d1", name="d.txt", content="Jane: We abandoned AI after errors.")
        ]),
        codebook=Codebook(codes=[Code(id="AI_USE", name="AI Use")]),
    )
    response = NegativeCaseResponse(
        negative_cases=[
            NegativeCase(
                code_name="AI Use",
                disconfirming_evidence="abandoned AI after errors",
                explanation="This challenges a simple adoption narrative.",
                implication="AI use has failure cases.",
            )
        ],
        overall_assessment="One negative case found.",
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        instance = MockLLM.return_value
        instance.extract_structured = AsyncMock(return_value=response)
        result = asyncio.run(NegativeCaseStage().execute(state, PipelineContext()))

    assert result.claims
    claim = result.claims[0]
    assert claim.claim_kind == ClaimKind.NEGATIVE_CASE
    assert claim.scope.code_ids == ["AI_USE"]
    assert claim.contrary_anchors
