"""
Thematic coding stage: wraps the current Phase 1 logic.
Produces a Codebook + CodeApplications from the corpus.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.analysis_schemas import CodeHierarchy
from qc_clean.schemas.adapters import (
    code_hierarchy_to_applications,
    code_hierarchy_to_codebook,
)
from qc_clean.schemas.domain import ProjectState
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class ThematicCodingStage(PipelineStage):

    def __init__(self, pause_for_review: bool = False):
        self._pause_for_review = pause_for_review

    def name(self) -> str:
        return "thematic_coding"

    def requires_human_review(self) -> bool:
        return self._pause_for_review

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)
        num_interviews = state.corpus.num_documents

        prompt = _build_phase1_prompt(combined_text, num_interviews)

        phase1_response = await llm.extract_structured(prompt, CodeHierarchy)

        # Convert to domain model
        codebook = code_hierarchy_to_codebook(phase1_response)
        state.codebook = codebook

        # Build applications from all docs
        all_applications = []
        for doc in state.corpus.documents:
            apps = code_hierarchy_to_applications(
                phase1_response, doc.id, codebook.version
            )
            all_applications.extend(apps)
        state.code_applications = all_applications

        # Stash raw response in config for downstream stages
        config["_phase1_json"] = phase1_response.model_dump_json(indent=2)

        logger.info(
            "Thematic coding complete: %d codes, %d applications",
            len(codebook.codes),
            len(all_applications),
        )
        return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _build_phase1_prompt(combined_text: str, num_interviews: int) -> str:
    return f"""You are a qualitative researcher analyzing {num_interviews} interview(s) to discover thematic codes.

ANALYTIC QUESTION: What are the key themes, patterns, and insights in these interviews?

CRITICAL INSTRUCTIONS:
1. Read through ALL interview content comprehensively
2. Distinguish between INTERVIEWER QUESTIONS and INTERVIEWEE RESPONSES — only code the interviewee's statements, not the interviewer's framing questions
3. Create a hierarchical code structure with up to 3 levels
4. Target 10-15 total codes (5-7 top-level themes with selective sub-codes). Merge overlapping themes rather than creating near-duplicates
5. Each code MUST have these fields:
   - id: Unique ID in CAPS_WITH_UNDERSCORES format
   - name: Clear human-readable name
   - description: 2-3 sentences explaining the code
   - semantic_definition: Clear definition of what qualifies for this code
   - parent_id: ID of parent code (null for top-level codes)
   - level: Hierarchy level (0=top, 1=sub, 2=detailed)
   - example_quotes: 1-3 VERBATIM quotes from the INTERVIEWEE (not the interviewer)
   - mention_count: Count how many distinct times this theme is mentioned or referenced across the interview(s). Be precise — count actual mentions, not estimates
   - discovery_confidence: Float 0.0-1.0 using the FULL range:
     * 0.0-0.3: Weakly supported (mentioned once, tangentially)
     * 0.3-0.6: Moderately supported (mentioned a few times, some detail)
     * 0.6-0.8: Strongly supported (discussed substantively, with examples)
     * 0.8-1.0: Very strongly supported (major theme with extensive discussion)

6. Hierarchy: Level 0 = main themes, Level 1 = sub-themes, Level 2 = detailed codes
7. Codes must be mutually distinct — if two codes would share >50% of their supporting quotes, merge them

INTERVIEW CONTENT:
{combined_text}

Generate a complete hierarchical taxonomy of codes."""
