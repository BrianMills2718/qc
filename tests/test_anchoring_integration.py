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
    assert any(w.startswith("Thematic coding:") for w in result.data_warnings)


def test_constant_comparison_merge_populates_anchors():
    """gt_constant_comparison applications get char offsets + hash when the quote
    resolves uniquely in the segment's document (INV-1, best-effort)."""
    from qc_clean.core.grounding import verify_anchor
    from qc_clean.core.pipeline.stages.gt_constant_comparison import (
        SegmentCodeApplication,
        SegmentCodingResponse,
        _merge_segment_results,
    )
    from qc_clean.schemas.domain import Code, Codebook

    content = "Sam: structure helps me focus and deliver on time."
    codebook = Codebook(codes=[Code(id="C1", name="Structure", description="d")])
    apps = []
    response = SegmentCodingResponse(
        applications=[SegmentCodeApplication(code_name="Structure", quote="structure helps me focus", is_new_code=False)],
    )
    segment = {"doc_id": "d1", "text": content, "speaker": "Sam"}
    _merge_segment_results(codebook, apps, response, segment, {"d1": content})

    assert len(apps) == 1
    a = apps[0]
    assert a.doc_id == "d1" and a.speaker == "Sam"
    assert a.start_char is not None and a.quote_hash is not None
    assert content[a.start_char:a.end_char] == "structure helps me focus"
    assert verify_anchor(content, a.start_char, a.end_char, a.quote_hash)


def test_incremental_thematic_anchors_and_drops_ambiguous():
    """Incremental thematic coding anchors unique quotes and drops ambiguous ones."""
    from qc_clean.core.pipeline.stages.incremental_coding import _process_thematic_response
    from qc_clean.schemas.analysis_schemas import CodeHierarchy, ThematicCode
    from qc_clean.schemas.domain import Code, Codebook, Corpus, Document

    new_docs = [
        Document(id="n1", name="n1.txt", content="Pat: I value deep focus time. We felt rushed."),
        Document(id="n2", name="n2.txt", content="Lee: Honestly we felt rushed all quarter."),
    ]
    state = _two_doc_state()
    state.corpus = Corpus(documents=new_docs)
    state.codebook = Codebook(codes=[Code(id="FOCUS", name="Focus", description="d")])

    resp = CodeHierarchy(
        codes=[ThematicCode(id="FOCUS", name="Focus", description="d", semantic_definition="s",
                            level=0, mention_count=1, discovery_confidence=0.7,
                            example_quotes=["I value deep focus time", "we felt rushed"])],
        total_codes=1, analysis_confidence=0.7,
    )
    apps = _process_thematic_response(resp, state, new_docs, {"n1", "n2"})

    # unique quote anchored; ambiguous ("we felt rushed" in both docs) dropped
    assert len(apps) == 1
    assert apps[0].doc_id == "n1"
    assert apps[0].quote_hash is not None
    assert any("uniquely anchored" in w for w in state.data_warnings)
