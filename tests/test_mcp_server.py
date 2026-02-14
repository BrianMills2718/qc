"""
Tests for the QC MCP server (qc_mcp_server.py).

Tests all 18 tools: 11 existing + 7 new. Uses tmp_path for isolated
ProjectStore and mocks LLMHandler for pipeline-calling tools.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import (
    AnalysisMemo,
    AnalysisPhaseResult,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    Entity,
    IRRResult,
    Methodology,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
    Provenance,
    Recommendation,
    StabilityResult,
    Synthesis,
)

import qc_mcp_server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_store(tmp_path: Path):
    """Replace global store with one backed by tmp_path."""
    original = qc_mcp_server.store
    qc_mcp_server.store = ProjectStore(projects_dir=tmp_path)
    yield qc_mcp_server.store
    qc_mcp_server.store = original


@pytest.fixture
def sample_project(tmp_store) -> ProjectState:
    """Create and save a minimal project."""
    state = ProjectState(
        id="proj-1",
        name="Test Study",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
    )
    tmp_store.save(state)
    return state


@pytest.fixture
def project_with_docs(tmp_store) -> ProjectState:
    """Project with documents loaded."""
    state = ProjectState(
        id="proj-docs",
        name="Doc Study",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(id="d1", name="interview1.txt", content="Alice: We use AI daily."),
            Document(id="d2", name="interview2.txt", content="Bob: AI adoption was slow."),
        ]),
    )
    tmp_store.save(state)
    return state


@pytest.fixture
def completed_project(tmp_store) -> ProjectState:
    """Project with codebook, applications, memos, synthesis, and phase results."""
    codes = [
        Code(id="C1", name="AI Adoption", description="Use of AI", mention_count=5, confidence=0.9),
        Code(id="C2", name="Privacy Concerns", description="Data privacy", mention_count=3, confidence=0.7),
    ]
    apps = [
        CodeApplication(id="A1", code_id="C1", doc_id="d1", quote_text="We use AI daily.", confidence=0.85),
        CodeApplication(id="A2", code_id="C2", doc_id="d2", quote_text="AI adoption was slow.", confidence=0.75),
    ]
    memos = [
        AnalysisMemo(id="M1", memo_type="theoretical", title="AI Theme", content="AI is dominant."),
    ]
    state = ProjectState(
        id="proj-done",
        name="Completed Study",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(id="d1", name="interview1.txt", content="Alice: We use AI daily."),
            Document(id="d2", name="interview2.txt", content="Bob: AI adoption was slow."),
        ]),
        codebook=Codebook(codes=codes),
        code_applications=apps,
        memos=memos,
        entities=[Entity(id="E1", name="AI", entity_type="concept")],
        synthesis=Synthesis(
            executive_summary="AI is widely adopted.",
            key_findings=["AI adoption is increasing", "Privacy is a concern"],
            recommendations=[Recommendation(title="Invest in AI", priority="high")],
        ),
        pipeline_status=PipelineStatus.COMPLETED,
        phase_results=[
            AnalysisPhaseResult(phase_name="Ingest", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="Thematic Coding", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="Synthesis", status=PipelineStatus.COMPLETED),
        ],
    )
    tmp_store.save(state)
    return state


# ---------------------------------------------------------------------------
# Project management
# ---------------------------------------------------------------------------

class TestProjectManagement:
    def test_create_project(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_create_project("My Study", "grounded_theory"))
        assert result["name"] == "My Study"
        assert result["methodology"] == "grounded_theory"
        assert "project_id" in result

    def test_create_project_invalid_methodology(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_create_project("Bad", "invalid"))
        assert "error" in result

    def test_list_projects_empty(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_list_projects())
        assert "message" in result

    def test_list_projects(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_list_projects())
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["name"] == "Test Study"

    def test_show_project(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_show_project("proj-1"))
        assert result["name"] == "Test Study"
        assert result["methodology"] == "thematic_analysis"
        assert result["documents"] == 0

    def test_show_project_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_show_project("nonexistent"))
        assert "error" in result

    def test_show_project_includes_phase_results(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_show_project("proj-done"))
        assert "phase_results" in result
        assert len(result["phase_results"]) == 3
        assert result["phase_results"][0]["phase"] == "Ingest"
        assert result["phase_results"][0]["status"] == "completed"

    def test_delete_project(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_delete_project("proj-1"))
        assert "message" in result
        # Verify gone
        result2 = json.loads(qc_mcp_server.qc_show_project("proj-1"))
        assert "error" in result2

    def test_delete_project_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_delete_project("nonexistent"))
        assert "error" in result


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------

class TestDocumentManagement:
    def test_add_documents(self, sample_project, tmp_store):
        docs = [
            {"name": "interview1.txt", "content": "Alice: Hello"},
            {"name": "interview2.txt", "content": "Bob: Hi"},
        ]
        result = json.loads(qc_mcp_server.qc_add_documents("proj-1", docs))
        assert result["added"] == 2
        assert result["total_documents"] == 2

    def test_add_documents_missing_project(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_add_documents("nope", [{"name": "a", "content": "b"}]))
        assert "error" in result

    def test_add_documents_empty_list(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_add_documents("proj-1", []))
        assert "error" in result

    def test_add_documents_missing_name(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_add_documents("proj-1", [{"content": "text"}]))
        assert "error" in result


# ---------------------------------------------------------------------------
# Codebook / inspection
# ---------------------------------------------------------------------------

class TestInspection:
    def test_get_codebook(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_codebook("proj-done"))
        assert result["code_count"] == 2
        assert result["codes"][0]["name"] == "AI Adoption"

    def test_get_codebook_empty(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_codebook("proj-1"))
        assert result["code_count"] == 0

    def test_get_codebook_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_codebook("nope"))
        assert "error" in result

    def test_get_applications(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_applications("proj-done"))
        assert result["total_applications"] == 2
        assert result["returned"] == 2

    def test_get_applications_filtered(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_applications("proj-done", code_name="Privacy"))
        assert result["returned"] == 1
        assert result["applications"][0]["code"] == "Privacy Concerns"

    def test_get_memos(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_memos("proj-done"))
        assert result["memo_count"] == 1
        assert result["memos"][0]["title"] == "AI Theme"

    def test_get_synthesis(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_synthesis("proj-done"))
        assert "AI is widely adopted" in result["executive_summary"]
        assert len(result["key_findings"]) == 2
        assert result["recommendations"][0]["title"] == "Invest in AI"

    def test_get_synthesis_empty(self, sample_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_get_synthesis("proj-1"))
        assert "message" in result


# ---------------------------------------------------------------------------
# Pipeline execution (mocked LLM)
# ---------------------------------------------------------------------------

def _mock_pipeline_run(final_status=PipelineStatus.COMPLETED):
    """Create a side_effect function that simulates pipeline.run()."""
    async def _run(state, ctx, resume_from=None):
        state.pipeline_status = final_status
        state.codebook.codes = [
            Code(id="MC1", name="Mock Theme", mention_count=2, confidence=0.8),
        ]
        state.code_applications = [
            CodeApplication(code_id="MC1", doc_id="d1", quote_text="mock quote"),
        ]
        state.phase_results = [
            AnalysisPhaseResult(phase_name="Ingest", status=PipelineStatus.COMPLETED),
            AnalysisPhaseResult(phase_name="Thematic Coding", status=PipelineStatus.COMPLETED),
        ]
        return state
    return _run


class TestPipelineExecution:
    @pytest.mark.asyncio
    async def test_run_pipeline_no_docs(self, sample_project, tmp_store):
        result = json.loads(await qc_mcp_server.qc_run_pipeline("proj-1"))
        assert "error" in result
        assert "no documents" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_pipeline_not_found(self, tmp_store):
        result = json.loads(await qc_mcp_server.qc_run_pipeline("nope"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_pipeline(self, project_with_docs, tmp_store):
        with patch("qc_mcp_server.create_pipeline") as mock_factory:
            mock_pipeline = MagicMock()
            mock_pipeline.run = AsyncMock(side_effect=_mock_pipeline_run())
            mock_factory.return_value = mock_pipeline

            result = json.loads(await qc_mcp_server.qc_run_pipeline("proj-docs"))
            assert result["status"] == "completed"
            assert result["codes"] == 1
            assert result["code_applications"] == 1
            assert len(result["phase_results"]) == 2

    @pytest.mark.asyncio
    async def test_run_pipeline_resume(self, project_with_docs, tmp_store):
        # Set up paused state
        state = tmp_store.load("proj-docs")
        state.pipeline_status = PipelineStatus.PAUSED_FOR_REVIEW
        state.current_phase = "Thematic Coding"
        tmp_store.save(state)

        with patch("qc_mcp_server.create_pipeline") as mock_factory:
            mock_pipeline = MagicMock()
            mock_pipeline.run = AsyncMock(side_effect=_mock_pipeline_run())
            mock_factory.return_value = mock_pipeline

            result = json.loads(await qc_mcp_server.qc_run_pipeline("proj-docs"))
            assert result["status"] == "completed"
            # Verify resume_from was passed
            call_args = mock_pipeline.run.call_args
            assert call_args.kwargs.get("resume_from") == "Thematic Coding"

    @pytest.mark.asyncio
    async def test_run_stage(self, project_with_docs, tmp_store):
        mock_stage = MagicMock()
        mock_stage.name.return_value = "Thematic Coding"

        async def _exec(state, ctx):
            state.codebook.codes = [Code(id="S1", name="Stage Theme")]
            return state
        mock_stage.execute = AsyncMock(side_effect=_exec)

        with patch("qc_mcp_server.create_pipeline") as mock_factory:
            mock_pipeline = MagicMock()
            mock_pipeline.stages = [mock_stage]
            mock_factory.return_value = mock_pipeline

            result = json.loads(await qc_mcp_server.qc_run_stage("proj-docs", "Thematic Coding"))
            assert result["stage"] == "Thematic Coding"
            assert result["status"] == "completed"
            assert result["codes"] == 1

    @pytest.mark.asyncio
    async def test_run_stage_not_found(self, project_with_docs, tmp_store):
        mock_stage = MagicMock()
        mock_stage.name.return_value = "Ingest"

        with patch("qc_mcp_server.create_pipeline") as mock_factory:
            mock_pipeline = MagicMock()
            mock_pipeline.stages = [mock_stage]
            mock_factory.return_value = mock_pipeline

            result = json.loads(await qc_mcp_server.qc_run_stage("proj-docs", "Nonexistent Stage"))
            assert "error" in result
            assert "available_stages" in result

    @pytest.mark.asyncio
    async def test_recode(self, completed_project, tmp_store):
        with patch("qc_mcp_server.create_incremental_pipeline") as mock_factory:
            mock_pipeline = MagicMock()

            async def _run(state, ctx, resume_from=None):
                state.pipeline_status = PipelineStatus.COMPLETED
                state.iteration = 2
                return state
            mock_pipeline.run = AsyncMock(side_effect=_run)
            mock_factory.return_value = mock_pipeline

            result = json.loads(await qc_mcp_server.qc_recode("proj-done"))
            assert result["status"] == "completed"
            assert result["iteration"] == 2
            assert result["codes"] == 2  # existing codes preserved

    @pytest.mark.asyncio
    async def test_recode_no_codebook(self, project_with_docs, tmp_store):
        result = json.loads(await qc_mcp_server.qc_recode("proj-docs"))
        assert "error" in result
        assert "codebook" in result["error"].lower()


# ---------------------------------------------------------------------------
# IRR / Stability (mocked)
# ---------------------------------------------------------------------------

class TestIRRStability:
    @pytest.mark.asyncio
    async def test_run_irr(self, project_with_docs, tmp_store):
        with patch("qc_mcp_server.run_irr_analysis", new_callable=AsyncMock) as mock_irr:
            mock_irr.return_value = IRRResult(
                num_passes=3,
                aligned_codes=["ai adoption", "privacy"],
                unmatched_codes=["misc"],
                percent_agreement=0.75,
                fleiss_kappa=0.65,
                interpretation="substantial",
            )

            result = json.loads(await qc_mcp_server.qc_run_irr("proj-docs", passes=3))
            assert result["passes"] == 3
            assert result["percent_agreement"] == 0.75
            assert result["fleiss_kappa"] == 0.65
            assert result["interpretation"] == "substantial"
            assert len(result["aligned_codes"]) == 2

    @pytest.mark.asyncio
    async def test_run_irr_no_docs(self, sample_project, tmp_store):
        result = json.loads(await qc_mcp_server.qc_run_irr("proj-1"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_stability(self, project_with_docs, tmp_store):
        with patch("qc_mcp_server.run_stability_analysis", new_callable=AsyncMock) as mock_stab:
            mock_stab.return_value = StabilityResult(
                num_runs=5,
                overall_stability=0.82,
                stable_codes=["ai adoption"],
                moderate_codes=["privacy"],
                unstable_codes=["misc"],
                code_stability={"ai adoption": 1.0, "privacy": 0.6, "misc": 0.2},
                model_name="gpt-5-mini",
            )

            result = json.loads(await qc_mcp_server.qc_run_stability("proj-docs", runs=5))
            assert result["runs"] == 5
            assert result["overall_stability"] == 0.82
            assert result["stable_codes"] == ["ai adoption"]
            assert result["code_stability"]["ai adoption"] == 1.0

    @pytest.mark.asyncio
    async def test_run_stability_no_docs(self, sample_project, tmp_store):
        result = json.loads(await qc_mcp_server.qc_run_stability("proj-1"))
        assert "error" in result


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class TestReview:
    def test_review_summary(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_summary("proj-done"))
        assert result["codes_count"] == 2
        assert result["applications_count"] == 2
        assert isinstance(result["can_resume"], bool)

    def test_review_summary_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_summary("nope"))
        assert "error" in result

    def test_approve_all_codes(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_approve_all_codes("proj-done"))
        assert result["approved"] == 2
        # Verify persisted
        state = tmp_store.load("proj-done")
        for code in state.codebook.codes:
            assert code.provenance == Provenance.HUMAN

    def test_approve_all_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_approve_all_codes("nope"))
        assert "error" in result

    def test_review_codes(self, completed_project, tmp_store):
        decisions = [
            {"target_type": "code", "target_id": "C1", "action": "approve"},
            {"target_type": "code", "target_id": "C2", "action": "reject"},
        ]
        result = json.loads(qc_mcp_server.qc_review_codes("proj-done", decisions))
        assert result["applied"] == 2
        # Verify persisted: C2 should be gone
        state = tmp_store.load("proj-done")
        assert state.codebook.get_code("C2") is None
        assert state.codebook.get_code("C1").provenance == Provenance.HUMAN

    def test_review_codes_invalid_action(self, completed_project, tmp_store):
        decisions = [{"target_type": "code", "target_id": "C1", "action": "invalid_action"}]
        result = json.loads(qc_mcp_server.qc_review_codes("proj-done", decisions))
        assert "error" in result

    def test_review_codes_empty(self, completed_project, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_codes("proj-done", []))
        assert "error" in result

    def test_review_codes_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_codes("nope", [{"target_type": "code", "target_id": "X", "action": "approve"}]))
        assert "error" in result


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

class TestExport:
    def test_export_markdown(self, completed_project, tmp_store, tmp_path):
        out = str(tmp_path / "report.md")
        result = json.loads(qc_mcp_server.qc_export_markdown("proj-done", output_file=out))
        assert result["format"] == "markdown"
        assert Path(result["exported_to"]).exists()

    def test_export_json(self, completed_project, tmp_store, tmp_path):
        out = str(tmp_path / "export.json")
        result = json.loads(qc_mcp_server.qc_export_json("proj-done", output_file=out))
        assert result["format"] == "json"
        assert Path(result["exported_to"]).exists()

    def test_export_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_export_markdown("nope"))
        assert "error" in result
