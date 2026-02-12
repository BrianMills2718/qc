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
            # Corpus already populated (e.g. via add-docs).
            # Run speaker detection on any docs that are missing it.
            for doc in state.corpus.documents:
                if not doc.detected_speakers and doc.content:
                    doc.detected_speakers = _detect_speakers(doc.content)
            logger.info("Corpus already populated (%d docs), ran speaker detection",
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
    """Simple heuristic speaker detection from transcript text.

    Matches two common transcript formats:
      - ``Speaker Name:  text``   (colon-delimited)
      - ``Speaker Name   0:03``   (name + timestamp, e.g. auto-transcription tools)
    """
    import re

    speakers: list[str] = []

    # Pattern 1: "Name:" at start of line
    colon_pattern = re.compile(r"^([A-Z][A-Za-z\s.'-]{1,40}):\s", re.MULTILINE)
    for match in colon_pattern.finditer(text):
        name = match.group(1).strip()
        if name and name not in speakers:
            speakers.append(name)

    # Pattern 2: "Name   0:03" (name followed by whitespace + timestamp)
    # Use [^\S\n] to match horizontal whitespace only (not newlines)
    timestamp_pattern = re.compile(
        r"^([A-Z][A-Za-z .'-]{1,40})[^\S\n]{2,}\d+:\d{2}\b", re.MULTILINE
    )
    for match in timestamp_pattern.finditer(text):
        name = match.group(1).strip()
        if name and name not in speakers:
            speakers.append(name)

    return speakers
