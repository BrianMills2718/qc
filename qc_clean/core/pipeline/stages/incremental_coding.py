"""
Incremental coding stage: code new/uncoded documents against an existing codebook.

Used when documents are added to a completed project. Sends only new document
text to the LLM with the existing codebook as context, then merges results.
"""

from __future__ import annotations

import logging
from typing import List

from qc_clean.core.pipeline.irr import normalize_code_name
from qc_clean.core.pipeline.saturation import calculate_codebook_change
from qc_clean.schemas.analysis_schemas import CodeHierarchy
from qc_clean.schemas.adapters import code_hierarchy_to_codebook
from qc_clean.schemas.domain import (
    AnalysisMemo,
    Code,
    CodeApplication,
    Codebook,
    Document,
    Methodology,
    ProjectState,
    Provenance,
)
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class IncrementalCodingStage(PipelineStage):
    """Code only new/uncoded documents against an existing codebook."""

    def name(self) -> str:
        return "incremental_coding"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.get_uncoded_doc_ids()) > 0 and len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        # Identify uncoded documents
        uncoded_ids = set(state.get_uncoded_doc_ids())
        new_docs = [d for d in state.corpus.documents if d.id in uncoded_ids]

        if not new_docs:
            logger.info("No uncoded documents found, skipping incremental coding")
            return state

        # Save current codebook to history
        old_codebook = state.codebook.model_copy(deep=True)

        # Build prompt with existing codebook context + new doc text
        is_gt = state.config.methodology == Methodology.GROUNDED_THEORY
        codebook_context = _format_codebook_for_prompt(state.codebook)
        new_doc_text = _build_new_doc_text(new_docs)

        if is_gt:
            from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
            prompt = _build_incremental_gt_prompt(codebook_context, new_doc_text)
            response = await llm.extract_structured(prompt, OpenCodesResponse)
            new_applications = _process_gt_response(
                response, state, new_docs, uncoded_ids
            )
        else:
            prompt = _build_incremental_thematic_prompt(codebook_context, new_doc_text)
            response = await llm.extract_structured(prompt, CodeHierarchy)
            new_applications = _process_thematic_response(
                response, state, new_docs, uncoded_ids
            )

        # Append new applications (don't remove existing)
        state.code_applications.extend(new_applications)

        # Track iteration
        state.codebook_history.append(old_codebook)
        state.iteration += 1

        # Report changes
        change = calculate_codebook_change(old_codebook, state.codebook)
        logger.info(
            "Incremental coding complete: %d new docs, %d new applications, "
            "codebook change=%.1f%% (added=%d, removed=%d, modified=%d)",
            len(new_docs),
            len(new_applications),
            change["pct_change"] * 100,
            len(change["added_codes"]),
            len(change["removed_codes"]),
            len(change["modified_codes"]),
        )

        # Extract analytical memo if present
        if hasattr(response, "analytical_memo") and response.analytical_memo:
            state.memos.append(AnalysisMemo(
                memo_type="coding",
                title="Incremental Coding Memo",
                content=response.analytical_memo,
                doc_refs=[d.id for d in new_docs],
                code_refs=[c.id for c in state.codebook.codes],
            ))

        return state


def _format_codebook_for_prompt(codebook: Codebook) -> str:
    """Format existing codebook for inclusion in the LLM prompt."""
    lines = []
    for code in codebook.codes:
        line = f"- {code.name} (ID: {code.id}): {code.description}"
        if code.example_quotes:
            quotes = "; ".join(f'"{q[:80]}"' for q in code.example_quotes[:2])
            line += f"\n  Example quotes: {quotes}"
        lines.append(line)
    return "\n".join(lines)


def _build_new_doc_text(docs: List[Document]) -> str:
    """Build combined text from new documents only."""
    parts = []
    for doc in docs:
        parts.append(f"--- New Document: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _build_incremental_thematic_prompt(
    codebook_context: str, new_doc_text: str
) -> str:
    return f"""You are a qualitative researcher performing INCREMENTAL coding. A previous analysis has already produced a codebook. New documents have been added and need to be coded.

EXISTING CODEBOOK — Apply these codes to the new data where they fit:
{codebook_context}

NEW DOCUMENTS TO CODE:
{new_doc_text}

INSTRUCTIONS:
1. Read the new documents carefully
2. Apply EXISTING codes where they clearly match the new data — use the exact same code names and IDs
3. Create NEW codes ONLY for concepts genuinely not covered by the existing codebook
4. For new codes, follow the same format: unique ID, name, description, semantic_definition, example_quotes, etc.
5. Each example_quote must be a VERBATIM quote from the NEW documents above
6. Use the FULL confidence range (0.0-1.0) based on evidence strength

Generate codes that include both applications of existing codes to new data and any genuinely new codes.

ANALYTICAL MEMO: After completing the analysis, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- How the new data relates to existing codes
- Any new patterns or concepts not captured by the existing codebook
- Whether the existing codebook seems sufficient or needs revision"""


