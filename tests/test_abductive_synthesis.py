"""Tests for opt-in abductive candidate explanation synthesis."""

from __future__ import annotations

import asyncio

import pytest

from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.pipeline_factory import create_pipeline
from qc_clean.core.pipeline.stages.abductive_synthesis import AbductiveSynthesisStage
from qc_clean.schemas.analysis_schemas import (
    AbductiveCandidateExplanationItem,
    AbductiveCandidateExplanationResponse,
)
from qc_clean.schemas.domain import (
    CausalInterpretationStatus,
    ObservedPattern,
    ObservedPatternKind,
    ProjectState,
)


class _FakeLLMHandler:
    """Deterministic replacement for the live LLM handler."""

    response = AbductiveCandidateExplanationResponse(
        candidates=[
            AbductiveCandidateExplanationItem(
                source_pattern_ids=["pattern-1"],
                explanation_text="Coordination friction may explain the repeated workflow pattern.",
                mechanism_summary="Extra coordination work changes how staff adopt the tool.",
                rival_explanations=["The pattern may reflect documentation differences."],
                observable_implications=["Teams with more handoffs should show stronger friction."],
                evidence_gaps=["Need direct process evidence about handoffs."],
                confidence=0.4,
            )
        ],
        analytical_memo="Candidate generation remained provisional.",
    )

    def __init__(self, model_name: str):
        self.model_name = model_name

    async def extract_structured(self, prompt, schema, **kwargs):
        return self.response


def _state_with_pattern() -> ProjectState:
    return ProjectState(
        id="abductive-test",
        name="Abductive Test",
        observed_patterns=[
            ObservedPattern(
                id="pattern-1",
                source_stage="cross_interview",
                pattern_kind=ObservedPatternKind.CONSENSUS_CODE,
                summary="Coordination appears across loaded documents.",
                code_ids=["C1"],
                doc_ids=["d1", "d2"],
                application_ids=["A1"],
                count=2,
                total=2,
            )
        ],
    )


def test_stage_creates_candidate_explanations_from_observed_patterns(monkeypatch):
    monkeypatch.setattr(
        "qc_clean.core.llm.llm_handler.LLMHandler",
        _FakeLLMHandler,
    )
    state = _state_with_pattern()
    stage = AbductiveSynthesisStage()

    updated = asyncio.run(stage.execute(state, PipelineContext(model_name="test-model")))

    assert len(updated.abductive_explanations) == 1
    candidate = updated.abductive_explanations[0]
    assert candidate.source_stage == "abductive_synthesis"
    assert candidate.source_pattern_ids == ["pattern-1"]
    assert "Coordination friction" in candidate.explanation_text
    assert candidate.rival_explanations
    assert candidate.observable_implications
    assert candidate.evidence_gaps
    assert candidate.status.value == "candidate"
    assert updated.memos[-1].memo_type == "methodological"
    assert "not causal proof" in updated.memos[-1].content


def test_stage_marks_patterns_candidate_explanation_generated(monkeypatch):
    monkeypatch.setattr(
        "qc_clean.core.llm.llm_handler.LLMHandler",
        _FakeLLMHandler,
    )
    state = _state_with_pattern()

    updated = asyncio.run(
        AbductiveSynthesisStage().execute(
            state,
            PipelineContext(model_name="test-model"),
        )
    )

    assert updated.observed_patterns[0].causal_interpretation_status == (
        CausalInterpretationStatus.CANDIDATE_EXPLANATION_GENERATED
    )


def test_stage_rejects_unknown_source_pattern_ids(monkeypatch):
    class BadLLMHandler(_FakeLLMHandler):
        response = AbductiveCandidateExplanationResponse(
            candidates=[
                AbductiveCandidateExplanationItem(
                    source_pattern_ids=["missing-pattern"],
                    explanation_text="Bad reference.",
                    mechanism_summary="Bad mechanism.",
                    rival_explanations=["Alternative."],
                    observable_implications=["Implication."],
                    evidence_gaps=["Gap."],
                    confidence=0.3,
                )
            ],
            analytical_memo="Bad memo.",
        )

    monkeypatch.setattr(
        "qc_clean.core.llm.llm_handler.LLMHandler",
        BadLLMHandler,
    )

    with pytest.raises(ValueError, match="unknown observed pattern IDs"):
        asyncio.run(
            AbductiveSynthesisStage().execute(
                _state_with_pattern(),
                PipelineContext(model_name="test-model"),
            )
        )


def test_stage_skips_without_observed_patterns(monkeypatch):
    monkeypatch.setattr(
        "qc_clean.core.llm.llm_handler.LLMHandler",
        _FakeLLMHandler,
    )
    state = ProjectState(id="empty", name="Empty")

    updated = asyncio.run(
        AbductiveSynthesisStage().execute(
            state,
            PipelineContext(model_name="test-model"),
        )
    )

    assert updated.abductive_explanations == []
    assert updated.memos == []


def test_pipeline_factory_abductive_opt_in_inserts_before_negative_case():
    default_names = [stage.name() for stage in create_pipeline().stages]
    abductive_names = [
        stage.name()
        for stage in create_pipeline(enable_abductive_synthesis=True).stages
    ]

    assert "abductive_synthesis" not in default_names
    assert "abductive_synthesis" in abductive_names
    assert abductive_names.index("cross_interview") < abductive_names.index(
        "abductive_synthesis"
    )
    assert abductive_names.index("abductive_synthesis") < abductive_names.index(
        "negative_case_analysis"
    )
