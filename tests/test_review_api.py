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
    AnalyticClaim,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    Code,
    CodeApplication,
    CodeRelationship,
    Codebook,
    Corpus,
    CorpusScope,
    DomainEntityRelationship,
    Document,
    Entity,
    PipelineStatus,
    ProjectState,
    Provenance,
    ClaimAdjudicationStatus,
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
        corpus_scope=CorpusScope(
            phenomenon="AI workflow adoption",
            population="Clinic staff",
            sampling_frame="Pilot clinic interviewees",
            inclusion_criteria=["Participated in the pilot"],
            exclusion_criteria=["Vendors"],
            notes="Scope fixture.",
        ),
        codebook=Codebook(codes=codes),
        code_applications=apps,
        code_relationships=[
            CodeRelationship(
                id="CR1",
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="supports",
                strength=0.7,
                evidence=["evidence 1"],
            )
        ],
        entities=[
            Entity(id="E1", name="Scheduler", entity_type="tool"),
            Entity(id="E2", name="Front desk", entity_type="team"),
        ],
        entity_relationships=[
            DomainEntityRelationship(
                id="ER1",
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="used_by",
                strength=0.8,
                supporting_evidence=["evidence 2"],
            )
        ],
        claims=[
            AnalyticClaim(
                id="claim-review-api",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Theme A is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            )
        ],
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


