"""
Grounded Theory selective coding stage.
"""

from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from typing import List

from qc_clean.core.workflow.grounded_theory import CoreCategory
from qc_clean.schemas.adapters import core_category_to_domain
from qc_clean.schemas.domain import ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class CoreCategoriesResponse(BaseModel):
    core_categories: List[CoreCategory] = Field(
        description="List of core categories identified"
    )


class GTSelectiveCodingStage(PipelineStage):

    def name(self) -> str:
        return "gt_selective_coding"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        codes_text = config.get("_gt_open_codes_text", "")
        axial_text = config.get("_gt_axial_text", "")

        prompt = f"""You are conducting selective coding in grounded theory methodology to identify the core categories.

Given these open codes and axial relationships, identify the CORE CATEGORY or CATEGORIES that:
1. Have the most analytical power and explanatory capability
2. Appear frequently and significantly in the data
3. Relate meaningfully to other major categories
4. Can integrate and explain the central phenomenon

Note: Complex phenomena may require multiple core categories for complete explanation.

Open Codes:
{codes_text}

Axial Relationships:
{axial_text}

For each core category, provide:
1. Clear name and definition
2. The central phenomenon it explains
3. How it relates to other major categories
4. Its theoretical properties
5. Why it has explanatory power
6. Rationale for why this is a core integrating category

The core categories should be the central organizing concepts for your emerging theory."""

        response = await llm.extract_structured(prompt, CoreCategoriesResponse)

        state.core_categories = [
            core_category_to_domain(cc)
            for cc in response.core_categories
        ]

        # Stash for downstream
        config["_gt_core_categories"] = response.core_categories
        config["_gt_core_text"] = "\n".join(
            f"- {cc.category_name}: {cc.definition}"
            for cc in response.core_categories
        )

        logger.info(
            "GT selective coding complete: %d core categories",
            len(state.core_categories),
        )
        return state
