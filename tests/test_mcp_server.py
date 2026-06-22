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
    AnalyticClaim,
    AnalysisMemo,
    AnalysisPhaseResult,
    ClaimAdjudicationStatus,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    Code,
    CodeApplication,
    CodeRelationship,
    Codebook,
    Corpus,
    CorpusScope,
    DomainEntityRelationship,
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


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file for test assertions."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
        assert result["corpus_scope"] is None
        assert result["corpus_scope_set"] is False

    def test_create_project_with_scope(self, tmp_store):
        result = json.loads(
            qc_mcp_server.qc_create_project(
                "Scoped Study",
                "thematic_analysis",
                phenomenon="AI adoption",
                population="Clinic staff",
                sampling_frame="Pilot clinics",
                inclusion_criteria=["Pilot participant"],
                exclusion_criteria=["Vendors"],
                notes="Bounded to early adopters.",
            )
        )

        assert result["name"] == "Scoped Study"
        assert result["corpus_scope_set"] is True
        assert result["corpus_scope"] == {
            "phenomenon": "AI adoption",
            "population": "Clinic staff",
            "sampling_frame": "Pilot clinics",
            "inclusion_criteria": ["Pilot participant"],
            "exclusion_criteria": ["Vendors"],
            "notes": "Bounded to early adopters.",
        }
        loaded = tmp_store.load(result["project_id"])
        assert loaded.corpus_scope == CorpusScope(
            phenomenon="AI adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinics",
            inclusion_criteria=["Pilot participant"],
            exclusion_criteria=["Vendors"],
            notes="Bounded to early adopters.",
        )

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

    @pytest.mark.parametrize("invalid_id", ["../proj-1", "proj-1!"])
    def test_invalid_project_ids_return_error_without_aliasing_existing_project(
        self, sample_project, tmp_store, tmp_path, invalid_id
    ):
        export_path = tmp_path / "should-not-export.json"

        results = [
            json.loads(qc_mcp_server.qc_show_project(invalid_id)),
            json.loads(qc_mcp_server.qc_get_claims(invalid_id)),
            json.loads(qc_mcp_server.qc_get_codebook(invalid_id)),
            json.loads(qc_mcp_server.qc_export_json(invalid_id, str(export_path))),
        ]

        for result in results:
            assert "error" in result
            assert "not found" in result["error"]

        assert export_path.exists() is False
        assert tmp_store.exists("proj-1") is True
        assert json.loads(qc_mcp_server.qc_show_project("proj-1"))["id"] == "proj-1"

    @pytest.mark.parametrize("invalid_id", ["../proj-1", "proj-1!"])
    def test_delete_invalid_project_id_does_not_delete_existing_project(
        self, sample_project, tmp_store, invalid_id
    ):
        result = json.loads(qc_mcp_server.qc_delete_project(invalid_id))

        assert "error" in result
        assert "not found" in result["error"]
        assert tmp_store.exists("proj-1") is True
        assert json.loads(qc_mcp_server.qc_show_project("proj-1"))["id"] == "proj-1"

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

    def test_get_codebook_surfaces_data_warnings(self, completed_project, tmp_store):
        completed_project.data_warnings = ["Incremental recode invalidated synthesis."]
        tmp_store.save(completed_project)

        result = json.loads(qc_mcp_server.qc_get_codebook("proj-done"))

        assert result["data_warnings"] == ["Incremental recode invalidated synthesis."]

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

    def test_get_claims(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="AI Adoption is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
                support_status=ClaimSupportStatus.SUPPORTED,
                supporting_anchors=[
                    ClaimAnchor(
                        doc_id="d1",
                        start_char=0,
                        end_char=18,
                        quote_text="AI adoption evidence",
                        quote_hash="support-mcp",
                        code_application_id="A1",
                    )
                ],
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id="d2",
                        start_char=5,
                        end_char=24,
                        quote_text="AI adoption exception",
                        quote_hash="contrary-mcp",
                    )
                ],
            )
        ]
        tmp_store.save(completed_project)

        result = json.loads(qc_mcp_server.qc_get_claims("proj-done"))

        assert result["claim_summary"]["total_claims"] == 1
        assert result["disconfirmation_summary"]["total_targets"] == 1
        assert result["disconfirmation_summary"]["unchallenged_targets"] == 1
        assert result["claims"][0]["claim_text"] == "AI Adoption is a code."
        assert result["claims"][0]["support_status"] == "supported"
        assert result["claims"][0]["scope"]["code_ids"] == ["C1"]
        assert result["claims"][0]["scope"]["corpus_level"] is False
        assert result["claims"][0]["supporting_anchors"] == 1
        assert result["claims"][0]["contrary_anchors"] == 1
        assert result["claims"][0]["supporting_anchor_details"][0] == {
            "doc_id": "d1",
            "start_char": 0,
            "end_char": 18,
            "quote_hash": "support-mcp",
            "quote_text": "AI adoption evidence",
            "segment_id": None,
            "code_application_id": "A1",
        }
        assert result["claims"][0]["contrary_anchor_details"][0]["quote_hash"] == "contrary-mcp"


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
    async def test_run_irr_application_level(self, project_with_docs, tmp_store):
        with patch("qc_mcp_server.run_irr_analysis", new_callable=AsyncMock) as mock_irr:
            mock_irr.return_value = IRRResult(
                num_passes=2,
                percent_agreement=1.0,
                cohens_kappa=1.0,
                interpretation="almost perfect",
                application_level=True,
                application_units=0,
                application_percent_agreement=None,
                application_interpretation="no positive code applications compared",
                segment_decision_units=2,
                segment_decision_percent_agreement=1.0,
                segment_decision_cohens_kappa=1.0,
                segment_decision_interpretation="almost perfect",
            )

            result = json.loads(await qc_mcp_server.qc_run_irr(
                "proj-docs", passes=2, application_level=True,
            ))

            assert result["application_level"] is True
            assert result["application_units"] == 0
            assert result["application_percent_agreement"] is None
            assert result["application_interpretation"] == "no positive code applications compared"
            assert result["segment_decision_units"] == 2
            assert result["segment_decision_percent_agreement"] == 1.0
            assert result["segment_decision_cohens_kappa"] == 1.0
            mock_irr.assert_awaited_once()
            assert mock_irr.await_args.kwargs["application_level"] is True

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

    def test_review_claims(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="claim-review-mcp",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="AI adoption changes workflow.",
                scope=ClaimScope(corpus_level=True, code_ids=["C1"]),
                origin_object_type="synthesis_key_finding",
                origin_object_id="finding:0",
                support_status=ClaimSupportStatus.NEEDS_ANCHOR,
            )
        ]
        tmp_store.save(completed_project)

        result = json.loads(qc_mcp_server.qc_review_claims("proj-done"))

        assert result["project_id"] == "proj-done"
        assert result["project_name"] == "Completed Study"
        assert result["pipeline_status"] == "completed"
        assert result["summary"]["claims_count"] == 1
        assert result["can_resume"] is False
        assert result["returned"] == 1
        assert result["total_claims"] == 1
        claim = result["claims"][0]
        assert claim["id"] == "claim-review-mcp"
        assert claim["kind"] == "synthesis_finding"
        assert claim["source_stage"] == "synthesis"
        assert claim["support_status"] == "needs_anchor"
        assert claim["adjudication_status"] == "pending"
        assert claim["claim_text"] == "AI adoption changes workflow."
        assert claim["scope"]["corpus_level"] is True
        assert claim["scope"]["code_ids"] == ["C1"]
        assert claim["supporting_anchors"] == 0
        assert claim["contrary_anchors"] == 0
        assert claim["revision_history_count"] == 0
        assert claim["created_by"] == "llm"

    def test_review_claims_limit(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Claim 1.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            ),
            AnalyticClaim(
                id="claim-2",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Claim 2.",
                scope=ClaimScope(code_ids=["C2"]),
                origin_object_type="code",
                origin_object_id="C2",
            ),
        ]
        tmp_store.save(completed_project)

        limited = json.loads(qc_mcp_server.qc_review_claims("proj-done", limit=1))
        negative = json.loads(qc_mcp_server.qc_review_claims("proj-done", limit=-5))

        assert limited["returned"] == 1
        assert limited["total_claims"] == 2
        assert limited["limit"] == 1
        assert limited["claims"][0]["id"] == "claim-1"
        assert negative["returned"] == 0
        assert negative["total_claims"] == 2
        assert negative["limit"] == 0

    def test_review_claims_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_claims("nope"))
        assert "error" in result

    def test_review_negative_cases(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="claim-normal",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="AI Adoption is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            ),
            AnalyticClaim(
                id="neg-mcp",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Negative case for AI Adoption: counterexample.",
                scope=ClaimScope(claim_ids=["claim-normal"], code_ids=["C1"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:0:AI Adoption",
                support_status=ClaimSupportStatus.NEEDS_ANCHOR,
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id="d2",
                        start_char=11,
                        end_char=35,
                        quote_text="AI adoption failed here",
                        quote_hash="def456",
                        code_application_id="A2",
                    )
                ],
            ),
        ]
        tmp_store.save(completed_project)

        result = json.loads(qc_mcp_server.qc_review_negative_cases("proj-done"))

        assert result["project_id"] == "proj-done"
        assert result["project_name"] == "Completed Study"
        assert result["pipeline_status"] == "completed"
        assert result["returned"] == 1
        assert result["total_negative_cases"] == 1
        assert result["can_resume"] is False
        negative_case = result["negative_cases"][0]
        assert negative_case["id"] == "neg-mcp"
        assert negative_case["kind"] == "negative_case"
        assert negative_case["scope"]["claim_ids"] == ["claim-normal"]
        assert negative_case["scope"]["code_ids"] == ["C1"]
        assert negative_case["contrary_anchors"] == 1
        assert negative_case["contrary_anchor_details"] == [
            {
                "doc_id": "d2",
                "start_char": 11,
                "end_char": 35,
                "quote_hash": "def456",
                "quote_text": "AI adoption failed here",
                "segment_id": None,
                "code_application_id": "A2",
            }
        ]

    def test_review_negative_cases_limit(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="neg-1",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Negative case 1.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:0",
            ),
            AnalyticClaim(
                id="neg-2",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Negative case 2.",
                scope=ClaimScope(code_ids=["C2"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:1",
            ),
        ]
        tmp_store.save(completed_project)

        limited = json.loads(qc_mcp_server.qc_review_negative_cases("proj-done", limit=1))
        negative = json.loads(qc_mcp_server.qc_review_negative_cases("proj-done", limit=-5))

        assert limited["returned"] == 1
        assert limited["total_negative_cases"] == 2
        assert limited["limit"] == 1
        assert limited["negative_cases"][0]["id"] == "neg-1"
        assert negative["returned"] == 0
        assert negative["total_negative_cases"] == 2
        assert negative["limit"] == 0

    def test_review_negative_cases_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_negative_cases("nope"))
        assert "error" in result

    def test_review_relationships(self, completed_project, tmp_store):
        completed_project.entities = [
            Entity(id="E1", name="AI", entity_type="concept"),
            Entity(id="E2", name="Clinic team", entity_type="team"),
        ]
        completed_project.code_relationships = [
            CodeRelationship(
                id="CR1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="tensions_with",
                strength=0.7,
                evidence=["AI use raises privacy concern."],
            )
        ]
        completed_project.entity_relationships = [
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="used_by",
                strength=0.8,
                supporting_evidence=["Clinic team uses AI."],
            )
        ]
        tmp_store.save(completed_project)

        result = json.loads(qc_mcp_server.qc_review_relationships("proj-done"))

        assert result["project_id"] == "proj-done"
        assert result["project_name"] == "Completed Study"
        assert result["pipeline_status"] == "completed"
        assert result["summary"]["relationships_count"] == 2
        assert result["can_resume"] is False
        assert result["returned"] == 2
        assert result["total_relationships"] == 2
        code_rel = result["relationships"][0]
        assert code_rel["target_type"] == "code_relationship"
        assert code_rel["id"] == "CR1"
        assert code_rel["source_name"] == "AI Adoption"
        assert code_rel["target_name"] == "Privacy Concerns"
        assert code_rel["evidence_count"] == 1
        entity_rel = result["relationships"][1]
        assert entity_rel["target_type"] == "entity_relationship"
        assert entity_rel["id"] == "ER1"
        assert entity_rel["source_name"] == "AI"
        assert entity_rel["target_name"] == "Clinic team"

    def test_review_relationships_limit(self, completed_project, tmp_store):
        completed_project.code_relationships = [
            CodeRelationship(id="CR1", source_code_id="C1", target_code_id="C2"),
            CodeRelationship(id="CR2", source_code_id="C2", target_code_id="C1"),
        ]
        tmp_store.save(completed_project)

        limited = json.loads(qc_mcp_server.qc_review_relationships("proj-done", limit=1))
        negative = json.loads(qc_mcp_server.qc_review_relationships("proj-done", limit=-5))

        assert limited["returned"] == 1
        assert limited["total_relationships"] == 2
        assert limited["limit"] == 1
        assert limited["relationships"][0]["id"] == "CR1"
        assert negative["returned"] == 0
        assert negative["total_relationships"] == 2
        assert negative["limit"] == 0

    def test_review_relationships_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_review_relationships("nope"))
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
        assert result["claims_count"] == 0
        # Verify persisted: C2 should be gone
        state = tmp_store.load("proj-done")
        assert state.codebook.get_code("C2") is None
        assert state.codebook.get_code("C1").provenance == Provenance.HUMAN

    def test_review_decisions_claim(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="claim-mcp",
                claim_kind=ClaimKind.SYNTHESIS_FINDING,
                source_stage="synthesis",
                claim_text="AI adoption changes workflow.",
                scope=ClaimScope(corpus_level=True),
                origin_object_type="synthesis_key_finding",
                origin_object_id="finding:0",
            )
        ]
        tmp_store.save(completed_project)
        decisions = [
            {
                "target_type": "claim",
                "target_id": "claim-mcp",
                "action": "approve",
                "rationale": "Reviewed against source evidence.",
            }
        ]

        result = json.loads(qc_mcp_server.qc_review_decisions("proj-done", decisions))

        assert result["applied"] == 1
        assert result["codes_remaining"] == 2
        assert result["claims_count"] == 1
        state = tmp_store.load("proj-done")
        claim = state.claims[0]
        assert claim.adjudication_status == ClaimAdjudicationStatus.RETAINED
        assert claim.revision_history[-1].action == "approve"
        assert claim.revision_history[-1].rationale == "Reviewed against source evidence."

    def test_review_decisions_relationship(self, completed_project, tmp_store):
        completed_project.entities = [
            Entity(id="E1", name="AI", entity_type="concept"),
            Entity(id="E2", name="Clinic team", entity_type="team"),
        ]
        completed_project.code_relationships = [
            CodeRelationship(
                id="CR1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="tensions_with",
                strength=0.7,
            )
        ]
        completed_project.entity_relationships = [
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="used_by",
                strength=0.8,
            )
        ]
        tmp_store.save(completed_project)
        decisions = [
            {
                "target_type": "code_relationship",
                "target_id": "CR1",
                "action": "modify",
                "rationale": "Narrowed relation.",
                "new_value": {
                    "relationship_type": "moderates",
                    "strength": 0.9,
                    "evidence": ["reviewed evidence"],
                },
            },
            {
                "target_type": "entity_relationship",
                "target_id": "ER1",
                "action": "reject",
                "rationale": "Unsupported entity link.",
            },
        ]

        result = json.loads(qc_mcp_server.qc_review_decisions("proj-done", decisions))

        assert result["applied"] == 2
        assert result["relationships_count"] == 1
        state = tmp_store.load("proj-done")
        assert len(state.entity_relationships) == 0
        assert len(state.code_relationships) == 1
        rel = state.code_relationships[0]
        assert rel.relationship_type == "moderates"
        assert rel.strength == 0.9
        assert rel.evidence == ["reviewed evidence"]

    def test_review_codes_delegates_claim_decision(self, completed_project, tmp_store):
        completed_project.claims = [
            AnalyticClaim(
                id="claim-mcp-legacy",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="AI Adoption is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            )
        ]
        tmp_store.save(completed_project)
        decisions = [
            {
                "target_type": "claim",
                "target_id": "claim-mcp-legacy",
                "action": "reject",
                "rationale": "Not supported after review.",
            }
        ]

        result = json.loads(qc_mcp_server.qc_review_codes("proj-done", decisions))

        assert result["applied"] == 1
        assert result["claims_count"] == 1
        state = tmp_store.load("proj-done")
        claim = state.claims[0]
        assert claim.adjudication_status == ClaimAdjudicationStatus.WITHDRAWN
        assert claim.revision_history[-1].action == "reject"
        assert claim.revision_history[-1].rationale == "Not supported after review."

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

    def test_export_markdown_with_audit_manifest(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="../../report.md",
                audit_manifest=True,
            )
        )

        assert result["format"] == "markdown"
        assert Path(result["exported_to"]).parent == exports_dir
        assert Path(result["audit_manifest"]).parent == exports_dir
        assert Path(result["audit_manifest"]).name == "report.manifest.json"
        assert Path(result["audit_manifest"]).exists()

    def test_export_json_with_audit_manifest_verification(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_json(
                "proj-done",
                output_file="export.json",
                audit_manifest=True,
                verify_audit_manifest=True,
            )
        )

        assert result["format"] == "json"
        assert result["audit_verification"]["status"] == "verified"
        assert Path(result["audit_manifest"]).exists()

    def test_export_json_with_audit_event_log(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        from qc_clean.core.export.audit_event_log import verify_export_audit_event_log

        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_json(
                "proj-done",
                output_file="../../export.json",
                audit_manifest=True,
                verify_audit_manifest=True,
                audit_event_log=True,
            )
        )
        events = _read_jsonl(Path(result["audit_event_log"]))
        verification = verify_export_audit_event_log(result["audit_event_log"]).model_dump(
            mode="json"
        )

        assert result["format"] == "json"
        assert Path(result["audit_event_log"]).parent == exports_dir
        assert Path(result["audit_event_log"]).name == "export.audit_events.jsonl"
        assert [event["event_type"] for event in events] == [
            "manifest_written",
            "manifest_verified",
        ]
        assert events[1]["previous_event_sha256"] == events[0]["event_sha256"]
        assert verification["status"] == "verified"

    def test_export_json_with_audit_event_db(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        from qc_clean.core.export.audit_event_log import verify_export_audit_event_db

        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_json(
                "proj-done",
                output_file="../../export.json",
                audit_manifest=True,
                verify_audit_manifest=True,
                audit_event_log=True,
                audit_event_db=True,
            )
        )
        verification = verify_export_audit_event_db(result["audit_event_db"]).model_dump(
            mode="json"
        )

        assert result["format"] == "json"
        assert Path(result["audit_event_db"]).parent == exports_dir
        assert Path(result["audit_event_db"]).name == "export.audit_events.sqlite"
        assert verification["status"] == "verified"
        assert verification["event_count"] == 2

    def test_export_publish_preflight_requires_audit_manifest(
        self,
        completed_project,
        tmp_store,
    ):
        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="report.md",
                publish_preflight=True,
            )
        )

        assert "error" in result
        assert "publish_preflight=True requires audit_manifest=True" in result["error"]

    def test_export_scope_lint_requires_publish_preflight(
        self,
        completed_project,
        tmp_store,
    ):
        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="report.md",
                audit_manifest=True,
                scope_lint=True,
            )
        )

        assert "error" in result
        assert "scope_lint=True requires publish_preflight=True" in result["error"]

    def test_export_markdown_with_publish_preflight(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="../../report.md",
                audit_manifest=True,
                publish_preflight=True,
            )
        )

        assert result["format"] == "markdown"
        assert Path(result["exported_to"]).parent == exports_dir
        assert result["publish_preflight"]["status"] == "pass"
        assert Path(result["audit_manifest"]).exists()

    def test_export_markdown_scope_lint_blocks_risky_text(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)
        completed_project.synthesis = Synthesis(
            executive_summary="Across operations teams, AI changes workflow priorities.",
            key_findings=["These findings should generalize to the broader population."],
        )
        tmp_store.save(completed_project)

        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="../../report.md",
                audit_manifest=True,
                publish_preflight=True,
                scope_lint=True,
            )
        )

        assert "error" in result
        assert "Export publish preflight failed" in result["error"]
        assert result["publish_preflight"]["status"] == "fail"
        assert any(
            failure["code"] == "scope_lint_missing_corpus_scope_generalization"
            for failure in result["publish_preflight"]["failures"]
        )
        assert Path(result["exported_to"]).parent == exports_dir
        assert Path(result["audit_manifest"]).parent == exports_dir

    def test_export_json_publish_preflight_event_log_and_db(
        self,
        completed_project,
        tmp_store,
        tmp_path,
        monkeypatch,
    ):
        from qc_clean.core.export.audit_event_log import verify_export_audit_event_db

        exports_dir = (tmp_path / "exports").resolve()
        monkeypatch.setattr(qc_mcp_server, "EXPORTS_DIR", exports_dir)

        result = json.loads(
            qc_mcp_server.qc_export_json(
                "proj-done",
                output_file="../../export.json",
                audit_manifest=True,
                publish_preflight=True,
                audit_event_log=True,
                audit_event_db=True,
            )
        )
        events = _read_jsonl(Path(result["audit_event_log"]))
        verification = verify_export_audit_event_db(result["audit_event_db"]).model_dump(
            mode="json"
        )

        assert result["publish_preflight"]["status"] == "pass"
        assert [event["event_type"] for event in events] == [
            "manifest_written",
            "publish_preflight",
        ]
        assert events[1]["event_status"] == "pass"
        assert verification["status"] == "verified"
        assert verification["event_count"] == 2

    def test_export_audit_event_log_requires_audit_manifest(
        self,
        completed_project,
        tmp_store,
    ):
        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="report.md",
                audit_event_log=True,
            )
        )

        assert "error" in result
        assert "audit_event_log=True requires audit_manifest=True" in result["error"]

    def test_export_audit_event_db_requires_event_log(
        self,
        completed_project,
        tmp_store,
    ):
        result = json.loads(
            qc_mcp_server.qc_export_markdown(
                "proj-done",
                output_file="report.md",
                audit_manifest=True,
                audit_event_db=True,
            )
        )

        assert "error" in result
        assert "audit_event_db=True requires audit_event_log=True" in result["error"]

    def test_export_verify_requires_audit_manifest(self, completed_project, tmp_store):
        result = json.loads(
            qc_mcp_server.qc_export_json(
                "proj-done",
                output_file="export.json",
                verify_audit_manifest=True,
            )
        )

        assert "error" in result
        assert "requires audit_manifest=True" in result["error"]

    def test_export_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_export_markdown("nope"))
        assert "error" in result