def _replace_with_two_claims(tmp_store, review_project):
    """Replace the review fixture claim ledger with two ordered claims."""
    review_project.claims = [
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
    tmp_store.save(review_project)


class TestReviewUIPage:
    def test_serves_html(self, client):
        resp = client.get("/review/test-project-123")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "test-project-123" in resp.text
        assert "Code Review" in resp.text

    def test_review_page_exposes_claim_review_ui(self, client):
        resp = client.get("/review/test-project-123")

        assert resp.status_code == 200
        assert 'id="claimModeBtn"' in resp.text
        assert '"/projects/" + PROJECT_ID + "/review/claims"' in resp.text
        assert "function renderClaimCard" in resp.text
        assert 'target_type: "claim"' in resp.text

    def test_review_page_exposes_relationship_review_ui(self, client):
        resp = client.get("/review/test-project-123")

        assert resp.status_code == 200
        assert 'id="relationshipModeBtn"' in resp.text
        assert '"/projects/" + PROJECT_ID + "/review/relationships"' in resp.text
        assert "function renderRelationshipCard" in resp.text
        assert "function setRelationshipDecision" in resp.text
        assert "target_type: relationship.target_type" in resp.text

    def test_review_page_exposes_negative_case_review_ui(self, client):
        resp = client.get("/review/test-project-123")

        assert resp.status_code == 200
        assert 'id="negativeCaseModeBtn"' in resp.text
        assert '"/projects/" + PROJECT_ID + "/review/negative-cases"' in resp.text
        assert "function renderNegativeCases" in resp.text
        assert "renderClaimCard(negativeCase)" in resp.text

    def test_review_page_exposes_orientation_aids(self, client):
        resp = client.get("/review/test-project-123")

        assert resp.status_code == 200
        assert "Start here" in resp.text
        assert "What to inspect" in resp.text
        assert "This is a software review surface" in resp.text
        assert 'title="Review code labels, descriptions, and example quotes."' in resp.text
        assert "function renderModeHelp" in resp.text
        assert "function actionTooltip" in resp.text
        assert "Evidence anchors" in resp.text

    def test_review_page_exposes_anchor_detail_rendering(self, client):
        resp = client.get("/review/test-project-123")

        assert resp.status_code == 200
        assert "function renderAnchorDetails" in resp.text
        assert "contrary_anchor_details" in resp.text
        assert "supporting_anchor_details" in resp.text

    def test_404_for_missing_project(self, client):
        resp = client.get("/review/nonexistent")
        assert resp.status_code == 404


class TestClaimLedgerEndpoint:
    def test_get_project_claims_includes_disconfirmation_summary(self, client):
        resp = client.get("/projects/test-project-123/claims")

        assert resp.status_code == 200
        data = resp.json()
        assert data["claim_summary"]["total_claims"] == 1
        assert data["disconfirmation_summary"]["total_targets"] == 1
        assert data["disconfirmation_summary"]["unchallenged_targets"] == 1

    def test_get_project_claims_includes_limit_metadata(self, client):
        resp = client.get("/projects/test-project-123/claims")

        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] == 1
        assert data["total_claims"] == 1
        assert data["limit"] == 100
        assert data["offset"] == 0

    def test_get_project_claims_limit_parameter(
        self, client, tmp_store, review_project
    ):
        _replace_with_two_claims(tmp_store, review_project)

        limited = client.get("/projects/test-project-123/claims?limit=1")
        negative = client.get("/projects/test-project-123/claims?limit=-5")

        assert limited.status_code == 200
        limited_data = limited.json()
        assert limited_data["returned"] == 1
        assert limited_data["total_claims"] == 2
        assert limited_data["limit"] == 1
        assert limited_data["claims"][0]["id"] == "claim-1"

        assert negative.status_code == 200
        negative_data = negative.json()
        assert negative_data["returned"] == 0
        assert negative_data["total_claims"] == 2
        assert negative_data["limit"] == 0
        assert negative_data["claims"] == []

    def test_get_project_claims_offset_parameter(
        self, client, tmp_store, review_project
    ):
        _replace_with_two_claims(tmp_store, review_project)

        resp = client.get("/projects/test-project-123/claims?limit=1&offset=1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] == 1
        assert data["total_claims"] == 2
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert data["claims"][0]["id"] == "claim-2"

    def test_get_project_claims_offset_bounds(
        self, client, tmp_store, review_project
    ):
        _replace_with_two_claims(tmp_store, review_project)

        negative = client.get("/projects/test-project-123/claims?limit=1&offset=-5")
        beyond_end = client.get("/projects/test-project-123/claims?limit=1&offset=99")

        assert negative.status_code == 200
        negative_data = negative.json()
        assert negative_data["returned"] == 1
        assert negative_data["total_claims"] == 2
        assert negative_data["limit"] == 1
        assert negative_data["offset"] == 0
        assert negative_data["claims"][0]["id"] == "claim-1"

        assert beyond_end.status_code == 200
        beyond_end_data = beyond_end.json()
        assert beyond_end_data["returned"] == 0
        assert beyond_end_data["total_claims"] == 2
        assert beyond_end_data["limit"] == 1
        assert beyond_end_data["offset"] == 99
        assert beyond_end_data["claims"] == []

    def test_get_project_claims_includes_anchor_details(
        self, client, tmp_store, review_project
    ):
        review_project.claims[0].supporting_anchors = [
            ClaimAnchor(
                doc_id="d1",
                start_char=0,
                end_char=12,
                quote_text="support text",
                quote_hash="support-hash",
                code_application_id="A1",
            )
        ]
        review_project.claims[0].contrary_anchors = [
            ClaimAnchor(
                doc_id="d1",
                start_char=20,
                end_char=35,
                quote_text="contrary text",
                quote_hash="contrary-hash",
            )
        ]
        tmp_store.save(review_project)

        resp = client.get("/projects/test-project-123/claims")

        assert resp.status_code == 200
        claim = resp.json()["claims"][0]
        assert claim["supporting_anchors"] == 1
        assert claim["contrary_anchors"] == 1
        assert claim["supporting_anchor_details"][0] == {
            "doc_id": "d1",
            "start_char": 0,
            "end_char": 12,
            "quote_hash": "support-hash",
            "quote_text": "support text",
            "segment_id": None,
            "code_application_id": "A1",
        }
        assert claim["contrary_anchor_details"][0]["quote_text"] == "contrary text"

    def test_get_project_claims_includes_scope(self, client):
        resp = client.get("/projects/test-project-123/claims")

        assert resp.status_code == 200
        claim = resp.json()["claims"][0]
        assert claim["scope"]["code_ids"] == ["C1"]
        assert claim["scope"]["corpus_level"] is False


class TestInvalidProjectIDBoundaries:
    @pytest.mark.parametrize("invalid_id", ["test-project-123!", "%2E%2E%2Ftest-project-123"])
    def test_invalid_project_ids_return_404_without_aliasing_existing_project(
        self, client, tmp_store, invalid_id
    ):
        original_scope = tmp_store.load("test-project-123").corpus_scope.model_dump()

        read_responses = [
            client.get(f"/projects/{invalid_id}/claims"),
            client.get(f"/projects/{invalid_id}/review/codes"),
        ]
        mutation_response = client.put(
            f"/projects/{invalid_id}/scope",
            json={
                "phenomenon": "Should not write",
                "population": "Should not write",
            },
        )

        for response in [*read_responses, mutation_response]:
            assert response.status_code == 404

        loaded = tmp_store.load("test-project-123")
        assert loaded.corpus_scope.model_dump() == original_scope


class TestCorpusScopeEndpoint:
    def test_get_project_scope_returns_current_scope(self, client):
        resp = client.get("/projects/test-project-123/scope")

        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-project-123"
        assert data["is_set"] is True
        assert data["scope"]["phenomenon"] == "AI workflow adoption"
        assert data["scope"]["population"] == "Clinic staff"
        assert data["scope"]["inclusion_criteria"] == ["Participated in the pilot"]

    def test_put_project_scope_updates_scope(self, client, tmp_store):
        resp = client.put("/projects/test-project-123/scope", json={
            "phenomenon": "AI scheduling adoption",
            "population": "Front desk staff",
            "sampling_frame": "Two pilot clinics",
            "inclusion_criteria": ["Used the scheduling tool"],
            "exclusion_criteria": ["No direct scheduling work"],
            "notes": "Updated through API.",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["scope"]["phenomenon"] == "AI scheduling adoption"
        assert data["scope"]["population"] == "Front desk staff"
        loaded = tmp_store.load("test-project-123")
        assert loaded.corpus_scope is not None
        assert loaded.corpus_scope.sampling_frame == "Two pilot clinics"
        assert loaded.corpus_scope.notes == "Updated through API."


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


class TestReviewClaimsEndpoint:
    def test_returns_claims_for_review(self, client):
        resp = client.get("/projects/test-project-123/review/claims")

        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-project-123"
        assert data["project_name"] == "Test Review Project"
        assert data["pipeline_status"] == "paused_for_review"
        assert data["summary"]["claims_count"] == 1
        assert data["returned"] == 1
        assert data["total_claims"] == 1
        claim = data["claims"][0]
        assert claim["id"] == "claim-review-api"
        assert claim["kind"] == "code"
        assert claim["source_stage"] == "thematic_coding"
        assert claim["support_status"] == "needs_anchor"
        assert claim["adjudication_status"] == "pending"
        assert claim["claim_text"] == "Theme A is a code."
        assert claim["scope"]["code_ids"] == ["C1"]
        assert claim["origin_object_type"] == "code"
        assert claim["origin_object_id"] == "C1"
        assert claim["supporting_anchors"] == 0
        assert claim["contrary_anchors"] == 0
        assert claim["revision_history_count"] == 0
        assert claim["created_by"] == "llm"

    def test_review_claims_limit_offset(self, client, tmp_store, review_project):
        review_project.claims = [
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
        tmp_store.save(review_project)

        resp = client.get("/projects/test-project-123/review/claims?limit=1&offset=1")

        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] == 1
        assert data["total_claims"] == 2
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert data["claims"][0]["id"] == "claim-2"

    def test_404_for_missing_project(self, client):
        resp = client.get("/projects/nonexistent/review/claims")
        assert resp.status_code == 404


class TestReviewNegativeCasesEndpoint:
    def test_returns_negative_cases_for_review(self, client, tmp_store, review_project):
        review_project.claims = [
            AnalyticClaim(
                id="claim-normal",
                claim_kind=ClaimKind.CODE,
                source_stage="thematic_coding",
                claim_text="Theme A is a code.",
                scope=ClaimScope(code_ids=["C1"]),
                origin_object_type="code",
                origin_object_id="C1",
            ),
            AnalyticClaim(
                id="neg-1",
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Negative case for Theme A: counterexample.",
                scope=ClaimScope(claim_ids=["claim-normal"], code_ids=["C1"]),
                origin_object_type="negative_case",
                origin_object_id="negative_case:0:Theme A",
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id="d1",
                        start_char=7,
                        end_char=29,
                        quote_text="counterexample evidence",
                        quote_hash="abc123",
                        code_application_id="A1",
                    )
                ],
            ),
        ]
        tmp_store.save(review_project)

        resp = client.get("/projects/test-project-123/review/negative-cases")

        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-project-123"
        assert data["returned"] == 1
        assert data["total_negative_cases"] == 1
        negative_case = data["negative_cases"][0]
        assert negative_case["id"] == "neg-1"
        assert negative_case["kind"] == "negative_case"
        assert negative_case["scope"]["claim_ids"] == ["claim-normal"]
        assert negative_case["scope"]["code_ids"] == ["C1"]
        assert negative_case["claim_text"] == "Negative case for Theme A: counterexample."
        assert negative_case["contrary_anchors"] == 1
        assert negative_case["contrary_anchor_details"] == [
            {
                "doc_id": "d1",
                "start_char": 7,
                "end_char": 29,
                "quote_hash": "abc123",
                "quote_text": "counterexample evidence",
                "segment_id": None,
                "code_application_id": "A1",
            }
        ]

    def test_review_negative_cases_limit_offset(
        self, client, tmp_store, review_project
    ):
        review_project.claims = [
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
        tmp_store.save(review_project)

        resp = client.get(
            "/projects/test-project-123/review/negative-cases?limit=1&offset=1"
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] == 1
        assert data["total_negative_cases"] == 2
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert data["negative_cases"][0]["id"] == "neg-2"

    def test_404_for_missing_project(self, client):
        resp = client.get("/projects/nonexistent/review/negative-cases")
        assert resp.status_code == 404


class TestReviewRelationshipsEndpoint:
    def test_returns_relationships_for_review(self, client):
        resp = client.get("/projects/test-project-123/review/relationships")

        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == "test-project-123"
        assert data["project_name"] == "Test Review Project"
        assert data["pipeline_status"] == "paused_for_review"
        assert data["summary"]["relationships_count"] == 2
        assert data["returned"] == 2
        assert data["total_relationships"] == 2
        code_rel = data["relationships"][0]
        assert code_rel["target_type"] == "code_relationship"
        assert code_rel["id"] == "CR1"
        assert code_rel["source_name"] == "Theme A"
        assert code_rel["target_name"] == "Theme B"
        assert code_rel["relationship_type"] == "supports"
        assert code_rel["evidence_count"] == 1
        entity_rel = data["relationships"][1]
        assert entity_rel["target_type"] == "entity_relationship"
        assert entity_rel["id"] == "ER1"
        assert entity_rel["source_name"] == "Scheduler"
        assert entity_rel["target_name"] == "Front desk"
        assert entity_rel["relationship_type"] == "used_by"
        assert entity_rel["evidence_count"] == 1

    def test_review_relationships_limit_offset(self, client):
        resp = client.get(
            "/projects/test-project-123/review/relationships?limit=1&offset=1"
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["returned"] == 1
        assert data["total_relationships"] == 2
        assert data["limit"] == 1
        assert data["offset"] == 1
        assert data["relationships"][0]["id"] == "ER1"

    def test_404_for_missing_project(self, client):
        resp = client.get("/projects/nonexistent/review/relationships")
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

    def test_claim_decision_persists(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {
                    "target_type": "claim",
                    "target_id": "claim-review-api",
                    "action": "approve",
                    "rationale": "Reviewed against source evidence.",
                },
            ]
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] == 1
        assert data["claims_count"] == 1
        state = tmp_store.load("test-project-123")
        claim = state.claims[0]
        assert claim.adjudication_status == ClaimAdjudicationStatus.RETAINED
        assert claim.revision_history[-1].action == "approve"
        assert claim.revision_history[-1].rationale == "Reviewed against source evidence."

    def test_relationship_decision_persists(self, client, tmp_store):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {
                    "target_type": "code_relationship",
                    "target_id": "CR1",
                    "action": "modify",
                    "rationale": "Reviewer narrowed the relation.",
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
                    "rationale": "Entity link was unsupported.",
                },
            ]
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["applied"] == 2
        assert data["relationships_count"] == 1
        state = tmp_store.load("test-project-123")
        assert len(state.entity_relationships) == 0
        assert len(state.code_relationships) == 1
        rel = state.code_relationships[0]
        assert rel.relationship_type == "moderates"
        assert rel.strength == 0.9
        assert rel.evidence == ["reviewed evidence"]

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

    def test_rejects_missing_decision_fields(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [{}]
        })
        assert resp.status_code == 422

    def test_rejects_invalid_action(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "code", "target_id": "C1", "action": "invalid_action"},
            ]
        })
        assert resp.status_code == 422

    def test_rejects_non_list_decisions(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": "not-list"
        })
        assert resp.status_code == 422

    def test_rejects_unsupported_target_type(self, client):
        resp = client.post("/projects/test-project-123/review/decisions", json={
            "decisions": [
                {"target_type": "not_a_target", "target_id": "C1", "action": "approve"},
            ]
        })
        assert resp.status_code == 400
        assert "Unknown target_type" in resp.json()["detail"]


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

    def test_legacy_post_rejects_invalid_payload(self, client):
        resp = client.post("/projects/test-project-123/review", json={
            "decisions": [{}]
        })
        assert resp.status_code == 422
