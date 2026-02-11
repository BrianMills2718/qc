"""
Tests for the unified domain model (qc_clean.schemas.domain).
Covers schema validation, defaults, and round-trip JSON serialization.
"""

import json
import pytest
from pydantic import ValidationError

from qc_clean.schemas.domain import (
    AnalysisMemo,
    AnalysisPhaseResult,
    Code,
    CodeApplication,
    Codebook,
    CodeRelationship,
    CoreCategoryResult,
    Corpus,
    Document,
    DomainEntityRelationship,
    Entity,
    HumanReviewDecision,
    Methodology,
    ParticipantPerspective,
    PerspectiveAnalysis,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
    Provenance,
    Recommendation,
    ReviewAction,
    Synthesis,
    TheoreticalModelResult,
)


# ---------------------------------------------------------------------------
# Document / Corpus
# ---------------------------------------------------------------------------


class TestDocument:
    def test_defaults(self):
        doc = Document(name="interview.docx")
        assert doc.name == "interview.docx"
        assert doc.content == ""
        assert doc.detected_speakers == []
        assert doc.is_truncated is False
        assert doc.id  # auto-generated uuid

    def test_with_content(self):
        doc = Document(
            name="test.txt",
            content="Hello world",
            detected_speakers=["Alice", "Bob"],
            is_truncated=True,
        )
        assert doc.content == "Hello world"
        assert len(doc.detected_speakers) == 2
        assert doc.is_truncated is True


class TestCorpus:
    def test_empty(self):
        corpus = Corpus()
        assert corpus.num_documents == 0

    def test_add_and_get(self):
        corpus = Corpus()
        doc = Document(id="d1", name="a.txt")
        corpus.add_document(doc)
        assert corpus.num_documents == 1
        assert corpus.get_document("d1") is doc
        assert corpus.get_document("missing") is None


# ---------------------------------------------------------------------------
# Code / Codebook
# ---------------------------------------------------------------------------


class TestCode:
    def test_defaults(self):
        code = Code(name="test_code")
        assert code.provenance == Provenance.LLM
        assert code.version == 1
        assert code.level == 0
        assert code.parent_id is None

    def test_full(self):
        code = Code(
            id="AI_USAGE",
            name="AI Usage",
            description="How AI is used.",
            definition="Any description of using AI tools.",
            parent_id=None,
            level=0,
            properties=["frequency"],
            dimensions=["formal-informal"],
            mention_count=5,
            confidence=0.8,
        )
        assert code.id == "AI_USAGE"
        assert code.mention_count == 5


class TestCodebook:
    def test_empty(self):
        cb = Codebook()
        assert cb.version == 1
        assert len(cb.codes) == 0

    def test_lookup(self):
        c1 = Code(id="C1", name="Theme A")
        c2 = Code(id="C2", name="Theme B", parent_id="C1", level=1)
        cb = Codebook(codes=[c1, c2])

        assert cb.get_code("C1") is c1
        assert cb.get_code("missing") is None
        assert cb.get_code_by_name("Theme B") is c2
        assert len(cb.top_level_codes()) == 1
        assert len(cb.children_of("C1")) == 1


# ---------------------------------------------------------------------------
# CodeApplication / CodeRelationship
# ---------------------------------------------------------------------------


class TestCodeApplication:
    def test_defaults(self):
        app = CodeApplication(code_id="C1", doc_id="D1", quote_text="some text")
        assert app.applied_by == Provenance.LLM
        assert app.codebook_version == 1
        assert app.confidence == 0.0


class TestCodeRelationship:
    def test_defaults(self):
        rel = CodeRelationship(source_code_id="C1", target_code_id="C2")
        assert rel.relationship_type == "related_to"
        assert rel.strength == 0.0


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------


class TestEntity:
    def test_defaults(self):
        ent = Entity(name="AI")
        assert ent.entity_type == "concept"

    def test_relationship(self):
        rel = DomainEntityRelationship(
            entity_1_id="e1", entity_2_id="e2", relationship_type="uses"
        )
        assert rel.strength == 0.0


# ---------------------------------------------------------------------------
# Analysis artifacts
# ---------------------------------------------------------------------------


class TestAnalysisMemo:
    def test_defaults(self):
        memo = AnalysisMemo()
        assert memo.memo_type == "theoretical"
        assert memo.created_by == Provenance.LLM


class TestHumanReviewDecision:
    def test_create(self):
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C1",
            action=ReviewAction.APPROVE,
            rationale="Looks good",
        )
        assert decision.action == ReviewAction.APPROVE


class TestAnalysisPhaseResult:
    def test_defaults(self):
        pr = AnalysisPhaseResult(phase_name="ingest")
        assert pr.status == PipelineStatus.PENDING
        assert pr.error_message is None


# ---------------------------------------------------------------------------
# Perspective / Synthesis / GT
# ---------------------------------------------------------------------------


