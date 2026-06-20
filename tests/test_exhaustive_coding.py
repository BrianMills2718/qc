"""Exhaustive per-segment thematic coding (INV-8 Phase 5).

One batched call renders a decision for every segment; applications anchor
directly to segment spans; 'no_code' segments are recorded (examined, not
relevant) — distinct from 'not examined'.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from qc_clean.core.grounding import verify_anchor
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage
from qc_clean.core.segmentation import segment_corpus
from qc_clean.schemas.analysis_schemas import (
    ExhaustiveCodingResponse,
    SegmentDecision,
    ThematicCode,
)
from qc_clean.schemas.domain import (
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
)


def _state():
    content = ("Interviewer: How do you feel about the monitoring tool?\n"
               "Dana: It makes me anxious; I feel watched.\n"
               "Dana: My boss says it's support, but it feels like distrust.")
    doc = Document(id="d1", name="dana.txt", content=content,
                   detected_speakers=["Interviewer", "Dana"])
    state = ProjectState(name="t", config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
                         corpus=Corpus(documents=[doc]))
    state.segments = segment_corpus([doc])
    return state, doc


def test_exhaustive_codes_every_segment_and_anchors_to_spans():
    state, doc = _state()
    assert len(state.segments) == 3  # 1 interviewer prompt + 2 Dana turns

    mock = ExhaustiveCodingResponse(
        codes=[
            ThematicCode(id="ANXIETY", name="Surveillance anxiety", description="d",
                         semantic_definition="s", level=0, mention_count=1, discovery_confidence=0.8),
            ThematicCode(id="DISTRUST", name="Perceived distrust", description="d",
                         semantic_definition="s", level=0, mention_count=1, discovery_confidence=0.8),
        ],
        decisions=[
            SegmentDecision(segment_index=0, code_ids=[]),            # interviewer prompt -> no code
            SegmentDecision(segment_index=1, code_ids=["ANXIETY"]),
            SegmentDecision(segment_index=2, code_ids=["DISTRUST"]),
        ],
        total_codes=2, analysis_confidence=0.8,
    )
    ctx = PipelineContext(exhaustive_coding=True)
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(ThematicCodingStage().execute(state, ctx))

    # EVERY segment examined: decisions recorded (no None).
    decisions = [s.decision for s in result.segments]
    assert decisions == ["no_code", "coded", "coded"]

    # Two applications, each anchored exactly to its segment span + verifiable.
    assert len(result.code_applications) == 2
    by_code = {a.code_id: a for a in result.code_applications}
    for code_id, seg_idx in [("ANXIETY", 1), ("DISTRUST", 2)]:
        a = by_code[code_id]
        seg = result.segments[seg_idx]
        assert a.start_char == seg.start_char and a.end_char == seg.end_char
        assert a.quote_text == seg.text
        assert verify_anchor(doc.content, a.start_char, a.end_char, a.quote_hash)


def test_exhaustive_sets_phase1_json_for_downstream_stages():
    """Regression: exhaustive coding must stash the codebook as ctx.phase1_json,
    exactly like the example-quote path. Downstream stages (perspective,
    relationship, synthesis) `ctx.require("phase1_json")`, so without this
    `project run --exhaustive` crashes at perspective on a default-methodology
    project. Caught by the full-pipeline live E2E; locked here deterministically."""
    state, _ = _state()
    mock = ExhaustiveCodingResponse(
        codes=[ThematicCode(id="ANXIETY", name="Surveillance anxiety", description="d",
                            semantic_definition="s", level=0, mention_count=1,
                            discovery_confidence=0.8)],
        decisions=[
            SegmentDecision(segment_index=0, code_ids=[]),
            SegmentDecision(segment_index=1, code_ids=["ANXIETY"]),
            SegmentDecision(segment_index=2, code_ids=["ANXIETY"]),
        ],
        total_codes=1, analysis_confidence=0.8,
    )
    ctx = PipelineContext(exhaustive_coding=True)
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        asyncio.run(ThematicCodingStage().execute(state, ctx))

    assert ctx.phase1_json, "exhaustive path must populate ctx.phase1_json"
    import json
    parsed = json.loads(ctx.phase1_json)
    assert any(c.get("id") == "ANXIETY" for c in parsed.get("codes", []))


def test_exhaustive_warns_when_model_skips_a_segment():
    state, _ = _state()
    mock = ExhaustiveCodingResponse(
        codes=[ThematicCode(id="X", name="X", description="d", semantic_definition="s",
                            level=0, mention_count=1, discovery_confidence=0.5)],
        decisions=[SegmentDecision(segment_index=0, code_ids=[])],  # only 1 of 3 segments
        total_codes=1, analysis_confidence=0.5,
    )
    ctx = PipelineContext(exhaustive_coding=True)
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(ThematicCodingStage().execute(state, ctx))

    # Segments the model skipped stay 'not examined' (None) and are flagged.
    assert result.segments[1].decision is None
    assert any("not examined" in w for w in result.data_warnings)


def test_default_mode_unchanged_no_segment_decisions():
    """Without the flag, the cheap example-quote path runs (segments not decided)."""
    state, _ = _state()
    from qc_clean.schemas.analysis_schemas import CodeHierarchy
    mock = CodeHierarchy(
        codes=[ThematicCode(id="ANXIETY", name="A", description="d", semantic_definition="s",
                            level=0, mention_count=1, discovery_confidence=0.8,
                            example_quotes=["It makes me anxious"])],
        total_codes=1, analysis_confidence=0.8,
    )
    ctx = PipelineContext()  # exhaustive_coding defaults False
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(ThematicCodingStage().execute(state, ctx))
    assert all(s.decision is None for s in result.segments)  # decisions only in exhaustive mode
