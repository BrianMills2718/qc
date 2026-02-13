"""
Grounded Theory theory integration stage.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.gt_schemas import TheoreticalModel
from qc_clean.schemas.adapters import theoretical_model_to_domain
from qc_clean.schemas.domain import AnalysisMemo, ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class GTTheoryIntegrationStage(PipelineStage):

    def name(self) -> str:
        return "gt_theory_integration"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.core_categories) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        codes_text = config.get("_gt_open_codes_text", "")
        axial_text = config.get("_gt_axial_text", "")
        core_text = config.get("_gt_core_text", "")

        prompt = f"""You are completing grounded theory analysis by integrating all phases into a coherent theoretical model.

Based on the complete analysis:

Core Categories: {core_text}

Open Codes: {codes_text}

Axial Relationships: {axial_text}

Develop a comprehensive theoretical model that includes:
1. Name for the theoretical model
2. The core category and its central role
3. Theoretical framework that explains the phenomenon
4. Key theoretical propositions (if-then statements)
5. Major conceptual relationships
6. Scope conditions (when/where theory applies)
7. Implications of the theory
8. Suggested future research directions

Create a theory that is:
- Grounded in the data analyzed
- Conceptually clear and well-integrated
- Has explanatory and predictive power
- Connects to broader theoretical understanding

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

        response = await llm.extract_structured(prompt, TheoreticalModel)
        state.theoretical_model = theoretical_model_to_domain(response)

        # Extract analytical memo
        if response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="theoretical",
                title="Theory Integration Memo",
                content=response.analytical_memo,
            ))

        logger.info(
            "GT theory integration complete: %s",
            state.theoretical_model.model_name,
        )
        return state
