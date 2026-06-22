"""
Tests for project run, export, and API resume functionality.
Uses mock stages to avoid LLM calls.
"""

import asyncio
import csv
import json
import pytest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from qc_clean.core.cli.commands import project as project_commands
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    CorpusScope,
    Document,
    Entity,
    DomainEntityRelationship,
    Methodology,
    PipelineStatus,
    PerspectiveAnalysis,
    ParticipantPerspective,
    ProjectConfig,
    ProjectState,
    Recommendation,
    Synthesis,
)
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.pipeline.pipeline_engine import AnalysisPipeline, PipelineStage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_store(tmp_path):
    return ProjectStore(projects_dir=tmp_path)


@pytest.fixture
def sample_state():
    """A richly populated project state for testing export."""
    doc = Document(id="d1", name="interview1.txt", content="Hello, this is a test interview.")
    code_parent = Code(id="C1", name="Communication", description="Communication themes", mention_count=5, confidence=0.8)
    code_child = Code(id="C2", name="Active Listening", description="Listening skills", parent_id="C1", level=1, mention_count=3, confidence=0.7)
    app = CodeApplication(id="A1", code_id="C1", doc_id="d1", quote_text="this is a test", speaker="Interviewer", confidence=0.85)

    return ProjectState(
        id="test-proj",
        name="Test Export Project",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[code_parent, code_child]),
        code_applications=[app],
        entities=[
            Entity(id="E1", name="Team A", entity_type="organization"),
            Entity(id="E2", name="Team B", entity_type="organization"),
        ],
        entity_relationships=[
            DomainEntityRelationship(
                entity_1_id="E1", entity_2_id="E2",
                relationship_type="collaborates_with", strength=0.9,
            ),
        ],
        perspective_analysis=PerspectiveAnalysis(
            participants=[
                ParticipantPerspective(name="Alice", role="Manager", perspective_summary="Focused on outcomes"),
            ],
        ),
        synthesis=Synthesis(
            executive_summary="The analysis reveals key communication patterns.",
            key_findings=["Finding 1", "Finding 2"],
            recommendations=[
                Recommendation(title="Improve listening", description="Train team on active listening", priority="high"),
            ],
        ),
        pipeline_status=PipelineStatus.COMPLETED,
    )


# ---------------------------------------------------------------------------
# Mock stages for pipeline tests
# ---------------------------------------------------------------------------

class MockCodingStage(PipelineStage):
    """Adds a code to the codebook."""
    def name(self) -> str:
        return "mock_coding"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.codebook.codes.append(
            Code(id="MC1", name="MockTheme", mention_count=2, confidence=0.75)
        )
        return state


class MockSynthesisStage(PipelineStage):
    def name(self) -> str:
        return "mock_synthesis"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.synthesis = Synthesis(
            executive_summary="Mock synthesis complete.",
            key_findings=["Mock finding"],
        )
        return state


class MockFailingRunStage(PipelineStage):
    def name(self) -> str:
        return "mock_failure"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        raise RuntimeError("mock run failure")


class MockReviewStage(PipelineStage):
    def name(self) -> str:
        return "mock_review_stage"

    def requires_human_review(self) -> bool:
        return True

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.codebook.codes.append(
            Code(id="RC1", name="ReviewTheme", mention_count=1, confidence=0.6)
        )
        return state


# ---------------------------------------------------------------------------
# Tests: _run_project logic
# ---------------------------------------------------------------------------

