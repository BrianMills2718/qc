"""
Thematic coding stage: wraps the current Phase 1 logic.
Produces a Codebook + CodeApplications from the corpus.
"""

from __future__ import annotations

import logging

from qc_clean.core.claims import (
    claims_for_code_applications,
    claims_for_codes,
    replace_claims_for_stage,
)
from qc_clean.core.grounding import MatchStatus, resolve_and_anchor, warn_unanchored as _warn_unanchored
from qc_clean.core.prompting import (
    format_untrusted_data_block,
    format_untrusted_documents,
    render_prompt_override,
)
from qc_clean.core.prompt_override_registry import get_prompt_override_surface
from qc_clean.schemas.analysis_schemas import CodeHierarchy
from qc_clean.schemas.adapters import code_hierarchy_to_codebook
from qc_clean.schemas.domain import (
    AnalysisMemo,
    CodeApplication,
    GroundingIssue,
    GroundingIssueStatus,
    ProjectState,
    Provenance,
)
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
        if ctx.exhaustive_coding:
            return await self._execute_exhaustive(state, ctx)
        return await self._execute_example_quotes(state, ctx)

    async def _execute_example_quotes(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        logger.info(
            "Starting thematic_coding: docs=%d, model=%s",
            state.corpus.num_documents, ctx.model_name,
        )
        llm = LLMHandler(model_name=ctx.model_name)

        combined_text = _build_combined_text(state)
        num_interviews = state.corpus.num_documents

        if ctx.prompt_overrides.get("thematic_coding"):
            surface = get_prompt_override_surface("thematic_coding")
            # Use the override prompt, substituting {combined_text} and {num_interviews}
            prompt = render_prompt_override(
                stage_name=surface.stage_name,
                template=ctx.prompt_overrides["thematic_coding"],
                required_placeholders=surface.required_data_placeholders,
                values={
                    "combined_text": combined_text,
                    "num_interviews": num_interviews,
                },
                optional_data_placeholders=surface.optional_data_placeholders,
                metadata_placeholders=surface.metadata_placeholders,
            )
            logger.info("Using prompt override for thematic_coding (%d chars)", len(prompt))
        else:
            prompt = _build_phase1_prompt(combined_text, num_interviews)

        if ctx.irr_prompt_suffix:
            prompt = prompt + "\n\n" + ctx.irr_prompt_suffix

        phase1_response = await llm.extract_structured(
            prompt, CodeHierarchy, **ctx.llm_call_options(self.name())
        )

        # Convert to domain model
        codebook = code_hierarchy_to_codebook(phase1_response)
        state.codebook = codebook

        # Build applications, matching quotes to source documents.
        # The LLM produced codes from all docs combined, so we match each
        # quote to the document(s) it actually appears in.
        all_applications = []
        unresolvable = 0
        ambiguous = 0
        for tc in phase1_response.codes:
            for quote in tc.example_quotes:
                app, match = resolve_and_anchor(
                    quote, state.corpus.documents,
                    code_id=tc.id, codebook_version=codebook.version,
                    confidence=tc.discovery_confidence,
                    segments=state.segments,
                    allow_fuzzy=False,
                )
                if app is not None:
                    all_applications.append(app)
                elif match.status is MatchStatus.AMBIGUOUS:
                    ambiguous += 1  # occurs >1x -> can't uniquely anchor (INV-1)
                    state.grounding_issues.append(_grounding_issue(
                        stage_name=self.name(),
                        code_id=tc.id,
                        quote=quote,
                        status=GroundingIssueStatus.AMBIGUOUS_MATCH,
                        occurrence_count=match.total_occurrences,
                    ))
                else:
                    unresolvable += 1  # no source match -> drop (INV-1)
                    state.grounding_issues.append(_grounding_issue(
                        stage_name=self.name(),
                        code_id=tc.id,
                        quote=quote,
                        status=GroundingIssueStatus.NO_SOURCE_MATCH,
                        occurrence_count=match.total_occurrences,
                    ))
        state.code_applications = all_applications
        _warn_unanchored(state, unresolvable, ambiguous, label="Thematic coding")

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
        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_codes(state, self.name())
            + claims_for_code_applications(state, self.name()),
            no_claims_reason="thematic coding produced no codes or applications",
        )

        logger.info(
            "Thematic coding complete: %d codes, %d applications",
            len(codebook.codes),
            len(all_applications),
        )
        return state

    async def _execute_exhaustive(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        """Exhaustive coding: one batched call renders a decision for EVERY segment.

        Closes INV-8 (examined-and-judged coverage) and INV-1 (applications anchor
        directly to segment offsets — no fuzzy matching). Segments with no code are
        recorded as 'no_code' (examined, not relevant), distinct from 'not examined'.
        """
        from qc_clean.core.llm.llm_handler import LLMHandler
        from qc_clean.core.grounding import quote_hash
        from qc_clean.core.segmentation import segment_corpus
        from qc_clean.schemas.analysis_schemas import CodeHierarchy, ExhaustiveCodingResponse

        if not state.segments:
            state.segments = segment_corpus(state.corpus.documents)
        segments = state.segments
        if not segments:
            raise RuntimeError("Exhaustive coding requires segments but the corpus produced none.")

        logger.info(
            "Starting exhaustive thematic_coding: docs=%d, segments=%d, model=%s",
            state.corpus.num_documents, len(segments), ctx.model_name,
        )
        llm = LLMHandler(model_name=ctx.model_name)

        prompt = _build_exhaustive_prompt(segments)
        if ctx.irr_prompt_suffix:
            prompt = prompt + "\n\n" + ctx.irr_prompt_suffix

        response = await llm.extract_structured(
            prompt, ExhaustiveCodingResponse, **ctx.llm_call_options(self.name())
        )

        # Codebook from discovered codes (reuse the thematic adapter).
        hierarchy = CodeHierarchy(codes=response.codes, total_codes=len(response.codes),
                                  analysis_confidence=response.analysis_confidence)
        codebook = code_hierarchy_to_codebook(hierarchy)
        state.codebook = codebook
        valid_code_ids = {c.id for c in codebook.codes}

        decisions_by_index = {d.segment_index: d for d in response.decisions}
        applications = []
        coded = no_code = 0
        for i, seg in enumerate(segments):
            d = decisions_by_index.get(i)
            applied = [cid for cid in d.code_ids if cid in valid_code_ids] if d else []
            if d is None:
                seg.decision = None  # the model skipped this segment (honest gap)
                continue
            if applied:
                seg.decision = "coded"
                coded += 1
                for code_id in applied:
                    applications.append(CodeApplication(
                        code_id=code_id,
                        doc_id=seg.doc_id,
                        quote_text=seg.text,
                        speaker=seg.speaker or None,
                        start_char=seg.start_char,
                        end_char=seg.end_char,
                        quote_hash=quote_hash(seg.text, 0, len(seg.text)),
                        applied_by=Provenance.LLM,
                        codebook_version=codebook.version,
                    ))
            else:
                seg.decision = "no_code"
                no_code += 1

        state.code_applications = applications
        examined = coded + no_code
        if examined < len(segments):
            state.data_warnings.append(
                f"Exhaustive coding: {len(segments) - examined} of {len(segments)} "
                f"segment(s) received no decision from the model (left 'not examined')."
            )

        if response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="coding",
                title="Exhaustive Thematic Coding Memo",
                content=response.analytical_memo,
                code_refs=[c.id for c in codebook.codes],
            ))

        # Stash the discovered codebook as phase1_json so downstream stages
        # (perspective/relationship/synthesis) that require it work identically
        # to the example-quote path. Without this, `project run --exhaustive`
        # crashes at the perspective stage on a default-methodology project.
        ctx.phase1_json = hierarchy.model_dump_json(indent=2)
        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_codes(state, self.name())
            + claims_for_code_applications(state, self.name()),
            no_claims_reason="exhaustive thematic coding produced no codes or applications",
        )

        logger.info(
            "Exhaustive coding complete: %d codes, %d/%d segments examined "
            "(%d coded, %d no-code), %d applications",
            len(codebook.codes), examined, len(segments), coded, no_code, len(applications),
        )
        return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_exhaustive_prompt(segments) -> str:
    """Prompt for exhaustive coding: discover codes + decide EVERY segment."""
    lines = []
    for i, seg in enumerate(segments):
        payload = f"Speaker: {seg.speaker}\nText:\n{seg.text}" if seg.speaker else seg.text
        lines.append(f"[SEGMENT {i}]")
        lines.append(format_untrusted_data_block(f"Segment {i}", payload))
    numbered = "\n\n".join(lines)
    return f"""You are a qualitative researcher performing EXHAUSTIVE thematic coding. Every segment below must receive a decision — this is what makes the analysis defensible (no segment silently skipped).

TASK:
1. Discover a hierarchical codebook from the data. Each code has an `id` in CAPS_WITH_UNDERSCORES, a name, description, semantic_definition, level, mention_count, and discovery_confidence.
2. For EVERY segment, output a decision: the list of code `id`s that apply to it. If no code applies (e.g. interviewer prompts, filler, off-topic), return an EMPTY list for that segment — do NOT force a code.

Return `codes` (the codebook) and `decisions` (exactly one entry per segment index below, with `segment_index` matching the [SEGMENT N] number). Every segment index from 0 to {len(segments) - 1} must appear in `decisions`.

SEGMENTS:
{numbered}

Also write a brief analytical_memo (3-5 sentences) on key decisions, surprises, and uncertainties."""

def _build_combined_text(state: ProjectState) -> str:
    return format_untrusted_documents(state.corpus.documents, label_prefix="Interview")


def _grounding_issue(
    *,
    stage_name: str,
    code_id: str,
    quote: str,
    status: GroundingIssueStatus,
    occurrence_count: int,
) -> GroundingIssue:
    remediation = {
        GroundingIssueStatus.NO_SOURCE_MATCH: (
            "Review the source transcript and either correct the quote text, "
            "replace it with an exact source span, or remove the evidence item."
        ),
        GroundingIssueStatus.AMBIGUOUS_MATCH: (
            "Review duplicate source occurrences and select the intended "
            "document/span before using this quote as evidence."
        ),
    }[status]
    return GroundingIssue(
        stage_name=stage_name,
        code_id=code_id,
        quote_text=quote,
        status=status,
        occurrence_count=occurrence_count,
        remediation_hint=remediation,
    )


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
