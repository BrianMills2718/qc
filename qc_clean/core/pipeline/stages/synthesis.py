"""
Synthesis stage: wraps the current Phase 4 final synthesis & recommendations.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.analysis_schemas import AnalysisSynthesis
from qc_clean.schemas.adapters import analysis_synthesis_to_synthesis
from qc_clean.schemas.domain import ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class SynthesisStage(PipelineStage):

    def name(self) -> str:
        return "synthesis"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)
        phase1_text = config.get("_phase1_json", "{}")
        phase2_text = config.get("_phase2_json", "{}")
        phase3_text = config.get("_phase3_json", "{}")

        prompt = _build_phase4_prompt(combined_text, phase1_text, phase2_text, phase3_text)

        phase4_response = await llm.extract_structured(prompt, AnalysisSynthesis)
        state.synthesis = analysis_synthesis_to_synthesis(phase4_response)

        logger.info("Synthesis complete")
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


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
- Honest confidence assessments using the full 0.0-1.0 range"""
