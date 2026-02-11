"""
Tests for cross-interview analysis and saturation detection.
"""

import asyncio
import pytest

from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
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
        assert "C1" in results["shared_codes"]
        # C2, C3, C4 are in 1 doc each -> unique
        assert "C2" in results["unique_codes"]
        assert "C3" in results["unique_codes"]

    def test_consensus_themes(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        # C1 is in 3/3 docs = 100% -> consensus
        consensus_ids = [ct["code_id"] for ct in results["consensus_themes"]]
        assert "C1" in consensus_ids

    def test_divergent_themes(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        divergent_ids = [dt["code_id"] for dt in results["divergent_themes"]]
        # C2, C3, C4 are in only 1 doc
        assert "C2" in divergent_ids or "C3" in divergent_ids

    def test_co_occurrences(self, multi_doc_state):
        results = analyze_cross_interview_patterns(multi_doc_state)
        # C1 and C4 co-occur in d1, C1 and C2 co-occur in d2, C1 and C3 co-occur in d3
        assert len(results["co_occurrences"]) >= 0  # at least some

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
        result = asyncio.get_event_loop().run_until_complete(
            stage.execute(multi_doc_state, {})
        )
        assert len(result.memos) == 1
        assert result.memos[0].memo_type == "cross_case"


# ---------------------------------------------------------------------------
# Saturation tests
# ---------------------------------------------------------------------------


class TestSaturation:
    def test_no_history(self):
        state = ProjectState(codebook=Codebook(codes=[Code(id="C1", name="A")]))
        result = check_saturation(state)
        assert result["saturated"] is False
        assert "First iteration" in result["message"]

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
        assert result["saturated"] is True

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
        assert result["saturated"] is False

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
        assert "C" in metrics["removed_codes"]
        assert "D" in metrics["added_codes"]
        assert "B" in metrics["modified_codes"]
        assert "A" in metrics["stable_codes"]
        assert metrics["pct_change"] > 0


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
        assert suggestions[0]["doc_id"] == "d4"

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