class TestPerspectiveAnalysis:
    def test_basic(self):
        pa = PerspectiveAnalysis(
            participants=[ParticipantPerspective(name="Alice")],
            consensus_themes=["theme1"],
        )
        assert len(pa.participants) == 1


class TestSynthesis:
    def test_basic(self):
        s = Synthesis(
            executive_summary="summary",
            recommendations=[Recommendation(title="Do X")],
        )
        assert len(s.recommendations) == 1


class TestGroundedTheoryModels:
    def test_core_category(self):
        cc = CoreCategoryResult(category_name="Adaptation")
        assert cc.category_name == "Adaptation"

    def test_theoretical_model(self):
        tm = TheoreticalModelResult(model_name="Theory of X")
        assert tm.model_name == "Theory of X"


# ---------------------------------------------------------------------------
# ProjectState
# ---------------------------------------------------------------------------


class TestProjectState:
    def test_defaults(self):
        state = ProjectState()
        assert state.name == "Untitled Project"
        assert state.pipeline_status == PipelineStatus.PENDING
        assert state.iteration == 1
        assert state.corpus.num_documents == 0
        assert state.codebook.version == 1

    def test_touch(self):
        state = ProjectState()
        old = state.updated_at
        import time
        time.sleep(0.01)
        state.touch()
        assert state.updated_at >= old

    def test_phase_results(self):
        state = ProjectState()
        pr = AnalysisPhaseResult(phase_name="ingest", status=PipelineStatus.COMPLETED)
        state.add_phase_result(pr)
        assert state.get_phase_result("ingest") is pr

        # Update existing
        pr2 = AnalysisPhaseResult(phase_name="ingest", status=PipelineStatus.FAILED)
        state.add_phase_result(pr2)
        assert state.get_phase_result("ingest").status == PipelineStatus.FAILED
        assert len(state.phase_results) == 1  # replaced, not duplicated

    def test_json_round_trip(self):
        """Serialize to JSON and back -- all data preserved."""
        doc = Document(id="d1", name="test.txt", content="hello")
        code = Code(id="C1", name="Theme", mention_count=3, confidence=0.7)
        app = CodeApplication(code_id="C1", doc_id="d1", quote_text="hello")

        state = ProjectState(
            name="Test Project",
            corpus=Corpus(documents=[doc]),
            codebook=Codebook(codes=[code]),
            code_applications=[app],
            data_warnings=["truncated"],
        )

        json_str = state.model_dump_json(indent=2)
        loaded = ProjectState.model_validate_json(json_str)

        assert loaded.name == "Test Project"
        assert loaded.corpus.num_documents == 1
        assert loaded.corpus.documents[0].id == "d1"
        assert len(loaded.codebook.codes) == 1
        assert loaded.codebook.codes[0].id == "C1"
        assert len(loaded.code_applications) == 1
        assert loaded.data_warnings == ["truncated"]

    def test_full_round_trip_with_all_sections(self):
        """Round-trip with every section populated."""
        state = ProjectState(
            name="Full",
            config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
            corpus=Corpus(documents=[Document(id="d1", name="a.txt")]),
            codebook=Codebook(codes=[Code(id="C1", name="A")]),
            code_applications=[
                CodeApplication(code_id="C1", doc_id="d1", quote_text="q")
            ],
            code_relationships=[
                CodeRelationship(source_code_id="C1", target_code_id="C1")
            ],
            entities=[Entity(name="Org")],
            entity_relationships=[
                DomainEntityRelationship(
                    entity_1_id="e1", entity_2_id="e2", relationship_type="uses"
                )
            ],
            perspective_analysis=PerspectiveAnalysis(
                participants=[ParticipantPerspective(name="Bob")],
            ),
            synthesis=Synthesis(executive_summary="ok"),
            core_categories=[CoreCategoryResult(category_name="CC")],
            theoretical_model=TheoreticalModelResult(model_name="TM"),
            memos=[AnalysisMemo(title="memo1")],
            review_decisions=[
                HumanReviewDecision(
                    target_type="code",
                    target_id="C1",
                    action=ReviewAction.APPROVE,
                )
            ],
            phase_results=[
                AnalysisPhaseResult(
                    phase_name="ingest", status=PipelineStatus.COMPLETED
                )
            ],
        )

        json_str = state.model_dump_json()
        loaded = ProjectState.model_validate_json(json_str)

        assert loaded.config.methodology == Methodology.GROUNDED_THEORY
        assert loaded.perspective_analysis.participants[0].name == "Bob"
        assert loaded.synthesis.executive_summary == "ok"
        assert loaded.core_categories[0].category_name == "CC"
        assert loaded.theoretical_model.model_name == "TM"
        assert len(loaded.memos) == 1
        assert len(loaded.review_decisions) == 1
        assert loaded.phase_results[0].status == PipelineStatus.COMPLETED
