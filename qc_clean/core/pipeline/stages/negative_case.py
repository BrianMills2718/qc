"""
Negative case analysis stage.

After coding is complete, asks the LLM to identify data that contradicts
or doesn't fit the emerging categories. Produces an analytical memo with
disconfirming evidence. Addresses Lincoln & Guba's credibility criterion.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from pydantic import BaseModel, Field

from qc_clean.core.claims import (
    claims_for_negative_cases,
    disconfirmation_targets,
    format_disconfirmation_targets,
    replace_claims_for_stage,
)
from qc_clean.core.disconfirmation import (
    anchor_for_candidate,
    format_disconfirmation_candidates,
    retrieve_disconfirmation_candidates,
)
from qc_clean.core.prompting import format_untrusted_data_block
from qc_clean.schemas.domain import AnalysisMemo, ProjectState, Provenance
from ..pipeline_engine import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


class NegativeCase(BaseModel):
    """A piece of data that contradicts or doesn't fit the emerging categories."""
    code_name: str = Field(description="The code/category being challenged")
    target_claim_id: Optional[str] = Field(
        default=None,
        description="Exact claim_id being challenged when the evidence contradicts a listed claim-ledger target",
    )
    candidate_id: Optional[str] = Field(
        default=None,
        description="Exact retrieved candidate_id containing the disconfirming evidence",
    )
    disconfirming_evidence: str = Field(description="Quote or data that contradicts this code")
    explanation: str = Field(description="Why this evidence challenges the code")
    implication: str = Field(default="", description="What this means for the analysis")


class NegativeCaseResponse(BaseModel):
    """LLM response for negative case analysis."""
    negative_cases: List[NegativeCase] = Field(
        default_factory=list,
        description="Cases that contradict or don't fit the emerging categories",
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

    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        disconfirmation_model = ctx.disconfirmation_model_name or ctx.model_name
        logger.info(
            "Starting negative_case_analysis: codes=%d, docs=%d, model=%s",
            len(state.codebook.codes), state.corpus.num_documents, disconfirmation_model,
        )
        llm = LLMHandler(model_name=disconfirmation_model)

        codes_text = format_untrusted_data_block("Current codebook", _format_codebook(state))
        cross_claims = _format_cross_interview_claims(state)
        target_claims = disconfirmation_targets(
            state,
            limit=ctx.disconfirmation_max_targets,
        )
        raw_ledger_targets = format_disconfirmation_targets(
            state,
            limit=ctx.disconfirmation_max_targets,
        )
        ledger_targets = (
            format_untrusted_data_block("Claim ledger targets", raw_ledger_targets)
            if raw_ledger_targets
            else ""
        )
        candidates = retrieve_disconfirmation_candidates(
            state,
            target_claims,
            candidates_per_claim=ctx.disconfirmation_candidates_per_claim,
        )
        candidate_anchors = {
            candidate.id: anchor_for_candidate(candidate)
            for candidate in candidates
        }
        candidate_section = format_disconfirmation_candidates(candidates)
        retrieval_summary = (
            f"Retrieved {len(candidates)} candidate passage(s) for "
            f"{len(target_claims)} claim target(s). "
            f"Interpretation model: {disconfirmation_model}."
        )

        # When cross-interview analysis has run, disconfirmation must cover those
        # final claims too, not only the codebook (INV-6). The section is omitted
        # for single-document corpora where no cross-interview stage ran.
        cross_section = (
            f"\n\nCROSS-INTERVIEW CLAIMS TO ALSO CHALLENGE (consensus / divergent themes "
            "asserted across interviews — test whether the data actually supports them):\n"
            f"{format_untrusted_data_block('Cross-interview claims memo', cross_claims)}"
            if cross_claims
            else ""
        )
        ledger_section = (
            f"\n\n{ledger_targets}\n\nIf a negative case challenges one of these ledger targets, "
            "copy that exact claim_id into target_claim_id."
            if ledger_targets
            else ""
        )

        prompt = f"""You are an adversarial qualitative methods reviewer conducting negative case analysis — a critical step for testing the credibility and trustworthiness of qualitative findings (Lincoln & Guba, 1985).

Adversarial here means skeptical and evidence-bound: actively look for exceptions, boundary conditions, and contradictions in the retrieved source candidates, but do not fabricate evidence and do not overstate weak candidates.

Given the codebook, any cross-interview claims, and the RETRIEVED CANDIDATE PASSAGES below, your task is to assess whether the retrieved source passages contain data that:
1. Contradicts the emerging categories, themes, or cross-interview claims
2. Doesn't fit neatly into any existing code
3. Presents alternative explanations for the observed patterns
4. Shows exceptions to the patterns identified

CURRENT CODEBOOK:
{codes_text}{cross_section}{ledger_section}

RETRIEVAL-FIRST SOURCE CANDIDATES:
{candidate_section}

For each negative case found:
- If it challenges a listed claim-ledger target, copy that target's exact claim_id into target_claim_id
- If it uses a retrieved candidate passage, copy that candidate's exact candidate_id into candidate_id
- Identify which code/category is being challenged
- Provide the specific disconfirming evidence (verbatim quote or paraphrase)
- Explain WHY this evidence challenges the code
- Describe what this means for the analysis (should the code be revised? Is it a boundary condition? Does it suggest a new category?)

Assess only the retrieved candidate passages. If the retrieved candidates do not support a negative case, return an empty negative_cases list and say that no retrieved candidate was sufficient. Do not infer that no contrary evidence exists outside the retrieved candidates.

Also provide an overall assessment of how well the current codebook fits the retrieved candidate evidence. Be honest — if the candidates do not challenge the codes or claims, say so. If there are significant gaps or forced fits, flag them.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- How the retrieved candidates affected the assessment
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""

        response = await llm.extract_structured(
            prompt, NegativeCaseResponse, **ctx.llm_call_options(self.name())
        )

        # Build memo content
        memo_parts = []
        memo_parts.append(f"## Retrieval-First Candidate Search\n\n{retrieval_summary}")
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

        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_negative_cases(
                state,
                response.negative_cases,
                self.name(),
                candidate_anchors=candidate_anchors,
            ),
            no_claims_reason="negative-case analysis found no disconfirming cases",
        )

        logger.info(
            "Negative case analysis complete: %d cases found",
            len(response.negative_cases),
        )
        return state

def _format_codebook(state: ProjectState) -> str:
    lines = []
    for code in state.codebook.codes:
        lines.append(f"- {code.name}: {code.description}")
        if code.reasoning:
            lines.append(f"  Reasoning: {code.reasoning}")
    return "\n".join(lines)


def _format_cross_interview_claims(state: ProjectState) -> str:
    """Return the most recent cross-interview claim memo, or "" if none.

    Cross-interview analysis stores consensus / divergent themes as a
    ``cross_case`` memo. Surfacing it here lets negative-case analysis challenge
    the final cross-interview claims, not only the codebook (INV-6).
    """
    cross_memos = [m for m in state.memos if m.memo_type == "cross_case"]
    if not cross_memos:
        return ""
    return cross_memos[-1].content
