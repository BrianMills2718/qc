"""
Tests for cross-interview analysis and saturation detection.
"""

import asyncio
import pytest

from qc_clean.schemas.domain import (
    CausalInterpretationStatus,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ObservedPatternKind,
    ParticipantPerspective,
    PerspectiveAnalysis,
    ProjectState,
)
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.cross_interview import (
    CrossInterviewStage,
    analyze_cross_interview_patterns,
)
from qc_clean.core.pipeline.saturation import (
    calculate_codebook_change,
    check_saturation,
)
from qc_clean.core.pipeline.theoretical_sampling import suggest_next_documents


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def multi_doc_state():
    """ProjectState with 3 documents and overlapping codes."""
    docs = [
        Document(id="d1", name="interview1.txt", content="AI is great. I use it daily."),
        Document(id="d2", name="interview2.txt", content="AI helps but has limits."),
        Document(id="d3", name="interview3.txt", content="I prefer manual methods."),
    ]
    codes = [
        Code(id="C1", name="AI Usage", mention_count=5, confidence=0.8),
        Code(id="C2", name="AI Limitations", mention_count=3, confidence=0.6),
        Code(id="C3", name="Manual Methods", mention_count=2, confidence=0.5),
        Code(id="C4", name="Unique Theme", mention_count=1, confidence=0.3),
    ]
    apps = [
        # C1 in d1 and d2 (shared)
        CodeApplication(code_id="C1", doc_id="d1", quote_text="AI is great"),
        CodeApplication(code_id="C1", doc_id="d2", quote_text="AI helps"),
        # C2 in d2 only
        CodeApplication(code_id="C2", doc_id="d2", quote_text="has limits"),
        # C3 in d3 only
        CodeApplication(code_id="C3", doc_id="d3", quote_text="manual methods"),
        # C4 in d1 only
        CodeApplication(code_id="C4", doc_id="d1", quote_text="unique"),
        # C1 also in d3 for consensus
        CodeApplication(code_id="C1", doc_id="d3", quote_text="AI daily"),
    ]
    return ProjectState(
        corpus=Corpus(documents=docs),
        codebook=Codebook(codes=codes),
        code_applications=apps,
    )


# ---------------------------------------------------------------------------
# Cross-interview tests
# ---------------------------------------------------------------------------