# ---------------------------------------------------------------------------
# Grounding report + data_warnings surfacing (INV-1 / INV-11)
# ---------------------------------------------------------------------------

class TestGroundingAndWarnings:
    def test_grounding_report(self, tmp_store):
        from qc_clean.core.grounding import resolve_span
        from qc_clean.schemas.domain import (
            Code, CodeApplication, Codebook, Corpus, Document, ProjectState,
        )
        content = "Alex: autonomy matters more than oversight here."
        doc = Document(id="dg", name="d.txt", content=content)
        m = resolve_span("autonomy matters", content)
        state = ProjectState(
            id="proj-ground", name="G",
            corpus=Corpus(documents=[doc]),
            codebook=Codebook(codes=[Code(id="C1", name="Autonomy", description="d")]),
            code_applications=[
                CodeApplication(code_id="C1", doc_id="dg", quote_text="autonomy matters",
                                start_char=m.start_char, end_char=m.end_char, quote_hash=m.quote_hash),
                CodeApplication(code_id="C1", doc_id="dg", quote_text="oversight"),  # no hash
            ],
        )
        tmp_store.save(state)
        result = json.loads(qc_mcp_server.qc_grounding_report("proj-ground"))
        assert result["grounding"]["total_applications"] == 2
        assert result["grounding"]["anchored_verified"] == 1
        assert abs(result["grounding"]["grounding_rate"] - 0.5) < 1e-9
        assert "coverage_rate" in result["coverage"]

    def test_grounding_report_not_found(self, tmp_store):
        result = json.loads(qc_mcp_server.qc_grounding_report("nope"))
        assert "error" in result

    def test_synthesis_surfaces_data_warnings(self, tmp_store):
        from qc_clean.schemas.domain import ProjectState, Synthesis
        state = ProjectState(
            id="proj-warn", name="W",
            synthesis=Synthesis(executive_summary="stale summary"),
            data_warnings=["synthesis may be stale after recode"],
        )
        tmp_store.save(state)
        result = json.loads(qc_mcp_server.qc_get_synthesis("proj-warn"))
        assert result["data_warnings"] == ["synthesis may be stale after recode"]
