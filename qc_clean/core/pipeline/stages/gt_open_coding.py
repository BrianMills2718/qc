"""
Grounded Theory open coding stage.
"""

from __future__ import annotations

import logging
from pydantic import BaseModel, Field
from typing import List

from qc_clean.core.workflow.grounded_theory import OpenCode
from qc_clean.schemas.adapters import open_codes_to_codebook
from qc_clean.schemas.domain import CodeApplication, ProjectState, Provenance
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class OpenCodesResponse(BaseModel):
    open_codes: List[OpenCode] = Field(description="List of open codes identified")


class GTOpenCodingStage(PipelineStage):

    def __init__(self, pause_for_review: bool = False):
        self._pause_for_review = pause_for_review

    def name(self) -> str:
        return "gt_open_coding"

    def requires_human_review(self) -> bool:
        return self._pause_for_review

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        from qc_clean.core.llm.llm_handler import LLMHandler

        model_name = config.get("model_name", "gpt-5-mini")
        llm = LLMHandler(model_name=model_name)

        combined_text = _build_combined_text(state)

        prompt = f"""You are an expert qualitative researcher conducting open coding analysis following grounded theory methodology.

Analyze the following interview data and identify key concepts and categories. For each concept identified:
1. Name the concept clearly and concisely
2. Describe what this concept represents in the data
3. Identify properties (characteristics) of this concept
4. Note dimensional variations (different ways this concept appears)
5. Provide supporting quotes that demonstrate this concept
6. Assess frequency and confidence
7. ORGANIZE HIERARCHICALLY:
   - Level 0: Top-level parent codes (3-5 major themes)
   - Level 1: Child codes under each parent (2-4 per parent)
   - Level 2+: Further sub-codes if the data supports it
   - Use parent_id to link each code to its parent (use parent's code_name with underscores)

Follow open coding principles:
- Stay close to the data
- Use participants' language when possible
- Look for actions, interactions, and meanings

Interview Data:
{combined_text}

Generate comprehensive open codes that capture the key concepts in this data."""

        response = await llm.extract_structured(prompt, OpenCodesResponse)
        open_codes = response.open_codes

        # Convert to domain codebook
        codebook = open_codes_to_codebook(open_codes)
        state.codebook = codebook

        # Build code applications from supporting quotes
        all_apps = []
        for oc in open_codes:
            code = codebook.get_code_by_name(oc.code_name)
            code_id = code.id if code else oc.code_name
            for quote in oc.supporting_quotes:
                for doc in state.corpus.documents:
                    if quote in doc.content:
                        all_apps.append(CodeApplication(
                            code_id=code_id,
                            doc_id=doc.id,
                            quote_text=quote,
                            confidence=oc.confidence,
                            applied_by=Provenance.LLM,
                            codebook_version=codebook.version,
                        ))
                        break
                else:
                    # Assign to first doc if quote not found verbatim
                    if state.corpus.documents:
                        all_apps.append(CodeApplication(
                            code_id=code_id,
                            doc_id=state.corpus.documents[0].id,
                            quote_text=quote,
                            confidence=oc.confidence,
                            applied_by=Provenance.LLM,
                            codebook_version=codebook.version,
                        ))
        state.code_applications = all_apps

        # Stash raw open codes for downstream GT stages
        config["_gt_open_codes"] = open_codes
        config["_gt_open_codes_text"] = _format_codes_for_analysis(open_codes)

        logger.info("GT open coding complete: %d codes", len(open_codes))
        return state


def _build_combined_text(state: ProjectState) -> str:
    parts = []
    for doc in state.corpus.documents:
        parts.append(f"--- Interview: {doc.name} ---")
        parts.append(doc.content)
        parts.append("")
    return "\n".join(parts)


def _format_codes_for_analysis(open_codes: list) -> str:
    formatted = []
    for code in open_codes:
        text = f"- {code.code_name}: {code.description}\n"
        text += f"  Properties: {', '.join(code.properties)}\n"
        text += f"  Frequency: {code.frequency}, Confidence: {code.confidence:.2f}"
        formatted.append(text)
    return "\n\n".join(formatted)
