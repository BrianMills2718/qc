"""
Relationship stage: wraps the current Phase 3 entity & relationship mapping.
"""

from __future__ import annotations

import logging

from qc_clean.core.claims import claims_for_relationships, replace_claims_for_stage
from qc_clean.core.prompting import format_untrusted_data_block, format_untrusted_documents
from qc_clean.schemas.analysis_schemas import EntityMapping
from qc_clean.schemas.adapters import entity_mapping_to_entities
from qc_clean.schemas.domain import Codebook, ProjectState
from ..pipeline_engine import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


class RelationshipStage(PipelineStage):

    def name(self) -> str:
        return "relationship"

    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        logger.info(
            "Starting relationship: docs=%d, codes=%d, model=%s",
            state.corpus.num_documents, len(state.codebook.codes), ctx.model_name,
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

        prompt = _build_phase3_prompt(combined_text, phase1_text, phase2_text, state.codebook)

        phase3_response = await llm.extract_structured(
            prompt, EntityMapping, **ctx.llm_call_options(self.name())
        )

        # Convert to domain entities — pass all doc IDs since entities span documents
        all_doc_ids = [d.id for d in state.corpus.documents]
        entities, entity_rels, code_rels, causal_chains, connections = entity_mapping_to_entities(
            phase3_response, all_doc_ids, codebook=state.codebook
        )
        state.entities = entities
        state.entity_relationships = entity_rels
        state.code_relationships = code_rels

        # Extract analytical memo
        if phase3_response.analytical_memo:
            from qc_clean.schemas.domain import AnalysisMemo
            state.memos.append(AnalysisMemo(
                memo_type="pattern",
                title="Relationship Mapping Memo",
                content=phase3_response.analytical_memo,
                code_refs=[e.id for e in entities],
            ))

        # Store causal chains and connections as a memo
        if causal_chains or connections:
            from qc_clean.schemas.domain import AnalysisMemo
            memo_parts = []
            if causal_chains:
                memo_parts.append("## Cause-Effect Chains\n" + "\n".join(f"- {c}" for c in causal_chains))
            if connections:
                memo_parts.append("## Conceptual Connections\n" + "\n".join(f"- {c}" for c in connections))
            state.memos.append(AnalysisMemo(
                memo_type="relationship",
                title="Causal Chains & Conceptual Connections",
                content="\n\n".join(memo_parts),
            ))

        # Stash for downstream
        ctx.phase3_json = phase3_response.model_dump_json(indent=2)
        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_relationships(state, self.name()),
            no_claims_reason="relationship mapping produced no entity or code relationships",
        )

        logger.info(
            "Relationship mapping complete: %d entities, %d entity relationships, %d code relationships",
            len(entities),
            len(entity_rels),
            len(code_rels),
        )
        return state


def _build_combined_text(state: ProjectState) -> str:
    return format_untrusted_documents(state.corpus.documents, label_prefix="Interview")


def _build_phase3_prompt(
    combined_text: str,
    phase1_text: str,
    phase2_text: str,
    codebook: Codebook | None = None,
) -> str:
    code_reference = ""
    if codebook and codebook.codes:
        lines = ["THEMATIC CODE REFERENCE (use exact code IDs in code_relationships):"]
        for code in codebook.codes:
            desc = f" — {code.description[:80]}" if code.description else ""
            lines.append(f"  {code.id}: {code.name}{desc}")
        code_reference = "\n".join(lines) + "\n\n"

    return f"""Identify thematic code relationships and entity relationships in the interview data.

{code_reference}INSTRUCTIONS:
1. THEMATIC CODE RELATIONSHIPS (primary task): Map analytic relationships between the codes listed above. Use exact code IDs from the reference list. Produce 4-8 code relationships when the data supports them. Relationship types should be specific (e.g., "leads_to", "enables", "constrains", "qualifies", "tensions_with", "co-occurs_with").
2. ENTITY EXTRACTION: Extract only important entities that appear in at least one relationship, causal chain, or conceptual connection.
3. ENTITY RELATIONSHIPS: Map entity-to-entity relationships with clear evidence. Return roughly 4-10 entity relationships.
4. Identify cause-effect chains grounded in what the interviewee(s) actually said.

PREVIOUS ANALYSIS:
Phase 1 Codes: {phase1_text}
Phase 2 Speakers: {phase2_text}

INTERVIEW CONTENT:
{combined_text}

ANALYTICAL MEMO: After completing the analysis above, write a brief analytical memo (3-5 sentences) in the "analytical_memo" field recording:
- Key analytical decisions you made and why
- Patterns or surprises that emerged during analysis
- Uncertainties or areas needing further investigation

Provide focused code and entity relationship mapping. The code_relationships field is required — populate it with analytic links between the thematic codes listed above."""
