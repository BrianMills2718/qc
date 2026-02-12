"""
Tests for the review UI API endpoints.

Uses FastAPI TestClient with a temp ProjectStore.
"""

import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from qc_clean.plugins.api.api_server import QCAPIServer
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    PipelineStatus,
    ProjectState,
    Provenance,
)


@pytest.fixture
def tmp_store(tmp_path):
    """A ProjectStore writing to a temp directory."""
    return ProjectStore(projects_dir=tmp_path)


@pytest.fixture
def review_project(tmp_store):
    """A saved project with codes and applications, paused for review."""
    codes = [
        Code(id="C1", name="Theme A", description="desc A", mention_count=5,
             confidence=0.82, example_quotes=["quote one", "quote two"]),
        Code(id="C2", name="Theme B", description="desc B", mention_count=3,
             confidence=0.65),
        Code(id="C3", name="Theme C", description="desc C", mention_count=1,
             confidence=0.30),
    ]
    apps = [
        CodeApplication(id="A1", code_id="C1", doc_id="d1", quote_text="evidence 1",
                        speaker="P1", confidence=0.85),
        CodeApplication(id="A2", code_id="C1", doc_id="d1", quote_text="evidence 2",
                        speaker="P2", confidence=0.78),
        CodeApplication(id="A3", code_id="C2", doc_id="d1", quote_text="evidence 3",
                        confidence=0.70),
        CodeApplication(id="A4", code_id="C3", doc_id="d1", quote_text="evidence 4",
                        confidence=0.40),
    ]
    state = ProjectState(
        id="test-project-123",
        name="Test Review Project",
        corpus=Corpus(documents=[Document(id="d1", name="interview1.txt", content="sample")]),
        codebook=Codebook(codes=codes),
        code_applications=apps,
        pipeline_status=PipelineStatus.PAUSED_FOR_REVIEW,
        current_phase="thematic_coding",
    )
    tmp_store.save(state)
    return state


@pytest.fixture
def client(tmp_store, review_project, monkeypatch):
    """FastAPI TestClient wired to the temp store."""
    # Patch ProjectStore so the server endpoints use our temp store
    monkeypatch.setattr(
        "qc_clean.core.persistence.project_store.DEFAULT_PROJECTS_DIR",
        tmp_store.projects_dir,
    )

    server = QCAPIServer(config={"background_processing_enabled": False})
    from fastapi import FastAPI
    server._app = FastAPI()
    server._register_default_endpoints()
    return TestClient(server._app)


class TestReviewUIPage:
    def test_serves_html(self, client):
        resp = client.get("/review/test-project-123")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "test-project-123" in resp.text
        assert "Code Review" in resp.text

    def test_404_for_missing_project(self, client):
        resp = client.get("/review/nonexistent")
        assert resp.status_code == 404


class TestReviewCodesEndpoint:
    def test_returns_codes_with_applications(self, client):
        resp = client.get("/projects/test-project-123/review/codes")
        assert resp.status_code == 200
        data = resp.json()

        assert data["project_id"] == "test-project-123"
        assert data["project_name"] == "Test Review Project"
        assert data["pipeline_status"] == "paused_for_review"
        assert data["summary"]["codes_count"] == 3
        assert data["summary"]["applications_count"] == 4

        codes = data["codes"]
        assert len(codes) == 3

        # Check first code has applications grouped
        c1 = next(c for c in codes if c["id"] == "C1")
        assert c1["name"] == "Theme A"
        assert c1["confidence"] == 0.82
        assert c1["provenance"] == "llm"
        assert len(c1["applications"]) == 2
        assert c1["applications"][0]["doc_name"] == "interview1.txt"
        assert c1["applications"][0]["speaker"] == "P1"

        # Code with no applications
        c3 = next(c for c in codes if c["id"] == "C3")
        assert len(c3["applications"]) == 1  # A4

    def test_404_for_missing_project(self, client):
        resp = client.get("/projects/nonexistent/review/codes")
        assert resp.status_code == 404


class TestReviewDecisionsEndpoint:
    def test_submit_decisions(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code", "target_id": "C1", "action": "approve", "rationale": "Good"},
                {"target_type": "code", "target_id": "C3", "action": "reject"},
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] == 2
        assert data["codes_remaining"] == 2  # C3 was rejected
        assert data["can_resume"] is True

    def test_decisions_persist(self, client, tmp_store):
        """Decisions should be saved to disk."""
        client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code", "target_id": "C2", "action": "modify",
                 "new_value": {"name": "Theme B (revised)"}},
            ]
        })
        # Reload from disk
        state = tmp_store.load("test-project-123")
        c2 = state.codebook.get_code("C2")
        assert c2.name == "Theme B (revised)"
        assert c2.provenance == Provenance.HUMAN

    def test_merge_decision(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code", "target_id": "C3", "action": "merge",
                 "new_value": {"merge_into": "C1"}},
            ]
        })
        assert resp.status_code == 200
        state = tmp_store.load("test-project-123")
        assert state.codebook.get_code("C3") is None
        # A4 should now point to C1
        a4 = next(a for a in state.code_applications if a.id == "A4")
        assert a4.code_id == "C1"

    def test_split_decision(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code", "target_id": "C1", "action": "split",
                 "new_value": {"new_codes": [
                     {"id": "C1a", "name": "Theme A1"},
                     {"id": "C1b", "name": "Theme A2"},
                 ]}},
            ]
        })
        assert resp.status_code == 200
        state = tmp_store.load("test-project-123")
        assert state.codebook.get_code("C1") is None
        assert state.codebook.get_code("C1a") is not None
        assert state.codebook.get_code("C1b") is not None

    def test_application_decision(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code_application", "target_id": "A2", "action": "reject"},
            ]
        })
        assert resp.status_code == 200
        state = tmp_store.load("test-project-123")
        assert all(a.id != "A2" for a in state.code_applications)

    def test_empty_decisions(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": []
        })
        assert resp.status_code == 200
        assert resp.json()["applied"] == 0

    def test_404_for_missing_project(self, client):
        resp = client.post("/projects/nonexistent/review/decisions", json={
            "decisions": []
        })
        assert resp.status_code == 404


class TestApproveAllEndpoint:
    def test_approve_all(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/approve-all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] == 3
        assert data["can_resume"] is True

        # Verify all codes are now human-approved
        state = tmp_store.load("test-project-123")
        for code in state.codebook.codes:
            assert code.provenance == Provenance.HUMAN

    def test_404_for_missing_project(self, client):
        resp = client.post("/projects/nonexistent/review/approve-all")
        assert resp.status_code == 404


class TestLegacyReviewEndpoint:
    def test_legacy_post_still_works(self, client):
        """The old POST /projects/{id}/review should still work."""
        resp = client.post("/projects/test-project-123/review", json={
            "decisions": [
                {"target_type": "code", "target_id": "C1", "action": "approve"},
            ]
        })
        assert resp.status_code == 200
        assert resp.json()["applied"] == 1
