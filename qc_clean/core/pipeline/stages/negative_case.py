"""
Negative case analysis stage.

After coding is complete, asks the LLM to identify data that contradicts
or doesn't fit the emerging categories. Produces an analytical memo with
disconfirming evidence. Addresses Lincoln & Guba's credibility criterion.
"""

from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel, Field

from qc_clean.schemas.domain import AnalysisMemo, ProjectState, Provenance
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class NegativeCase(BaseModel):
    """A piece of data that contradicts or doesn't fit the emerging categories."""
    code_name: str = Field(description="The code/category being challenged")
    disconfirming_evidence: str = Field(description="Quote or data that contradicts this code")
    explanation: str = Field(description="Why this evidence challenges the code")
    implication: str = Field(description="What this means for the analysis")


class NegativeCaseResponse(BaseModel):
    """LLM response for negative case analysis."""
    negative_cases: List[NegativeCase] = Field(
        description="Cases that contradict or don't fit the emerging categories"
    )
    overall_assessment: str = Field(
        description="Overall assessment of how well the codebook fits the data"
    )
    analytical_memo: str = Field(
        default="",
        description="Analytical memo: record your reasoning, uncertainties, and emerging patterns",
    )


class NegativeCaseStage(PipelineStage):

    def name(self) -> str:
        return "negative_case_analysis"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)
        codes_text = _format_codebook(state)

        prompt = f"""You are a qualitative researcher conducting negative case analysis — a critical step for ensuring the credibility and trustworthiness of qualitative findings (Lincoln & Guba, 1985).

Given the codebook developed from the interview data, your task is to ACTIVELY SEARCH FOR data that:
1. Contradicts the emerging categories or themes
2. Doesn't fit neatly into any existing code
3. Presents alternative explanations for the observed patterns
4. Shows exceptions to the patterns identified

CURRENT CODEBOOK:
{codes_text}

INTERVIEW DATA:
{combined_text}

For each negative case found:
- Identify which code/category is being challenged
- Provide the specific disconfirming evidence (verbatim quote or paraphrase)
- Explain WHY this evidence challenges the code
- Describe what this means for the analysis (should the code be revised? Is it a boundary condition? Does it suggest a new category?)

Also provide an overall assessment of how well the current codebook fits the data. Be honest — if the codes fit well, say so. If there are significant gaps or forced fits, flag them.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

        response = await llm.extract_structured(prompt, NegativeCaseResponse)

        # Build memo content
        memo_parts = []
        memo_parts.append(f"## Overall Assessment\n\n{response.overall_assessment}")

        if response.negative_cases:
            memo_parts.append("## Negative Cases\n")
            for nc in response.negative_cases:
                memo_parts.append(f"### {nc.code_name}")
                memo_parts.append(f"**Evidence**: {nc.disconfirming_evidence}")
                memo_parts.append(f"**Challenge**: {nc.explanation}")
                memo_parts.append(f"**Implication**: {nc.implication}")
                memo_parts.append("")

        state.memos.append(AnalysisMemo(
            memo_type="negative_case",
            title="Negative Case Analysis",
            content="\n\n".join(memo_parts),
            code_refs=[nc.code_name for nc in response.negative_cases],
            doc_refs=[d.id for d in state.corpus.documents],
            created_by=Provenance.LLM,
        ))

        # Extract analytical memo
        if response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="methodological",
                title="Negative Case Analysis Memo",
                content=response.analytical_memo,
            ))

        logger.info(
            "Negative case analysis complete: %d cases found",
            len(response.negative_cases),
        )
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _format_codebook(state: ProjectState) -> str:
    lines = []
    for code in state.codebook.codes:
        lines.append(f"- {code.name}: {code.description}")
        if code.reasoning:
            lines.append(f"  Reasoning: {code.reasoning}")
    return "\n".join(lines)
