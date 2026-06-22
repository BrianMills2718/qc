"""
Synthesis stage: wraps the current Phase 4 final synthesis & recommendations.
"""

from __future__ import annotations

import logging

from qc_clean.core.claims import claims_for_synthesis, replace_claims_for_stage
from qc_clean.core.prompting import format_untrusted_data_block, format_untrusted_documents
from qc_clean.schemas.analysis_schemas import AnalysisSynthesis
from qc_clean.schemas.adapters import analysis_synthesis_to_synthesis
from qc_clean.schemas.domain import AnalysisMemo, ProjectState
from ..pipeline_engine import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


class SynthesisStage(PipelineStage):

    def name(self) -> str:
        return "synthesis"

    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        logger.info(
            "Starting synthesis: docs=%d, codes=%d, entities=%d, model=%s",
            state.corpus.num_documents, len(state.codebook.codes),
            len(state.entities), ctx.model_name,
        )
        llm = LLMHandler(model_name=ctx.model_name)

        combined_text = _build_combined_text(state)
        phase1_text = format_untrusted_data_block(
            "Phase 1 code hierarchy JSON",
            ctx.require("phase1_json", self.name()),
        )
        phase2_text = format_untrusted_data_block(
            "Phase 2 perspective analysis JSON",
            ctx.require("phase2_json", self.name()),
        )
        phase3_text = format_untrusted_data_block(
            "Phase 3 relationship mapping JSON",
            ctx.require("phase3_json", self.name()),
        )

        prompt = _build_phase4_prompt(combined_text, phase1_text, phase2_text, phase3_text)

        phase4_response = await llm.extract_structured(
            prompt, AnalysisSynthesis, **ctx.llm_call_options(self.name())
        )
        state.synthesis = analysis_synthesis_to_synthesis(phase4_response)

        # Extract analytical memo
        if phase4_response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="theoretical",
                title="Synthesis & Recommendations Memo",
                content=phase4_response.analytical_memo,
                code_refs=[c.id for c in state.codebook.codes],
            ))

        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_synthesis(state, self.name()),
            no_claims_reason="synthesis produced no findings, patterns, recommendations, or confidence claims",
        )

        logger.info("Synthesis complete")
        return state


def _build_combined_text(state: ProjectState) -> str:
    return format_untrusted_documents(state.corpus.documents, label_prefix="Interview")


def _build_phase4_prompt(
    combined_text: str,
    phase1_text: str,
    phase2_text: str,
    phase3_text: str,
) -> str:
    return f"""Synthesize all analysis phases into a final qualitative coding report.

CRITICAL RULES:
- Do NOT invent statistics, percentages, or numeric estimates that are not directly stated in the interviews
- Do NOT use language like "~70% prevalence" or "estimated frequency: 80%" — these are fabricated
- Instead, use qualitative descriptors: "frequently discussed", "mentioned once", "a major theme", "briefly touched on"
- The executive_summary should be 2-4 sentences, not a full paragraph
- Key findings should cite specific evidence from interviews
- Recommendations should be specific to the interview content, not generic consulting advice

COMPREHENSIVE ANALYSIS FROM PREVIOUS PHASES:
Phase 1 - Hierarchical Codes: {phase1_text}
Phase 2 - Speaker Analysis: {phase2_text}
Phase 3 - Entity Relationships: {phase3_text}

ORIGINAL INTERVIEW CONTENT:
{combined_text}

Provide final qualitative coding analysis with:
- Executive summary (2-4 sentences)
- Key findings with VERBATIM evidence (no fabricated statistics)
- Cross-cutting patterns
- Specific, actionable recommendations grounded in interview content
- Honest confidence assessments using the full 0.0-1.0 range

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""