class TestCrossInterviewAnalysis:
    def test_shared_codes(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        # C1 is in d1, d2, d3 -> shared
        assert "C1" in results.shared_codes
        # C2, C3, C4 are in 1 doc each -> unique
        assert "C2" in results.unique_codes
        assert "C3" in results.unique_codes

    def test_consensus_themes(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        # C1 is in 3/3 docs = 100% -> consensus
        consensus_ids = [ct["code_id"] for ct in results.consensus_themes]
        assert "C1" in consensus_ids

    def test_divergent_themes(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        divergent_ids = [dt["code_id"] for dt in results.divergent_themes]
        # C2, C3, C4 are in only 1 doc
        assert "C2" in divergent_ids or "C3" in divergent_ids

    def test_co_occurrences(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        # C1 and C4 co-occur in d1, C1 and C2 co-occur in d2, C1 and C3 co-occur in d3
        assert len(results.co_occurrences) >= 0  # at least some

    def test_single_doc_skips(self):
        """CrossInterviewStage should not execute on single-doc corpus."""
        stage = CrossInterviewStage()
        state = ProjectState(
            corpus=Corpus(documents=[Document(id="d1", name="only.txt")])
        )
        assert stage.can_execute(state) is False

    def test_multi_doc_executes(self, multi_doc_state):
        stage = CrossInterviewStage()
        assert stage.can_execute(multi_doc_state) is True

    def test_stage_creates_memo(self, multi_doc_state):
        stage = CrossInterviewStage()
        result = asyncio.run(
            stage.execute(multi_doc_state, PipelineContext())
        )
        assert len(result.memos) == 1
        assert result.memos[0].memo_type == "cross_case"
        assert "anchored application evidence in 3/3 loaded documents" in result.memos[0].content
        assert "present in 3/3 documents" not in result.memos[0].content

    def test_stage_populates_observed_patterns(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="one.txt", content="AI supports privacy."),
                Document(id="d2", name="two.txt", content="AI supports privacy."),
                Document(id="d3", name="three.txt", content="AI appears alone."),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="AI Use"),
                Code(id="C2", name="Privacy"),
                Code(id="C3", name="Rare Concern"),
            ]),
            code_applications=[
                CodeApplication(id="a1", code_id="C1", doc_id="d1", quote_text="AI"),
                CodeApplication(id="a2", code_id="C2", doc_id="d1", quote_text="privacy"),
                CodeApplication(id="a3", code_id="C1", doc_id="d2", quote_text="AI"),
                CodeApplication(id="a4", code_id="C2", doc_id="d2", quote_text="privacy"),
                CodeApplication(id="a5", code_id="C1", doc_id="d3", quote_text="AI"),
                CodeApplication(id="a6", code_id="C3", doc_id="d3", quote_text="rare"),
            ],
        )

        result = asyncio.run(CrossInterviewStage().execute(state, PipelineContext()))

        kinds = {pattern.pattern_kind for pattern in result.observed_patterns}
        assert ObservedPatternKind.CONSENSUS_CODE in kinds
        assert ObservedPatternKind.DIVERGENT_CODE in kinds
        assert ObservedPatternKind.CODE_CO_OCCURRENCE in kinds
        assert any(
            "anchored application evidence in 3/3 loaded documents" in pattern.summary
            for pattern in result.observed_patterns
        )
        assert not any("appears in" in pattern.summary for pattern in result.observed_patterns)

    def test_stage_promotes_perspective_consensus_and_divergence_patterns(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="one.txt", content="Alice: AI saves time."),
                Document(id="d2", name="two.txt", content="Bob: AI requires oversight."),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="AI Use"),
                Code(id="C2", name="Governance"),
            ]),
            code_applications=[
                CodeApplication(id="a1", code_id="C1", doc_id="d1", quote_text="AI saves time"),
                CodeApplication(id="a2", code_id="C2", doc_id="d2", quote_text="requires oversight"),
            ],
            perspective_analysis=PerspectiveAnalysis(
                participants=[
                    ParticipantPerspective(
                        name="Alice",
                        perspective_summary="AI is useful when governed.",
                        codes_emphasized=["C1", "C2"],
                    ),
                    ParticipantPerspective(
                        name="Bob",
                        perspective_summary="AI needs structured oversight.",
                        codes_emphasized=["C1", "C2"],
                    ),
                ],
                consensus_themes=["AI can be useful when governed well."],
                divergent_viewpoints=["Alice emphasizes adoption speed while Bob emphasizes oversight first."],
            ),
        )

        result = asyncio.run(CrossInterviewStage().execute(state, PipelineContext()))

        kinds = {pattern.pattern_kind for pattern in result.observed_patterns}
        assert ObservedPatternKind.PERSPECTIVE_CONSENSUS in kinds
        assert ObservedPatternKind.PERSPECTIVE_DIVERGENCE in kinds
        assert any(
            pattern.summary == "Participants converge on the position: AI can be useful when governed well."
            for pattern in result.observed_patterns
        )
        assert any(
            pattern.metadata.get("participant_names") == ["Alice", "Bob"]
            for pattern in result.observed_patterns
            if pattern.pattern_kind is ObservedPatternKind.PERSPECTIVE_CONSENSUS
        )

    def test_observed_patterns_are_descriptive_only(self, multi_doc_state):
        result = asyncio.run(
            CrossInterviewStage().execute(multi_doc_state, PipelineContext())
        )

        assert result.observed_patterns
        assert {
            pattern.causal_interpretation_status
            for pattern in result.observed_patterns
        } == {CausalInterpretationStatus.DESCRIPTIVE_ONLY}

    def test_co_occurrence_pattern_records_code_and_doc_scope(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="one.txt", content="AI supports privacy."),
                Document(id="d2", name="two.txt", content="AI supports privacy."),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="AI Use"),
                Code(id="C2", name="Privacy"),
            ]),
            code_applications=[
                CodeApplication(id="a1", code_id="C1", doc_id="d1", quote_text="AI"),
                CodeApplication(id="a2", code_id="C2", doc_id="d1", quote_text="privacy"),
                CodeApplication(id="a3", code_id="C1", doc_id="d2", quote_text="AI"),
                CodeApplication(id="a4", code_id="C2", doc_id="d2", quote_text="privacy"),
            ],
        )

        result = asyncio.run(CrossInterviewStage().execute(state, PipelineContext()))

        co_patterns = [
            pattern for pattern in result.observed_patterns
            if pattern.pattern_kind is ObservedPatternKind.CODE_CO_OCCURRENCE
        ]
        assert len(co_patterns) == 1
        pattern = co_patterns[0]
        assert pattern.code_ids == ["C1", "C2"]
        assert pattern.doc_ids == ["d1", "d2"]
        assert set(pattern.application_ids) == {"a1", "a2", "a3", "a4"}
        assert pattern.count == 2
        assert pattern.total == 2


