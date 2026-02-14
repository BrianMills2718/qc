"""
Grounded Theory selective coding stage.
"""

from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from typing import List

from qc_clean.schemas.gt_schemas import CoreCategory
from qc_clean.schemas.adapters import core_category_to_domain
from qc_clean.schemas.domain import AnalysisMemo, ProjectState
from ..pipeline_engine import PipelineStage, require_config

logger = logging.getLogger(__name__)


class CoreCategoriesResponse(BaseModel):
    core_categories: List[CoreCategory] = Field(
        description="List of core categories identified"
    )
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class GTSelectiveCodingStage(PipelineStage):

    def name(self) -> str:
        return "gt_selective_coding"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        logger.info(
            "Starting gt_selective_coding: codes=%d, relationships=%d, model=%s",
            len(state.codebook.codes), len(state.code_relationships), model_name,
        )
        llm = LLMHandler(model_name=model_name)

        codes_text = require_config(config, "_gt_open_codes_text", self.name())
        axial_text = require_config(config, "_gt_axial_text", self.name())

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

The core categories should be the central organizing concepts for your emerging theory.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

        response = await llm.extract_structured(prompt, CoreCategoriesResponse)

        state.core_categories = [
            core_category_to_domain(cc)
            for cc in response.core_categories
        ]

        # Extract analytical memo
        if response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="theoretical",
                title="Selective Coding Memo",
                content=response.analytical_memo,
                code_refs=[cc.category_name for cc in response.core_categories],
            ))

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