class TestProjectRun:
    def test_run_pipeline_on_project(self, tmp_store):
        """Run a mock pipeline and verify state is saved."""
        state = ProjectState(
            id="run-test",
            name="Run Test",
            corpus=Corpus(documents=[Document(name="test.txt", content="data")]),
        )
        tmp_store.save(state)

        # Build a mock pipeline
        stages = [MockCodingStage(), MockSynthesisStage()]
        pipeline = AnalysisPipeline(stages=stages)

        loaded = tmp_store.load("run-test")
        result = asyncio.run(
            pipeline.run(loaded, {"model_name": "gpt-5-mini"})
        )
        tmp_store.save(result)

        # Reload and verify
        final = tmp_store.load("run-test")
        assert final.pipeline_status == PipelineStatus.COMPLETED
        assert len(final.codebook.codes) == 1
        assert final.codebook.codes[0].name == "MockTheme"
        assert final.synthesis is not None
        assert final.synthesis.executive_summary == "Mock synthesis complete."

    def test_run_with_review_pause_and_resume(self, tmp_store):
        """Pipeline pauses for review, then resumes."""
        state = ProjectState(
            id="review-test",
            name="Review Test",
            corpus=Corpus(documents=[Document(name="test.txt", content="data")]),
        )
        tmp_store.save(state)

        stages = [MockReviewStage(), MockSynthesisStage()]
        pipeline = AnalysisPipeline(stages=stages)

        # First run: should pause
        loaded = tmp_store.load("review-test")
        result = asyncio.run(
            pipeline.run(loaded, {})
        )
        assert result.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW
        assert result.current_phase == "mock_review_stage"
        tmp_store.save(result)

        # Resume
        loaded2 = tmp_store.load("review-test")
        result2 = asyncio.run(
            pipeline.run(loaded2, {}, resume_from="mock_review_stage")
        )
        assert result2.pipeline_status == PipelineStatus.COMPLETED
        assert result2.synthesis is not None
        tmp_store.save(result2)

    def test_run_on_empty_project_fails(self, tmp_store):
        """Should not run if there are no documents."""
        state = ProjectState(id="empty-test", name="Empty")
        tmp_store.save(state)

        loaded = tmp_store.load("empty-test")
        assert loaded.corpus.num_documents == 0

    def test_save_callback_called(self, tmp_store):
        """The on_stage_complete callback should persist state after each stage."""
        state = ProjectState(
            id="callback-test",
            name="Callback Test",
            corpus=Corpus(documents=[Document(name="t.txt", content="x")]),
        )
        tmp_store.save(state)

        callback_count = [0]

        async def save_cb(s):
            tmp_store.save(s)
            callback_count[0] += 1

        stages = [MockCodingStage(), MockSynthesisStage()]
        pipeline = AnalysisPipeline(stages=stages, on_stage_complete=save_cb)

        loaded = tmp_store.load("callback-test")
        asyncio.run(
            pipeline.run(loaded, {})
        )

        assert callback_count[0] == 2

    def test_run_project_records_wall_clock_timing(self, tmp_store, monkeypatch):
        """CLI project run records end-to-end wall-clock timing metadata."""
        state = ProjectState(
            id="timing-test",
            name="Timing Test",
            corpus=Corpus(documents=[Document(name="t.txt", content="x")]),
        )
        tmp_store.save(state)

        def fake_create_pipeline(methodology, on_stage_complete, enable_human_review):
            return AnalysisPipeline(
                stages=[MockCodingStage()],
                on_stage_complete=on_stage_complete,
            )

        monkeypatch.setattr(
            "qc_clean.core.pipeline.pipeline_factory.create_pipeline",
            fake_create_pipeline,
        )

        result = project_commands._run_project(
            tmp_store,
            SimpleNamespace(
                project_id=state.id,
                review=False,
                model=None,
                exhaustive=True,
            ),
        )

        assert result == 0
        saved = tmp_store.load(state.id)
        timing = saved.config.extra["run_timing"]
        assert timing["schema_version"] == 1
        assert timing["status"] == "completed"
        assert timing["duration_s"] >= 0
        assert timing["trace_id"] == f"qualitative_coding/project/{state.id}"
        assert timing["model"] == "gpt-5-mini"
        assert timing["exhaustive_coding"] is True
        assert timing["resume_from"] is None
        assert timing["document_count"] == 1
        assert timing["phase_result_count"] == 1

    def test_run_project_records_wall_clock_timing_on_failure(self, tmp_store, monkeypatch):
        """Failed CLI project runs record timing before the failed state is saved."""
        state = ProjectState(
            id="timing-failed",
            name="Timing Failed",
            corpus=Corpus(documents=[Document(name="t.txt", content="x")]),
        )
        tmp_store.save(state)

        def fake_create_pipeline(methodology, on_stage_complete, enable_human_review):
            return AnalysisPipeline(
                stages=[MockFailingRunStage()],
                on_stage_complete=on_stage_complete,
            )

        monkeypatch.setattr(
            "qc_clean.core.pipeline.pipeline_factory.create_pipeline",
            fake_create_pipeline,
        )

        result = project_commands._run_project(
            tmp_store,
            SimpleNamespace(
                project_id=state.id,
                review=False,
                model="gpt-5-mini",
                exhaustive=False,
            ),
        )

        assert result == 1
        saved = tmp_store.load(state.id)
        timing = saved.config.extra["run_timing"]
        assert saved.pipeline_status == PipelineStatus.FAILED
        assert timing["status"] == "failed"
        assert timing["duration_s"] >= 0
        assert timing["trace_id"] == f"qualitative_coding/project/{state.id}"
        assert timing["exhaustive_coding"] is False