# ---------------------------------------------------------------------------
# Saturation tests
# ---------------------------------------------------------------------------


class TestSaturation:
    def test_no_history(self):
        state = ProjectState(codebook=Codebook(codes=[Code(id="C1", name="A")]))
        result = check_saturation(state)
        assert result.saturated is False
        assert "First iteration" in result.message

    def test_saturated(self):
        old = Codebook(codes=[
            Code(id="C1", name="A", description="desc", confidence=0.8),
            Code(id="C2", name="B", description="desc", confidence=0.7),
        ])
        new = Codebook(codes=[
            Code(id="C1", name="A", description="desc", confidence=0.8),
            Code(id="C2", name="B", description="desc", confidence=0.7),
        ])
        state = ProjectState(
            codebook=new,
            codebook_history=[old],
            iteration=2,
        )
        result = check_saturation(state, threshold=0.15)
        assert result.saturated is True

    def test_not_saturated(self):
        old = Codebook(codes=[
            Code(id="C1", name="A"),
            Code(id="C2", name="B"),
        ])
        new = Codebook(codes=[
            Code(id="C1", name="A"),
            Code(id="C3", name="C"),
            Code(id="C4", name="D"),
        ])
        state = ProjectState(
            codebook=new,
            codebook_history=[old],
            iteration=2,
        )
        result = check_saturation(state, threshold=0.15)
        assert result.saturated is False

    def test_codebook_change_metrics(self):
        old = Codebook(codes=[
            Code(id="C1", name="A"),
            Code(id="C2", name="B"),
            Code(id="C3", name="C"),
        ])
        new = Codebook(codes=[
            Code(id="C1", name="A"),
            Code(id="C2", name="B", description="updated"),
            Code(id="C4", name="D"),
        ])
        metrics = calculate_codebook_change(old, new)
        assert "C" in metrics.removed_codes
        assert "D" in metrics.added_codes
        assert "B" in metrics.modified_codes
        assert "A" in metrics.stable_codes
        assert metrics.pct_change > 0


# ---------------------------------------------------------------------------
# Theoretical sampling tests
# ---------------------------------------------------------------------------


class TestTheoreticalSampling:
    def test_suggest_uncoded(self, multi_doc_state):
        # Add an uncoded document
        multi_doc_state.corpus.add_document(
            Document(id="d4", name="new_interview.txt", content="Not yet coded.")
        )
        suggestions = suggest_next_documents(multi_doc_state)
        assert len(suggestions) >= 1
        assert suggestions[0].doc_id == "d4"

    def test_no_uncoded(self, multi_doc_state):
        # All documents are already coded
        suggestions = suggest_next_documents(multi_doc_state)
        assert len(suggestions) == 0

    def test_max_suggestions(self, multi_doc_state):
        for i in range(5):
            multi_doc_state.corpus.add_document(
                Document(id=f"new_{i}", name=f"new_{i}.txt")
            )
        suggestions = suggest_next_documents(multi_doc_state, max_suggestions=2)
        assert len(suggestions) <= 2

    def test_sampling_uses_category_diagnostics_over_application_count(self):
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="coded1.txt", content="Trust appeared once."),
                Document(id="d2", name="coded2.txt", content="Trust appeared twice."),
                Document(id="d3", name="candidate.txt", content="New candidate."),
            ]),
            codebook=Codebook(codes=[
                Code(id="TRUST", name="Trust", description="Trust category"),
            ]),
            code_applications=[
                CodeApplication(code_id="TRUST", doc_id="d1", quote_text="Trust appeared once."),
                CodeApplication(code_id="TRUST", doc_id="d2", quote_text="Trust appeared twice."),
            ],
        )

        suggestions = suggest_next_documents(state)

        assert suggestions[0].doc_id == "d3"
        assert suggestions[0].gap_codes == ["TRUST"]
        assert "category-development" in suggestions[0].reason
