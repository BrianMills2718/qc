from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.plugins.api.api_server import QCAPIServer
from qc_clean.schemas.domain import (
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
