"""
Tests for project persistence (qc_clean.core.persistence.project_store).
"""

import pytest
from pathlib import Path

from qc_clean.schemas.domain import (
    Code,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
from qc_clean.core.persistence.project_store import ProjectStore


@pytest.fixture
def tmp_store(tmp_path):
    """ProjectStore using a temporary directory."""
    return ProjectStore(projects_dir=tmp_path)


@pytest.fixture
def sample_state():
    doc = Document(id="d1", name="interview.txt", content="hello world")
    code = Code(id="C1", name="Theme A", mention_count=3, confidence=0.7)
    return ProjectState(
        id="test-project-1",
        name="Test Project",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[code]),
        data_warnings=["truncated"],
    )


class TestProjectStore:
    def test_save_and_load(self, tmp_store, sample_state):
        path = tmp_store.save(sample_state)
        assert path.exists()
        assert path.suffix == ".json"

        loaded = tmp_store.load("test-project-1")
        assert loaded.id == sample_state.id
        assert loaded.name == "Test Project"
        assert loaded.corpus.num_documents == 1
        assert loaded.corpus.documents[0].content == "hello world"
        assert len(loaded.codebook.codes) == 1
        assert loaded.data_warnings == ["truncated"]

    def test_load_missing_raises(self, tmp_store):
        with pytest.raises(FileNotFoundError):
            tmp_store.load("nonexistent")

    def test_list_projects_empty(self, tmp_store):
        assert tmp_store.list_projects() == []

    def test_list_projects(self, tmp_store, sample_state):
        tmp_store.save(sample_state)
        projects = tmp_store.list_projects()
        assert len(projects) == 1
        assert projects[0]["id"] == "test-project-1"
        assert projects[0]["name"] == "Test Project"

    def test_list_multiple(self, tmp_store):
        s1 = ProjectState(id="p1", name="Project 1")
        s2 = ProjectState(id="p2", name="Project 2")
        tmp_store.save(s1)
        tmp_store.save(s2)
        projects = tmp_store.list_projects()
        assert len(projects) == 2
        names = {p["name"] for p in projects}
        assert names == {"Project 1", "Project 2"}

    def test_overwrite(self, tmp_store, sample_state):
        tmp_store.save(sample_state)
        sample_state.name = "Updated Name"
        tmp_store.save(sample_state)
        loaded = tmp_store.load("test-project-1")
        assert loaded.name == "Updated Name"

    def test_delete(self, tmp_store, sample_state):
        tmp_store.save(sample_state)
        assert tmp_store.exists("test-project-1")
        assert tmp_store.delete("test-project-1") is True
        assert not tmp_store.exists("test-project-1")
        assert tmp_store.delete("test-project-1") is False

    def test_exists(self, tmp_store, sample_state):
        assert not tmp_store.exists("test-project-1")
        tmp_store.save(sample_state)
        assert tmp_store.exists("test-project-1")

    def test_invalid_id_raises(self, tmp_store):
        with pytest.raises(ValueError):
            tmp_store._path_for("")

    def test_round_trip_preserves_all_fields(self, tmp_store):
        """Full round-trip with a richly populated state."""
        from qc_clean.schemas.domain import (
            AnalysisMemo,
            AnalysisPhaseResult,
            CodeApplication,
            PipelineStatus,
            Provenance,
        )

        state = ProjectState(
            id="rich-project",
            name="Rich Project",
            corpus=Corpus(documents=[
                Document(id="d1", name="a.txt", content="content"),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="Code1", mention_count=5, confidence=0.8),
            ]),
            code_applications=[
                CodeApplication(code_id="C1", doc_id="d1", quote_text="q1"),
            ],
            memos=[AnalysisMemo(title="memo1", content="analysis")],
            phase_results=[
                AnalysisPhaseResult(phase_name="ingest", status=PipelineStatus.COMPLETED),
            ],
        )

        tmp_store.save(state)
        loaded = tmp_store.load("rich-project")

        assert loaded.corpus.documents[0].content == "content"
        assert loaded.codebook.codes[0].confidence == 0.8
        assert loaded.code_applications[0].quote_text == "q1"
        assert loaded.memos[0].title == "memo1"
        assert loaded.phase_results[0].status == PipelineStatus.COMPLETED
