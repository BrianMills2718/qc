from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.plugins.api.api_server import QCAPIServer
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimRelationship,
    ClaimScope,
    Code,
    CodeRelationship,
    Codebook,
    Corpus,
    Document,
    DomainEntityRelationship,
    Entity,
    Methodology,
    ProjectConfig,
    ProjectState,
)


@pytest.fixture
def tmp_store(tmp_path):
    return ProjectStore(projects_dir=tmp_path)


@pytest.fixture
def client(tmp_store, monkeypatch):
    monkeypatch.setattr(
        "qc_clean.core.persistence.project_store.DEFAULT_PROJECTS_DIR",
        tmp_store.projects_dir,
    )
    server = QCAPIServer(config={"background_processing_enabled": False})
    server._app = FastAPI()
    server._register_default_endpoints()
    return TestClient(server._app)


def test_graph_codes_endpoint_returns_relationship_edges_for_thematic_state(tmp_store, client):
    state = ProjectState(
        id="graph-api-1",
        name="Graph API",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[Document(id="d1", name="doc.txt", content="sample")]),
        codebook=Codebook(codes=[
            Code(id="C1", name="Code 1", description="desc"),
            Code(id="C2", name="Code 2", description="desc"),
        ]),
        code_relationships=[
            CodeRelationship(
                source_code_id="C1",
                target_code_id="C2",
                relationship_type="supports",
                strength=0.7,
            )
        ],
    )
    tmp_store.save(state)

    resp = client.get("/projects/graph-api-1/graph/codes")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["relationship_edges"] == [
        {"source": "C1", "target": "C2", "type": "supports", "strength": 0.7}
    ]
    assert "empty_reason" not in payload


def test_graph_endpoint_explains_unavailable_relationship_surface_when_missing(tmp_store, client):
    state = ProjectState(
        id="graph-api-2",
        name="Graph API Empty",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[Document(id="d1", name="doc.txt", content="sample")]),
        codebook=Codebook(codes=[Code(id="C1", name="Code 1", description="desc")]),
        entities=[
            Entity(id="E1", name="AI", entity_type="technology"),
            Entity(id="E2", name="Workflow", entity_type="concept"),
        ],
        entity_relationships=[
            DomainEntityRelationship(
                entity_1_id="E1",
                entity_2_id="E2",
                relationship_type="transforms",
                strength=0.8,
            )
        ],
    )
    tmp_store.save(state)

    resp = client.get("/projects/graph-api-2/graph/codes")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["relationship_edges"] == []
    assert payload["empty_reason"] == (
        "No supported code-to-code relationships were produced for this project yet."
    )


def test_graph_claims_endpoint_returns_claim_nodes_and_relationship_edges(tmp_store, client):
    state = ProjectState(
        id="graph-api-claims",
        name="Claim Graph API",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[Document(id="d1", name="doc.txt", content="sample")]),
        claims=[
            AnalyticClaim(
                id="claim-1",
                claim_kind=ClaimKind.PERSPECTIVE,
                source_stage="perspective",
                claim_text="Alice sees AI as useful with guardrails.",
                scope=ClaimScope(participant_names=["Alice"]),
                origin_object_type="participant_perspective",
                origin_object_id="Alice",
            ),
            AnalyticClaim(
                id="claim-2",
                claim_kind=ClaimKind.CROSS_CASE,
                source_stage="cross_interview",
                claim_text="Participants converge on the position: AI should be governed.",
                scope=ClaimScope(corpus_level=True, participant_names=["Alice", "Bob"]),
                origin_object_type="cross_interview_perspective_consensus",
                origin_object_id="perspective_consensus:0",
            ),
        ],
        claim_relationships=[
            ClaimRelationship(
                id="rel-1",
                source_stage="cross_interview",
                source_claim_id="claim-2",
                target_claim_id="claim-1",
                relationship_type="synthesizes",
                rationale="Cross-case synthesis summarizes a participant-level claim.",
            )
        ],
    )
    tmp_store.save(state)

    resp = client.get("/projects/graph-api-claims/graph/claims")
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload["nodes"]) == 2
    assert payload["edges"] == [
        {
            "id": "rel-1",
            "source": "claim-2",
            "target": "claim-1",
            "type": "synthesizes",
            "rationale": "Cross-case synthesis summarizes a participant-level claim.",
        }
    ]
    assert "empty_reason" not in payload


def test_graph_ui_page_exposes_claim_graph_tab(client, tmp_store):
    state = ProjectState(
        id="graph-ui-claims",
        name="Graph UI Claims",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
    )
    tmp_store.save(state)

    resp = client.get("/graph/graph-ui-claims")
    assert resp.status_code == 200
    assert 'data-view="claims"' in resp.text
    assert "/projects/\" + PROJECT_ID + \"/graph/claims" in resp.text
