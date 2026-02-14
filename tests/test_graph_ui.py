"""
Tests for graph visualization feature.

Covers:
- Graph data endpoint response shapes
- Graph UI HTML rendering
- Edge/node construction from ProjectState
"""

import pytest

from qc_clean.plugins.api.graph_ui import render_graph_page
from qc_clean.schemas.domain import (
    Code,
    Codebook,
    CodeRelationship,
    Corpus,
    Document,
    DomainEntityRelationship,
    Entity,
    Methodology,
    ProjectConfig,
    ProjectState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state_with_graph_data() -> ProjectState:
    """Create a state with codes, relationships, and entities."""
    state = ProjectState(
        name="graph_test",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[
            Document(id="d1", name="doc1.txt", content="Test content"),
        ]),
        codebook=Codebook(codes=[
            Code(id="THEME_A", name="Theme A", description="First theme",
                 level=0, mention_count=5, confidence=0.9,
                 example_quotes=["quote 1", "quote 2"]),
            Code(id="SUB_A1", name="Sub A1", description="Sub-theme of A",
                 level=1, parent_id="THEME_A", mention_count=3, confidence=0.7),
            Code(id="THEME_B", name="Theme B", description="Second theme",
                 level=0, mention_count=4, confidence=0.8),
        ]),
        code_relationships=[
            CodeRelationship(
                source_code_id="THEME_A",
                target_code_id="THEME_B",
                relationship_type="influences",
                strength=0.7,
                evidence=["evidence 1"],
            ),
        ],
        entities=[
            Entity(id="e1", name="AI", entity_type="technology",
                   description="Artificial Intelligence"),
            Entity(id="e2", name="Workflow", entity_type="concept",
                   description="Work processes"),
        ],
        entity_relationships=[
            DomainEntityRelationship(
                entity_1_id="e1",
                entity_2_id="e2",
                relationship_type="transforms",
                strength=0.8,
            ),
        ],
    )
    return state


def _build_code_graph_response(state: ProjectState) -> dict:
    """Simulate the code graph endpoint response."""
    nodes = []
    for code in state.codebook.codes:
        nodes.append({
            "id": code.id,
            "name": code.name,
            "description": code.description,
            "level": code.level,
            "mention_count": code.mention_count,
            "confidence": code.confidence,
            "example_quotes": code.example_quotes[:3],
            "parent_id": code.parent_id,
        })

    code_ids = {c.id for c in state.codebook.codes}
    hierarchy_edges = []
    for code in state.codebook.codes:
        if code.parent_id and code.parent_id in code_ids:
            hierarchy_edges.append({
                "source": code.parent_id,
                "target": code.id,
            })

    relationship_edges = []
    for rel in state.code_relationships:
        relationship_edges.append({
            "source": rel.source_code_id,
            "target": rel.target_code_id,
            "type": rel.relationship_type,
            "strength": rel.strength,
        })

    return {
        "project_name": state.name,
        "nodes": nodes,
        "hierarchy_edges": hierarchy_edges,
        "relationship_edges": relationship_edges,
    }


def _build_entity_graph_response(state: ProjectState) -> dict:
    """Simulate the entity graph endpoint response."""
    nodes = []
    for ent in state.entities:
        nodes.append({
            "id": ent.id,
            "name": ent.name,
            "type": ent.entity_type,
            "description": ent.description,
        })

    edges = []
    for rel in state.entity_relationships:
        edges.append({
            "source": rel.entity_1_id,
            "target": rel.entity_2_id,
            "type": rel.relationship_type,
            "strength": rel.strength,
        })

    return {
        "project_name": state.name,
        "nodes": nodes,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Graph UI HTML tests
# ---------------------------------------------------------------------------

class TestGraphUI:

    def test_render_graph_page(self):
        html = render_graph_page("test-project-123")
        assert "test-project-123" in html
        assert "cytoscape" in html.lower()
        assert "Code Hierarchy" in html
        assert "Code Relationships" in html
        assert "Entity Map" in html

    def test_graph_page_has_download_button(self):
        html = render_graph_page("proj1")
        assert "Download PNG" in html

    def test_graph_page_has_search(self):
        html = render_graph_page("proj1")
        assert "searchInput" in html
        assert "searchNodes" in html


# ---------------------------------------------------------------------------
# Graph data endpoint tests
# ---------------------------------------------------------------------------

class TestCodeGraphEndpoint:

    def test_code_nodes(self):
        state = _make_state_with_graph_data()
        resp = _build_code_graph_response(state)
        assert len(resp["nodes"]) == 3
        names = {n["name"] for n in resp["nodes"]}
        assert "Theme A" in names
        assert "Sub A1" in names
        assert "Theme B" in names

    def test_hierarchy_edges(self):
        state = _make_state_with_graph_data()
        resp = _build_code_graph_response(state)
        assert len(resp["hierarchy_edges"]) == 1
        edge = resp["hierarchy_edges"][0]
        assert edge["source"] == "THEME_A"
        assert edge["target"] == "SUB_A1"

    def test_relationship_edges(self):
        state = _make_state_with_graph_data()
        resp = _build_code_graph_response(state)
        assert len(resp["relationship_edges"]) == 1
        edge = resp["relationship_edges"][0]
        assert edge["type"] == "influences"
        assert edge["strength"] == 0.7

    def test_node_has_required_fields(self):
        state = _make_state_with_graph_data()
        resp = _build_code_graph_response(state)
        node = resp["nodes"][0]
        assert "id" in node
        assert "name" in node
        assert "level" in node
        assert "mention_count" in node
        assert "confidence" in node

    def test_empty_codebook(self):
        state = ProjectState()
        resp = _build_code_graph_response(state)
        assert resp["nodes"] == []
        assert resp["hierarchy_edges"] == []
        assert resp["relationship_edges"] == []

    def test_orphan_parent_id_not_in_hierarchy(self):
        """If parent_id references a non-existent code, no edge should be created."""
        state = ProjectState(
            codebook=Codebook(codes=[
                Code(id="C1", name="Code 1", parent_id="NONEXISTENT"),
            ]),
        )
        resp = _build_code_graph_response(state)
        assert len(resp["nodes"]) == 1
        assert len(resp["hierarchy_edges"]) == 0


class TestEntityGraphEndpoint:

    def test_entity_nodes(self):
        state = _make_state_with_graph_data()
        resp = _build_entity_graph_response(state)
        assert len(resp["nodes"]) == 2
        names = {n["name"] for n in resp["nodes"]}
        assert "AI" in names
        assert "Workflow" in names

    def test_entity_edges(self):
        state = _make_state_with_graph_data()
        resp = _build_entity_graph_response(state)
        assert len(resp["edges"]) == 1
        edge = resp["edges"][0]
        assert edge["type"] == "transforms"
        assert edge["strength"] == 0.8

    def test_entity_node_fields(self):
        state = _make_state_with_graph_data()
        resp = _build_entity_graph_response(state)
        node = resp["nodes"][0]
        assert "id" in node
        assert "name" in node
        assert "type" in node
        assert "description" in node

    def test_empty_entities(self):
        state = ProjectState()
        resp = _build_entity_graph_response(state)
        assert resp["nodes"] == []
        assert resp["edges"] == []
