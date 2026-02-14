"""
Grounded Theory axial coding stage.
"""

from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from typing import List

from qc_clean.schemas.gt_schemas import AxialRelationship
from qc_clean.schemas.adapters import axial_relationships_to_code_relationships
from qc_clean.schemas.domain import AnalysisMemo, ProjectState
from ..pipeline_engine import PipelineStage, require_config

logger = logging.getLogger(__name__)


class AxialRelationshipsResponse(BaseModel):
    axial_relationships: List[AxialRelationship] = Field(
        description="List of axial relationships identified"
    )
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class GTAxialCodingStage(PipelineStage):

    def __init__(self, pause_for_review: bool = False):
        self._pause_for_review = pause_for_review

    def name(self) -> str:
        return "gt_axial_coding"

    def requires_human_review(self) -> bool:
        return self._pause_for_review

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        logger.info(
            "Starting gt_axial_coding: codes=%d, model=%s",
            len(state.codebook.codes), model_name,
        )
        llm = LLMHandler(model_name=model_name)

        codes_text = require_config(config, "_gt_open_codes_text", self.name())
        combined_text = _build_combined_text(state)

        prompt = f"""You are conducting axial coding analysis in grounded theory methodology.

Given these open codes from the previous phase, identify relationships between categories:

Open Codes:
{codes_text}

For each significant relationship, identify:
1. The central category in this relationship
2. Related categories that connect to it
3. Type of relationship (causal, contextual, intervening, etc.)
4. Conditions that influence this relationship
5. Consequences that result from this relationship
6. Supporting evidence from the data
7. Strength of the relationship

Focus on the paradigm model:
- Causal conditions (what leads to the phenomenon)
- Context (specific conditions)
- Intervening conditions (broad conditions)
- Action/interaction strategies (responses)
- Consequences (outcomes)

Original Interview Data:
{combined_text}

Identify the key relationships that help explain the phenomena in the data.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

        response = await llm.extract_structured(prompt, AxialRelationshipsResponse)
        axial_rels = response.axial_relationships

        # Convert to domain code relationships
        code_rels = axial_relationships_to_code_relationships(axial_rels, state.codebook)
        state.code_relationships = code_rels

        # Extract analytical memo
        if response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="methodological",
                title="Axial Coding Memo",
                content=response.analytical_memo,
                code_refs=[c.id for c in state.codebook.codes],
            ))

        # Stash for downstream
        config["_gt_axial_relationships"] = axial_rels
        config["_gt_axial_text"] = _format_relationships(axial_rels)

        logger.info("GT axial coding complete: %d relationships", len(axial_rels))
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _format_relationships(rels: list) -> str:
    formatted = []
    for rel in rels:
        text = f"- {rel.central_category} -> {rel.related_category}\n"
        text += f"  Type: {rel.relationship_type}\n"
        text += f"  Strength: {rel.strength:.2f}"
        formatted.append(text)
    return "\n\n".join(formatted)
