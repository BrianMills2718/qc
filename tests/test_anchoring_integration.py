"""Phase 2: coding stages produce span-anchored applications (INV-1).

Locks in that the thematic stage (a) populates start_char/end_char/quote_hash on
applications whose quote resolves uniquely, and (b) drops quotes that are
ambiguous (occur in >1 document) rather than misattributing them — surfacing a
data_warning.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from qc_clean.core.grounding import verify_anchor
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage
from qc_clean.schemas.analysis_schemas import CodeHierarchy, ThematicCode
from qc_clean.schemas.domain import (
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
)


def _two_doc_state() -> ProjectState:
    return ProjectState(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(name="alex.txt", content="Alex: I do my best work alone. Sometimes I felt ignored."),
            Document(name="sam.txt", content="Sam: Honestly, I felt ignored in every meeting."),
        ]),
    )


def test_thematic_applications_are_span_anchored_and_ambiguous_dropped():
    state = _two_doc_state()
    ctx = PipelineContext()
    mock = CodeHierarchy(
        codes=[
            ThematicCode(
                id="AUTONOMY", name="Autonomy", description="d",
                semantic_definition="s", level=0, mention_count=1,
                discovery_confidence=0.8,
                example_quotes=[
                    "I do my best work alone",   # unique -> anchored to alex.txt
                    "I felt ignored",            # appears twice -> ambiguous -> dropped
                ],
            ),
        ],
        total_codes=1, analysis_confidence=0.8,
    )

    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(ThematicCodingStage().execute(state, ctx))

    # Only the unique quote becomes an application; the ambiguous one is dropped.
    assert len(result.code_applications) == 1
    app = result.code_applications[0]
    alex = next(d for d in result.corpus.documents if d.name == "alex.txt")
    assert app.doc_id == alex.id
    assert app.start_char is not None and app.end_char is not None
    assert alex.content[app.start_char:app.end_char] == "I do my best work alone"
    assert verify_anchor(alex.content, app.start_char, app.end_char, app.quote_hash)
    # The ambiguous drop is surfaced, never silently misattributed.
    assert any("uniquely anchored" in w for w in result.data_warnings)
