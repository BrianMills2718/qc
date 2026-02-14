"""
Grounded Theory constant comparison stage.

Implements iterative segment-by-segment coding following Strauss & Corbin:
1. Segment documents into codeable units (speaker turns or paragraph chunks)
2. Code each segment against the evolving codebook
3. After each full pass through segments, check for saturation
4. Stop when codebook stabilizes or max iterations reached

Replaces the single-batch GTOpenCodingStage for more methodologically
faithful grounded theory analysis.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List

from pydantic import BaseModel, Field

from qc_clean.core.pipeline.saturation import calculate_codebook_change
from qc_clean.schemas.domain import (
    AnalysisMemo,
    Code,
    CodeApplication,
    Codebook,
    Document,
    ProjectState,
    Provenance,
)
from qc_clean.schemas.gt_schemas import OpenCode
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response schemas for segment-level coding
# ---------------------------------------------------------------------------

class SegmentCodeApplication(BaseModel):
    """A code applied to a specific quote in a segment."""
    code_name: str = Field(description="Name of the code (existing or new)")
    quote: str = Field(description="Verbatim quote from the segment")
    is_new_code: bool = Field(
        default=False,
        description="True if this is a newly discovered code",
    )


class CodeModification(BaseModel):
    """A suggested modification to an existing code."""
    code_name: str = Field(description="Name of the code to modify")
    new_description: str = Field(default="", description="Updated description")
    new_properties: List[str] = Field(
        default_factory=list, description="Updated properties"
    )
    rationale: str = Field(default="", description="Why this modification is needed")


class SegmentCodingResponse(BaseModel):
    """LLM response for coding a single segment."""
    applications: List[SegmentCodeApplication] = Field(
        default_factory=list,
        description="Code applications for this segment",
    )
    new_codes: List[OpenCode] = Field(
        default_factory=list,
        description="New codes discovered in this segment",
    )
    modifications: List[CodeModification] = Field(
        default_factory=list,
        description="Suggested modifications to existing codes",
    )
    analytical_memo: str = Field(
        default="",
        description="Brief analytical memo about this segment's coding",
    )


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

def segment_documents(documents: List[Document]) -> List[Dict]:
    """
    Split documents into codeable segments.

    Uses speaker turns for interview transcripts (when speakers are detected),
    otherwise groups paragraphs into ~500-word chunks.
    """
    segments = []
    for doc in documents:
        if doc.detected_speakers:
            turns = split_by_speaker_turns(doc.content, doc.detected_speakers)
            for i, turn in enumerate(turns):
                if turn["text"].strip():
                    segments.append({
                        "doc_id": doc.id,
                        "doc_name": doc.name,
                        "segment_index": i,
                        "text": turn["text"],
                        "speaker": turn.get("speaker", ""),
                    })
        else:
            paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
            chunks = group_into_chunks(paragraphs, target_words=500)
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    segments.append({
                        "doc_id": doc.id,
                        "doc_name": doc.name,
                        "segment_index": i,
                        "text": chunk,
                        "speaker": "",
                    })
    return segments


def split_by_speaker_turns(
    content: str, speakers: List[str]
) -> List[Dict]:
    """Split transcript into speaker turns."""
    if not speakers:
        return [{"text": content, "speaker": ""}]

    # Build pattern matching any known speaker at start of line
    escaped = [re.escape(s) for s in speakers]
    pattern = re.compile(
        r"^(" + "|".join(escaped) + r")(?::\s|\s{2,}\d+:\d{2})",
        re.MULTILINE,
    )

    turns = []
    last_end = 0
    last_speaker = ""

    for match in pattern.finditer(content):
        if last_end > 0:
            text = content[last_end:match.start()].strip()
            if text:
                turns.append({"text": text, "speaker": last_speaker})
        last_speaker = match.group(1)
        last_end = match.end()

    # Capture final turn
    if last_end < len(content):
        text = content[last_end:].strip()
        if text:
            turns.append({"text": text, "speaker": last_speaker})

    # If no turns found (pattern didn't match), return whole content
    if not turns:
        return [{"text": content, "speaker": ""}]

    return turns


def group_into_chunks(paragraphs: List[str], target_words: int = 500) -> List[str]:
    """Group paragraphs into chunks of approximately target_words."""
    chunks = []
    current_chunk = []
    current_words = 0

    for para in paragraphs:
        word_count = len(para.split())
        if current_words + word_count > target_words and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_words = word_count
        else:
            current_chunk.append(para)
            current_words += word_count

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks


# ---------------------------------------------------------------------------
# Stage
# ---------------------------------------------------------------------------

class GTConstantComparisonStage(PipelineStage):
    """
    Iterative constant comparison coding following GT methodology.

    Segments documents, codes each segment against an evolving codebook,
    and iterates until saturation or max_iterations.
    """

    def __init__(
        self,
        pause_for_review: bool = False,
        max_iterations: int = 3,
        saturation_threshold: float = 0.15,
    ):
        self._pause_for_review = pause_for_review
        self._max_iterations = max_iterations
        self._saturation_threshold = saturation_threshold

    def name(self) -> str:
        return "gt_constant_comparison"

    def requires_human_review(self) -> bool:
        return self._pause_for_review

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        logger.info(
            "Starting gt_constant_comparison: docs=%d, max_iterations=%d, model=%s",
            state.corpus.num_documents, self._max_iterations, model_name,
        )
        llm = LLMHandler(model_name=model_name)

        segments = segment_documents(state.corpus.documents)
        if not segments:
            raise RuntimeError(
                "No segments found in documents — cannot perform constant comparison. "
                f"Corpus has {state.corpus.num_documents} documents."
            )

        codebook = Codebook(methodology="grounded_theory", created_by=Provenance.LLM)
        all_applications: List[CodeApplication] = []
        iteration_memos: List[str] = []
        final_iteration = 0

        for iteration in range(self._max_iterations):
            final_iteration = iteration
            old_codebook = codebook.model_copy(deep=True)

            for seg_idx, segment in enumerate(segments):
                prompt = _build_comparison_prompt(codebook, segment, seg_idx, len(segments))

                irr_suffix = config.get("irr_prompt_suffix", "")
                if irr_suffix:
                    prompt = prompt + "\n\n" + irr_suffix

                response = await llm.extract_structured(prompt, SegmentCodingResponse)
                _merge_segment_results(codebook, all_applications, response, segment)

                if response.analytical_memo:
                    iteration_memos.append(response.analytical_memo)

            # Check saturation after full pass
            if len(old_codebook.codes) > 0:
                change = calculate_codebook_change(old_codebook, codebook)
                logger.info(
                    "Constant comparison iteration %d: %d codes, %.1f%% change",
                    iteration + 1, len(codebook.codes),
                    change["pct_change"] * 100,
                )
                if change["pct_change"] < self._saturation_threshold:
                    logger.info("Saturation reached at iteration %d", iteration + 1)
                    break
            else:
                logger.info(
                    "Constant comparison iteration %d: %d codes (first pass)",
                    iteration + 1, len(codebook.codes),
                )

        state.codebook = codebook
        state.code_applications = all_applications
        state.iteration = final_iteration + 1
        if final_iteration > 0:
            state.codebook_history.append(old_codebook)

        # Aggregate memos
        if iteration_memos:
            combined_memo = "\n\n".join(
                f"**Segment {i+1}**: {m}" for i, m in enumerate(iteration_memos[:10])
            )
            state.memos.append(AnalysisMemo(
                memo_type="coding",
                title="Constant Comparison Coding Memos",
                content=combined_memo,
                code_refs=[c.id for c in codebook.codes],
            ))

        # Stash open codes for downstream GT stages
        from qc_clean.schemas.adapters import codebook_to_open_codes
        open_codes = codebook_to_open_codes(codebook)
        config["_gt_open_codes"] = open_codes
        config["_gt_open_codes_text"] = _format_codes_for_analysis(open_codes)

        logger.info(
            "Constant comparison complete: %d iterations, %d codes, %d applications",
            final_iteration + 1, len(codebook.codes), len(all_applications),
        )
        return state


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_comparison_prompt(
    codebook: Codebook,
    segment: Dict,
    seg_idx: int,
    total_segments: int,
) -> str:
    """Build the constant comparison prompt for a single segment."""
    codebook_section = _format_codebook_context(codebook)

    return f"""You are conducting grounded theory open coding using the constant comparison method.

