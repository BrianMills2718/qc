"""
Thematic coding stage: wraps the current Phase 1 logic.
Produces a Codebook + CodeApplications from the corpus.
"""

from __future__ import annotations

import logging

from typing import List

from qc_clean.schemas.analysis_schemas import CodeHierarchy
from qc_clean.schemas.adapters import code_hierarchy_to_codebook
from qc_clean.schemas.domain import AnalysisMemo, CodeApplication, Document, ProjectState, Provenance
from ..pipeline_engine import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


class ThematicCodingStage(PipelineStage):

    def __init__(self, pause_for_review: bool = False):
        self._pause_for_review = pause_for_review

    def name(self) -> str:
        return "thematic_coding"

    def requires_human_review(self) -> bool:
        return self._pause_for_review

    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        logger.info(
            "Starting thematic_coding: docs=%d, model=%s",
            state.corpus.num_documents, ctx.model_name,
        )
        llm = LLMHandler(model_name=ctx.model_name)

        combined_text = _build_combined_text(state)
        num_interviews = state.corpus.num_documents

        if ctx.prompt_overrides.get("thematic_coding"):
            # Use the override prompt, substituting {combined_text} and {num_interviews}
            prompt = ctx.prompt_overrides["thematic_coding"].format(
                combined_text=combined_text, num_interviews=num_interviews,
            )
            logger.info("Using prompt override for thematic_coding (%d chars)", len(prompt))
        else:
            prompt = _build_phase1_prompt(combined_text, num_interviews)

        if ctx.irr_prompt_suffix:
            prompt = prompt + "\n\n" + ctx.irr_prompt_suffix

        phase1_response = await llm.extract_structured(prompt, CodeHierarchy)

        # Convert to domain model
        codebook = code_hierarchy_to_codebook(phase1_response)
        state.codebook = codebook

        # Build applications, matching quotes to source documents.
        # The LLM produced codes from all docs combined, so we match each
        # quote to the document(s) it actually appears in.
        all_applications = []
        for tc in phase1_response.codes:
            for quote in tc.example_quotes:
                matched_docs = _match_quote_to_docs(quote, state.corpus.documents)
                if not matched_docs:
                    # Fallback: if no exact match, assign to first doc
                    matched_docs = [state.corpus.documents[0].id]
                for doc_id in matched_docs:
                    app = CodeApplication(
                        code_id=tc.id,
                        doc_id=doc_id,
                        quote_text=quote,
                        confidence=tc.discovery_confidence,
                        applied_by=Provenance.LLM,
                        codebook_version=codebook.version,
                    )
                    all_applications.append(app)
        state.code_applications = all_applications

        # Extract analytical memo
        if phase1_response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="coding",
                title="Thematic Coding Analysis Memo",
                content=phase1_response.analytical_memo,
                code_refs=[c.id for c in state.codebook.codes],
            ))

        # Stash raw response for downstream stages
        ctx.phase1_json = phase1_response.model_dump_json(indent=2)

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
   - reasoning: 1-2 sentences explaining WHY you created this code — what analytical decision led to it, what data pattern you noticed

6. Hierarchy: Level 0 = main themes, Level 1 = sub-themes, Level 2 = detailed codes
7. Codes must be mutually distinct — if two codes would share >50% of their supporting quotes, merge them

INTERVIEW CONTENT:
{combined_text}

Generate a complete hierarchical taxonomy of codes.

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation"""


def _match_quote_to_docs(quote: str, documents: List[Document]) -> List[str]:
    """Match a quote to the document(s) it appears in.

    Uses substring matching with a normalized version of the quote.
    Returns a list of matching document IDs (usually 1).
    """
    # Normalize for fuzzy matching: lowercase, collapse whitespace
    import re
    norm_quote = re.sub(r"\s+", " ", quote.lower().strip())

    # Use a shorter snippet for matching (LLM may paraphrase edges)
    # Take middle 60% of the quote for more reliable matching
    if len(norm_quote) > 40:
        start = len(norm_quote) // 5
        end = len(norm_quote) * 4 // 5
        search_snippet = norm_quote[start:end]
    else:
        search_snippet = norm_quote

    matched = []
    for doc in documents:
        norm_content = re.sub(r"\s+", " ", doc.content.lower())
        if search_snippet in norm_content:
            matched.append(doc.id)

    return matched
