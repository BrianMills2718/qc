"""
Relationship stage: wraps the current Phase 3 entity & relationship mapping.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.analysis_schemas import EntityMapping
from qc_clean.schemas.adapters import entity_mapping_to_entities
from qc_clean.schemas.domain import ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class RelationshipStage(PipelineStage):

    def name(self) -> str:
        return "relationship"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)
        phase1_text = config.get("_phase1_json", "{}")
        phase2_text = config.get("_phase2_json", "{}")

        prompt = _build_phase3_prompt(combined_text, phase1_text, phase2_text)

        phase3_response = await llm.extract_structured(prompt, EntityMapping)

        # Convert to domain entities
        doc_id = state.corpus.documents[0].id if state.corpus.documents else None
        entities, entity_rels = entity_mapping_to_entities(phase3_response, doc_id)
        state.entities = entities
        state.entity_relationships = entity_rels

        # Stash for downstream
        config["_phase3_json"] = phase3_response.model_dump_json(indent=2)

        logger.info(
            "Relationship mapping complete: %d entities, %d relationships",
            len(entities),
            len(entity_rels),
        )
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _build_phase3_prompt(
    combined_text: str,
    phase1_text: str,
    phase2_text: str,
) -> str:
    return f"""Identify key entities, concepts, and their relationships in the interview data.

INSTRUCTIONS:
1. Extract important entities (organizations, tools, concepts, methods, people)
2. Map meaningful relationships — only include relationships that have clear evidence in the text
3. Identify cause-effect chains grounded in what the interviewee(s) actually said
4. Limit to 10-15 most important relationships, not an exhaustive list
5. Relationship types should be specific verbs (e.g., "leads", "uses", "constrains") not vague labels

PREVIOUS ANALYSIS:
Phase 1 Codes: {phase1_text}
Phase 2 Speakers: {phase2_text}

INTERVIEW CONTENT:
{combined_text}

Provide focused entity relationship mapping."""