{codebook_section}

DATA SEGMENT ({seg_idx + 1} of {total_segments}, from "{segment['doc_name']}"{_speaker_info(segment)}):
\"\"\"{segment['text']}\"\"\"

INSTRUCTIONS:
1. Compare this segment against each existing code in the codebook
2. Apply existing codes where the data clearly fits — provide VERBATIM quotes as evidence
3. If you see a concept NOT captured by any existing code, create a new code:
   - Use a clear, concise name based on participants' language
   - Provide description, properties, dimensions, and supporting quotes
4. If existing codes need refinement based on this new data, suggest modifications
5. Stay close to the data — use participants' language when naming codes
6. Each quote must be VERBATIM from the segment above

For new codes, follow grounded theory principles:
- Name concepts clearly and concisely
- Identify properties (characteristics) and dimensional variations
- Note the analytical reasoning behind each code

ANALYTICAL MEMO: Write a brief note (1-2 sentences) about what you observed in this segment — patterns, surprises, connections to existing codes."""


def _format_codebook_context(codebook: Codebook) -> str:
    """Format existing codebook for inclusion in prompt."""
    if not codebook.codes:
        return "CURRENT CODEBOOK: (empty — this is the first segment, create initial codes)"

    lines = [f"CURRENT CODEBOOK ({len(codebook.codes)} codes):"]
    for code in codebook.codes:
        line = f"  - {code.name}: {code.description}"
        if code.properties:
            line += f"\n    Properties: {', '.join(code.properties[:5])}"
        lines.append(line)
    return "\n".join(lines)


def _speaker_info(segment: Dict) -> str:
    """Format speaker info if available."""
    if segment.get("speaker"):
        return f', speaker: {segment["speaker"]}'
    return ""


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def _merge_segment_results(
    codebook: Codebook,
    all_applications: List[CodeApplication],
    response: SegmentCodingResponse,
    segment: Dict,
) -> None:
    """Merge segment coding results into the codebook and applications list."""
    from qc_clean.core.pipeline.irr import normalize_code_name

    # 1. Add new codes to codebook
    for new_code in response.new_codes:
        norm_name = normalize_code_name(new_code.code_name)
        existing = None
        for c in codebook.codes:
            if normalize_code_name(c.name) == norm_name:
                existing = c
                break
        if not existing:
            code = Code(
                id=new_code.code_name.upper().replace(" ", "_"),
                name=new_code.code_name,
                description=new_code.description,
                properties=new_code.properties,
                dimensions=new_code.dimensions,
                parent_id=new_code.parent_id,
                level=new_code.level,
                provenance=Provenance.LLM,
                example_quotes=new_code.supporting_quotes,
                mention_count=new_code.frequency,
                confidence=new_code.confidence,
                reasoning=new_code.reasoning,
            )
            codebook.codes.append(code)

    # 2. Apply modifications
    for mod in response.modifications:
        existing = codebook.get_code_by_name(mod.code_name)
        if existing:
            if mod.new_description:
                existing.description = mod.new_description
            if mod.new_properties:
                for prop in mod.new_properties:
                    if prop not in existing.properties:
                        existing.properties.append(prop)

    # 3. Create code applications
    for app in response.applications:
        # Find the code by name (case-insensitive)
        norm_name = normalize_code_name(app.code_name)
        code = None
        for c in codebook.codes:
            if normalize_code_name(c.name) == norm_name:
                code = c
                break

        if code:
            all_applications.append(CodeApplication(
                code_id=code.id,
                doc_id=segment["doc_id"],
                quote_text=app.quote,
                speaker=segment.get("speaker") or None,
                confidence=code.confidence,
                applied_by=Provenance.LLM,
                codebook_version=codebook.version,
            ))
            # Increment mention count
            code.mention_count += 1


def _format_codes_for_analysis(open_codes: list) -> str:
    """Format open codes for downstream GT stages."""
    formatted = []
    for code in open_codes:
        text = f"- {code.code_name}: {code.description}\n"
        text += f"  Properties: {', '.join(code.properties)}\n"
        text += f"  Frequency: {code.frequency}, Confidence: {code.confidence:.2f}"
        formatted.append(text)
    return "\n\n".join(formatted)