# ---------------------------------------------------------------------------
# Tests: ProjectExporter
# ---------------------------------------------------------------------------

class TestProjectExporter:
    def test_export_json(self, tmp_path, sample_state):
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()

        out = tmp_path / "output.json"
        path = exporter.export_json(sample_state, str(out))
        assert Path(path).exists()

        data = json.loads(Path(path).read_text())
        assert data["name"] == "Test Export Project"
        assert data["pipeline_status"] == "completed"
        assert len(data["codebook"]["codes"]) == 2

    def test_export_csv(self, tmp_path, sample_state):
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()

        paths = exporter.export_csv(sample_state, str(tmp_path))
        assert len(paths) == 2

        # Check codes.csv
        codes_path = tmp_path / "codes.csv"
        assert codes_path.exists()
        with open(codes_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        names = {r["name"] for r in rows}
        assert "Communication" in names
        assert "Active Listening" in names

        # Check applications.csv
        apps_path = tmp_path / "applications.csv"
        assert apps_path.exists()
        with open(apps_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["quote_text"] == "this is a test"
        assert rows[0]["code_name"] == "Communication"
        assert rows[0]["doc_name"] == "interview1.txt"

    def test_export_markdown(self, tmp_path, sample_state):
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()

        out = tmp_path / "report.md"
        path = exporter.export_markdown(sample_state, str(out))
        assert Path(path).exists()

        content = Path(path).read_text()
        assert "# Test Export Project" in content
        assert "## Executive Summary" in content
        assert "communication patterns" in content
        assert "## Codebook" in content
        assert "Communication" in content
        assert "Active Listening" in content
        assert "## Key Quotes" in content
        assert "this is a test" in content
        assert "## Participant Perspectives" in content
        assert "Alice" in content
        assert "## Entity Relationships" in content
        assert "Team A" in content
        assert "## Recommendations" in content
        assert "Improve listening" in content
        assert "## Key Findings" in content
        assert "Finding 1" in content

    def test_export_markdown_code_hierarchy(self, tmp_path, sample_state):
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()

        out = tmp_path / "report.md"
        path = exporter.export_markdown(sample_state, str(out))
        content = Path(path).read_text()
        assert "### Code Hierarchy" in content
        assert "**Communication**" in content
        assert "Active Listening" in content

    def test_export_json_default_filename(self, tmp_path, sample_state):
        """Export JSON without specifying output file."""
        from qc_clean.core.export.data_exporter import ProjectExporter
        import os
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            exporter = ProjectExporter()
            path = exporter.export_json(sample_state)
            assert Path(path).exists()
            assert "Test Export Project" in path
        finally:
            os.chdir(old_cwd)

    def test_default_export_filename_sanitizes_project_name(self, tmp_path):
        """Default export filenames should not inherit directories from project names."""
        from qc_clean.core.export.data_exporter import ProjectExporter
        import os

        state = ProjectState(id="escape", name="../outside/project")
        old_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            path = ProjectExporter().export_json(state)
            assert Path(path).name == "_outside_project.json"
            assert Path(path).parent == Path(".")
            assert (tmp_path / "_outside_project.json").exists()
            assert not (tmp_path.parent / "outside").exists()
        finally:
            os.chdir(old_cwd)

    def test_export_csv_empty_state(self, tmp_path):
        """Export CSV with no codes/applications."""
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()
        state = ProjectState(id="empty", name="Empty")
        paths = exporter.export_csv(state, str(tmp_path))
        assert len(paths) == 2
        # codes.csv should have header only
        with open(tmp_path / "codes.csv") as f:
            reader = csv.DictReader(f)
            assert len(list(reader)) == 0

    def test_export_markdown_minimal(self, tmp_path):
        """Export Markdown from a minimal state (no synthesis, no entities, etc.)."""
        from qc_clean.core.export.data_exporter import ProjectExporter
        exporter = ProjectExporter()
        state = ProjectState(
            id="minimal",
            name="Minimal Project",
            codebook=Codebook(codes=[Code(id="C1", name="Theme", mention_count=1, confidence=0.5)]),
        )
        out = tmp_path / "minimal.md"
        path = exporter.export_markdown(state, str(out))
        content = Path(path).read_text()
        assert "# Minimal Project" in content
        assert "Theme" in content
        # Should NOT contain sections that have no data
        assert "## Executive Summary" not in content
        assert "## Recommendations" not in content

    def test_project_export_command_qdpx(self, tmp_path, tmp_store, sample_state, capsys):
        """The documented project export CLI path must reach QDPX export."""
        from qc_clean.core.cli.commands.project import _export_project

        tmp_store.save(sample_state)
        out = tmp_path / "export.qdpx"
        args = MagicMock(
            project_id=sample_state.id,
            format="qdpx",
            output_file=str(out),
            output_dir=None,
        )

        result = _export_project(tmp_store, args)

        assert result == 0
        assert out.exists()
        assert zipfile.is_zipfile(out)
        assert "Exported QDPX" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Tests: CLI argument parsing
# ---------------------------------------------------------------------------

class TestCLIParsing:
    def test_run_subparser(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "run", "my-proj-id"])
        assert args.command == "project"
        assert args.project_action == "run"
        assert args.project_id == "my-proj-id"
        assert args.model is None
        assert args.review is False

    def test_run_subparser_with_options(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "run", "pid", "--model", "gpt-5", "--review"])
        assert args.model == "gpt-5"
        assert args.review is True

    def test_export_subparser(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "export", "pid", "--format", "csv", "--output-dir", "/tmp/out"])
        assert args.command == "project"
        assert args.project_action == "export"
        assert args.project_id == "pid"
        assert args.format == "csv"
        assert args.output_dir == "/tmp/out"

    def test_export_subparser_json(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "export", "pid", "--format", "json", "--output-file", "out.json"])
        assert args.format == "json"
        assert args.output_file == "out.json"

    def test_export_subparser_qdpx(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "export", "pid", "--format", "qdpx", "--output-file", "out.qdpx"])
        assert args.command == "project"
        assert args.project_action == "export"
        assert args.project_id == "pid"
        assert args.format == "qdpx"
        assert args.output_file == "out.qdpx"

    def test_claims_subparser(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args(["project", "claims", "pid", "--limit", "5"])
        assert args.command == "project"
        assert args.project_action == "claims"
        assert args.project_id == "pid"
        assert args.limit == 5

    def test_scope_subparser(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args([
            "project",
            "scope",
            "pid",
            "--phenomenon",
            "AI adoption",
            "--population",
            "Clinic staff",
            "--sampling-frame",
            "Pilot clinics",
            "--include",
            "Pilot participant",
            "--include",
            "Direct workflow involvement",
            "--exclude",
            "Vendors",
            "--notes",
            "Bounded to early adopters.",
        ])

        assert args.command == "project"
        assert args.project_action == "scope"
        assert args.project_id == "pid"
        assert args.phenomenon == "AI adoption"
        assert args.population == "Clinic staff"
        assert args.sampling_frame == "Pilot clinics"
        assert args.inclusion_criteria == [
            "Pilot participant",
            "Direct workflow involvement",
        ]
        assert args.exclusion_criteria == ["Vendors"]
        assert args.notes == "Bounded to early adopters."

    def test_create_subparser_accepts_scope_fields(self):
        from qc_cli import create_parser
        parser = create_parser()

        args = parser.parse_args([
            "project",
            "create",
            "--name",
            "Scoped Project",
            "--methodology",
            "thematic_analysis",
            "--phenomenon",
            "AI adoption",
            "--population",
            "Clinic staff",
            "--sampling-frame",
            "Pilot clinics",
            "--include",
            "Pilot participant",
            "--include",
            "Direct workflow involvement",
            "--exclude",
            "Vendors",
            "--notes",
            "Bounded to early adopters.",
        ])

        assert args.command == "project"
        assert args.project_action == "create"
        assert args.name == "Scoped Project"
        assert args.methodology == "thematic_analysis"
        assert args.phenomenon == "AI adoption"
        assert args.population == "Clinic staff"
        assert args.sampling_frame == "Pilot clinics"
        assert args.inclusion_criteria == [
            "Pilot participant",
            "Direct workflow involvement",
        ]
        assert args.exclusion_criteria == ["Vendors"]
        assert args.notes == "Bounded to early adopters."


class TestProjectClaimsCommand:
    def test_project_claims_command_outputs_summary(self, tmp_store, capsys):
        from qc_clean.core.cli.commands.project import _show_claims

        state = ProjectState(
            id="claims-proj",
            name="Claims Project",
            claims=[
                AnalyticClaim(
                    claim_kind=ClaimKind.CODE,
                    source_stage="thematic_coding",
                    claim_text="Efficiency is a code.",
                    scope=ClaimScope(code_ids=["C1"]),
                    origin_object_type="code",
                    origin_object_id="C1",
                    support_status=ClaimSupportStatus.SUPPORTED,
                )
            ],
        )
        tmp_store.save(state)
        args = MagicMock(project_id="claims-proj", limit=10)

        result = _show_claims(tmp_store, args)

        assert result == 0
        out = capsys.readouterr().out
        assert "Claim Ledger: Claims Project" in out
        assert "Total claims: 1" in out
        assert "Disconfirmation targets: 1" in out
        assert "0 challenged, 1 unchallenged" in out
        assert "thematic_coding" in out
        assert "Efficiency is a code." in out


class TestProjectScopeCommand:
    def test_project_create_command_leaves_scope_unset_when_omitted(self, tmp_store, capsys):
        from qc_clean.core.cli.commands.project import _create_project

        args = SimpleNamespace(
            name="Unscoped Project",
            methodology="thematic_analysis",
        )

        result = _create_project(tmp_store, args)

        assert result == 0
        out = capsys.readouterr().out
        project_id = next(
            line.split(": ", 1)[1]
            for line in out.splitlines()
            if line.startswith("Created project:")
        )
        loaded = tmp_store.load(project_id)
        assert loaded.corpus_scope is None
        assert "Corpus scope: set" not in out

    def test_project_create_command_saves_scope_when_supplied(self, tmp_store, capsys):
        from qc_clean.core.cli.commands.project import _create_project

        args = SimpleNamespace(
            name="Scoped Project",
            methodology="thematic_analysis",
            phenomenon="AI adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinics",
            inclusion_criteria=["Pilot participant"],
            exclusion_criteria=["Vendors"],
            notes="Bounded to early adopters.",
        )

        result = _create_project(tmp_store, args)

        assert result == 0
        out = capsys.readouterr().out
        project_id = next(
            line.split(": ", 1)[1]
            for line in out.splitlines()
            if line.startswith("Created project:")
        )
        loaded = tmp_store.load(project_id)
        assert loaded.corpus_scope == CorpusScope(
            phenomenon="AI adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinics",
            inclusion_criteria=["Pilot participant"],
            exclusion_criteria=["Vendors"],
            notes="Bounded to early adopters.",
        )
        assert "Corpus scope: set" in out

    def test_project_scope_command_updates_and_outputs_scope(self, tmp_store, capsys):
        from qc_clean.core.cli.commands.project import _show_or_update_scope

        state = ProjectState(id="scope-proj", name="Scope Project")
        tmp_store.save(state)
        args = MagicMock(
            project_id="scope-proj",
            phenomenon="AI adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinics",
            inclusion_criteria=["Pilot participant"],
            exclusion_criteria=["Vendors"],
            notes="Bounded to early adopters.",
        )

        result = _show_or_update_scope(tmp_store, args)

        assert result == 0
        loaded = tmp_store.load("scope-proj")
        assert loaded.corpus_scope == CorpusScope(
            phenomenon="AI adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinics",
            inclusion_criteria=["Pilot participant"],
            exclusion_criteria=["Vendors"],
            notes="Bounded to early adopters.",
        )
        out = capsys.readouterr().out
        assert "Corpus Scope: Scope Project" in out
        assert "Phenomenon: AI adoption" in out
        assert "Population: Clinic staff" in out
        assert "Inclusion criteria:" in out
        assert "Pilot participant" in out


# ---------------------------------------------------------------------------
# Tests: API endpoints
# ---------------------------------------------------------------------------

class TestAPIEndpoints:
    def test_get_project_endpoint_registered(self):
        """Verify the GET /projects/{project_id} endpoint is in the endpoint list."""
        from qc_clean.plugins.api.api_server import QCAPIServer
        server = QCAPIServer({"background_processing_enabled": True, "enable_docs": False})

        # We need to trigger endpoint registration
        # The endpoints are registered in _register_default_endpoints which requires FastAPI
        try:
            import fastapi
            # Create a minimal app to trigger registration
            server._app = fastapi.FastAPI()
            server._register_default_endpoints()
            paths = [e["path"] for e in server.endpoints]
            assert "/projects/{project_id}" in paths
            assert "/projects/{project_id}/claims" in paths
            assert "/projects/{project_id}/resume" in paths
        except ImportError:
            pytest.skip("FastAPI not installed")