def _build_incremental_gt_prompt(codebook_context: str, new_doc_text: str) -> str:
    return f"""You are a qualitative researcher performing INCREMENTAL open coding following grounded theory. A previous analysis has already produced codes. New documents have been added and need to be coded.

EXISTING CODES — Apply these to the new data where they fit:
{codebook_context}

NEW DOCUMENTS TO CODE:
{new_doc_text}

INSTRUCTIONS:
1. Read the new documents carefully
2. Apply EXISTING codes where they clearly match — use the exact same code names
3. Create NEW codes ONLY for genuinely new concepts
4. For each code, provide supporting quotes from the NEW documents
5. Stay close to the data — use participants' language
6. For new codes: name, description, properties, dimensions, supporting_quotes, frequency, confidence

Generate open codes covering both existing code applications and any new codes.

ANALYTICAL MEMO: After completing the analysis, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- How the new data relates to existing codes
- Any new patterns or concepts not captured by the existing codebook
- Whether the existing codebook seems sufficient or needs revision"""


def _process_thematic_response(
    response: CodeHierarchy,
    state: ProjectState,
    new_docs: List[Document],
    uncoded_ids: set,
) -> List[CodeApplication]:
    """Process thematic coding response: merge codes and build applications."""
    import re

    new_applications = []
    existing_names = {normalize_code_name(c.name): c for c in state.codebook.codes}

    for tc in response.codes:
        norm_name = normalize_code_name(tc.name)
        existing = existing_names.get(norm_name)

        if existing:
            # Use existing code ID for applications
            code_id = existing.id
        else:
            # New code — add to codebook
            new_code = Code(
                id=tc.id,
                name=tc.name,
                description=tc.description,
                definition=tc.semantic_definition,
                parent_id=tc.parent_id,
                level=tc.level,
                provenance=Provenance.LLM,
                version=state.codebook.version + 1,
                example_quotes=tc.example_quotes,
                mention_count=tc.mention_count,
                confidence=tc.discovery_confidence,
                reasoning=tc.reasoning,
            )
            state.codebook.codes.append(new_code)
            existing_names[norm_name] = new_code
            code_id = new_code.id

        # Build applications only for new documents
        for quote in tc.example_quotes:
            norm_quote = re.sub(r"\s+", " ", quote.lower().strip())
            if len(norm_quote) > 40:
                start = len(norm_quote) // 5
                end = len(norm_quote) * 4 // 5
                search_snippet = norm_quote[start:end]
            else:
                search_snippet = norm_quote

            matched = False
            for doc in new_docs:
                norm_content = re.sub(r"\s+", " ", doc.content.lower())
                if search_snippet in norm_content:
                    new_applications.append(CodeApplication(
                        code_id=code_id,
                        doc_id=doc.id,
                        quote_text=quote,
                        confidence=tc.discovery_confidence,
                        applied_by=Provenance.LLM,
                        codebook_version=state.codebook.version,
                    ))
                    matched = True
                    break

            if not matched and new_docs:
                # Fallback: assign to first new doc
                new_applications.append(CodeApplication(
                    code_id=code_id,
                    doc_id=new_docs[0].id,
                    quote_text=quote,
                    confidence=tc.discovery_confidence,
                    applied_by=Provenance.LLM,
                    codebook_version=state.codebook.version,
                ))

    return new_applications


def _process_gt_response(
    response,
    state: ProjectState,
    new_docs: List[Document],
    uncoded_ids: set,
) -> List[CodeApplication]:
    """Process GT open coding response: merge codes and build applications."""
    from qc_clean.schemas.adapters import open_codes_to_codebook

    new_applications = []
    existing_names = {normalize_code_name(c.name): c for c in state.codebook.codes}

    for oc in response.open_codes:
        norm_name = normalize_code_name(oc.code_name)
        existing = existing_names.get(norm_name)

        if existing:
            code_id = existing.id
        else:
            # New code — add to codebook
            new_code = Code(
                id=oc.code_name.upper().replace(" ", "_"),
                name=oc.code_name,
                description=oc.description,
                properties=oc.properties,
                dimensions=oc.dimensions,
                parent_id=oc.parent_id,
                level=oc.level,
                provenance=Provenance.LLM,
                version=state.codebook.version + 1,
                example_quotes=oc.supporting_quotes,
                mention_count=oc.frequency,
                confidence=oc.confidence,
                reasoning=oc.reasoning,
            )
            state.codebook.codes.append(new_code)
            existing_names[norm_name] = new_code
            code_id = new_code.id

        # Build applications for new documents
        for quote in oc.supporting_quotes:
            matched = False
            for doc in new_docs:
                if quote in doc.content:
                    new_applications.append(CodeApplication(
                        code_id=code_id,
                        doc_id=doc.id,
                        quote_text=quote,
                        confidence=oc.confidence,
                        applied_by=Provenance.LLM,
                        codebook_version=state.codebook.version,
                    ))
                    matched = True
                    break
            if not matched and new_docs:
                new_applications.append(CodeApplication(
                    code_id=code_id,
                    doc_id=new_docs[0].id,
                    quote_text=quote,
                    confidence=oc.confidence,
                    applied_by=Provenance.LLM,
                    codebook_version=state.codebook.version,
                ))

    return new_applications
