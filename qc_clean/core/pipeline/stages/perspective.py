"""
Perspective stage: wraps the current Phase 2 speaker/participant analysis.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.analysis_schemas import SpeakerAnalysis
from qc_clean.schemas.adapters import speaker_analysis_to_perspectives
from qc_clean.schemas.domain import ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class PerspectiveStage(PipelineStage):

    def name(self) -> str:
        return "perspective"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)
        phase1_text = config.get("_phase1_json", "{}")
        num_interviews = state.corpus.num_documents

        # Determine single vs multi-speaker from detected speakers, not doc count.
        # A single document can be a multi-speaker focus group.
        all_speakers = []
        for doc in state.corpus.documents:
            for s in doc.detected_speakers:
                if s not in all_speakers:
                    all_speakers.append(s)
        is_single_speaker = len(all_speakers) <= 1

        prompt = _build_phase2_prompt(
            combined_text, phase1_text, num_interviews, is_single_speaker
        )

        phase2_response = await llm.extract_structured(prompt, SpeakerAnalysis)
        state.perspective_analysis = speaker_analysis_to_perspectives(phase2_response)

        # Stash for downstream
        config["_phase2_json"] = phase2_response.model_dump_json(indent=2)

        logger.info(
            "Perspective analysis complete: %d participants",
            len(state.perspective_analysis.participants),
        )
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _build_phase2_prompt(
    combined_text: str,
    phase1_text: str,
    num_interviews: int,
    is_single_speaker: bool,
) -> str:
    if is_single_speaker:
        return f"""Analyze the single interview participant's perspective in depth.

CRITICAL: This is a SINGLE-SPEAKER interview. Do NOT fabricate consensus or disagreement between multiple people.

INSTRUCTIONS:
1. Identify the speaker by name and role from the interview content
2. Analyze their perspective in relation to the discovered codes
3. For "codes_emphasized": list ONLY the top 5-7 code IDs this speaker discusses MOST, not every code
4. For "consensus_themes": list the speaker's strongest, most consistent positions (things they state firmly and repeatedly)
5. For "divergent_viewpoints": identify any INTERNAL tensions, ambivalences, or contradictions within the speaker's OWN views (e.g., "sees AI as useful but worries about IP"). If there are none, return an empty list — do NOT fabricate tensions
6. For "perspective_mapping": map the speaker's name to their top 5-7 most emphasized code IDs

PHASE 1 CODES (for reference):
{phase1_text}

INTERVIEW CONTENT:
{combined_text}

Provide detailed single-speaker analysis."""
    else:
        return f"""Analyze the different participant perspectives across {num_interviews} interviews.

INSTRUCTIONS:
1. Identify each distinct speaker by name and role
2. Analyze how different perspectives relate to the discovered codes
3. For "codes_emphasized": list ONLY the top 5-7 code IDs each speaker discusses MOST
4. For "consensus_themes": identify genuine areas where multiple speakers AGREE
5. For "divergent_viewpoints": identify genuine areas where speakers DISAGREE or hold different positions
6. For "perspective_mapping": map each speaker's name to their top 5-7 most emphasized code IDs

PHASE 1 CODES (for reference):
{phase1_text}

INTERVIEW CONTENT:
{combined_text}

Provide detailed multi-speaker analysis."""
