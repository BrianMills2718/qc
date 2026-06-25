"""Tests for RelationshipStage — thematic code relationship extraction.

Verifies that the relationship stage correctly maps LLM EntityMapping output to
domain CodeRelationship and DomainEntityRelationship objects in ProjectState.

# mock-ok: LLM calls are mocked to avoid external API calls in deterministic tests.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.schemas.analysis_schemas import (
    CodeRelationshipCandidate,
    EntityMapping,
    EntityRelationship,
)
from qc_clean.schemas.domain import (
    Code,
    Codebook,
    CodeRelationship,
    Corpus,
    Document,
    DomainEntityRelationship,
    Methodology,
    ProjectConfig,
    ProjectState,
)
from qc_clean.core.pipeline.pipeline_engine import PipelineContext


def _make_state(codes: list[Code] | None = None) -> ProjectState:
    """Minimal ProjectState with a codebook."""
    doc = Document(id="d1", name="interview.txt", content="Some interview content.")
    cb = Codebook(codes=codes or [
        Code(id="C1", name="Barriers", description="Adoption barriers"),
        Code(id="C2", name="Support", description="Support structures"),
        Code(id="C3", name="Outcomes", description="Observed outcomes"),
    ])
    return ProjectState(
        id="rel-test",
        name="Relationship Test",
        config=ProjectConfig(methodology=Methodology.DEFAULT),
        corpus=Corpus(documents=[doc]),
        codebook=cb,
    )


def _make_ctx(phase1_json: str = "{}", phase2_json: str = "{}") -> PipelineContext:
    ctx = PipelineContext(model_name="test-model")
    ctx.phase1_json = phase1_json
    ctx.phase2_json = phase2_json
    return ctx


def _mock_entity_mapping(
    code_rels: list[CodeRelationshipCandidate] | None = None,
    entity_rels: list[EntityRelationship] | None = None,
) -> EntityMapping:
    return EntityMapping(
        entities=["entity_a", "entity_b"],
        relationships=entity_rels or [
            EntityRelationship(
                entity_1="entity_a",
                entity_2="entity_b",
                relationship_type="collaborates_with",
                strength=0.8,
                supporting_evidence=["They worked together."],
            ),
        ],
        code_relationships=code_rels or [
            CodeRelationshipCandidate(
                source_code="C1",
                target_code="C2",
                relationship_type="constrains",
                strength=0.75,
                supporting_evidence=["Barriers constrain support structures."],
            ),
            CodeRelationshipCandidate(
                source_code="C2",
                target_code="C3",
                relationship_type="enables",
                strength=0.8,
                supporting_evidence=["Support enables outcomes."],
            ),
        ],
        analytical_memo="Thematic relationships identified.",
    )


def _run_stage(state: ProjectState, ctx: PipelineContext, mapping: EntityMapping) -> ProjectState:
    """Run the RelationshipStage with a mocked LLM response."""
    from qc_clean.core.pipeline.stages.relationship import RelationshipStage

    meta = SimpleNamespace(
        model="test-model",
        cost=0.0,
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    )
    stage = RelationshipStage()

    with patch(
        "qc_clean.core.llm.llm_handler.acall_llm_structured",
        new_callable=AsyncMock,
        return_value=(mapping, meta),
    ):
        return asyncio.run(stage.execute(state, ctx))


class TestRelationshipStageCodeRelationships:
    def test_relationship_stage_populates_thematic_code_relationships(self):
        """Default thematic relationship stage writes state.code_relationships from structured output."""
        state = _make_state()
        ctx = _make_ctx()
        mapping = _mock_entity_mapping()

        result = _run_stage(state, ctx, mapping)

        assert len(result.code_relationships) == 2
        cr0 = result.code_relationships[0]
        assert isinstance(cr0, CodeRelationship)
        # source/target resolve through the codebook (C1, C2 are valid code IDs)
        assert cr0.source_code_id in {"C1", "C2", "C3"}
        assert cr0.target_code_id in {"C1", "C2", "C3"}
        assert cr0.relationship_type in {"constrains", "enables"}

    def test_relationship_stage_preserves_entity_relationships(self):
        """Entity relationships persist correctly alongside code relationship extraction."""
        state = _make_state()
        ctx = _make_ctx()
        mapping = _mock_entity_mapping()

        result = _run_stage(state, ctx, mapping)

        assert len(result.entity_relationships) >= 1
        er0 = result.entity_relationships[0]
        assert isinstance(er0, DomainEntityRelationship)
        assert er0.relationship_type == "collaborates_with"
        # Code relationships are still populated
        assert len(result.code_relationships) == 2
