"""
Ingest stage: extract text from documents, detect speakers, build Corpus.
"""

from __future__ import annotations

import logging

from qc_clean.schemas.domain import (
    Corpus,
    Document,
    PipelineStatus,
    ProjectState,
)
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class IngestStage(PipelineStage):

    def name(self) -> str:
        return "ingest"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        """
        Build the Corpus from raw interview data.

        Expects ``config["interviews"]`` -- a list of dicts with keys
        ``name`` and ``content``.  If the corpus is already populated
        (e.g. loaded from a saved project), this stage is a no-op.
        """
        interviews = config.get("interviews", [])

        if state.corpus.num_documents > 0 and not interviews:
            logger.info("Corpus already populated (%d docs), skipping ingest",
                        state.corpus.num_documents)
            return state

        corpus = Corpus()
        data_warnings: list[str] = []

        for interview in interviews:
            content = interview.get("content", "")
            doc_name = interview.get("name", "Unknown")

            # Detect truncation
            is_truncated = False
            stripped = content.rstrip()
            if stripped and stripped[-1] not in '.!?"\')\n':
                is_truncated = True
                data_warnings.append(
                    f"Interview '{doc_name}' appears truncated (ends mid-sentence)"
                )

            # Simple speaker detection (look for "Name:" patterns)
            speakers = _detect_speakers(content)

            doc = Document(
                name=doc_name,
                content=content,
                detected_speakers=speakers,
                is_truncated=is_truncated,
                metadata=interview.get("metadata", {}),
            )
            # Preserve explicit id if provided
            if "id" in interview:
                doc.id = interview["id"]

            corpus.add_document(doc)

        state.corpus = corpus
        state.data_warnings.extend(data_warnings)

        logger.info(
            "Ingested %d documents (%d warnings)",
            corpus.num_documents,
            len(data_warnings),
        )
        return state


def _detect_speakers(text: str) -> list[str]:
    """Simple heuristic speaker detection from transcript text."""
    import re

    speakers: list[str] = []
    # Match lines like "Speaker Name:" at the start of a line
    pattern = re.compile(r"^([A-Z][A-Za-z\s.'-]{1,40}):\s", re.MULTILINE)
    for match in pattern.finditer(text):
        name = match.group(1).strip()
        if name and name not in speakers:
            speakers.append(name)
    return speakers
