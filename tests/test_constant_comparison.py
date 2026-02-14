"""
Tests for GT constant comparison stage.

Covers:
- Segmentation: speaker turns, paragraph chunks, edge cases
- Merge logic: new codes, modifications, applications
- Stage orchestration with mocked LLM
- Pipeline factory integration
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.pipeline.stages.gt_constant_comparison import (
    GTConstantComparisonStage,
    SegmentCodeApplication,
    SegmentCodingResponse,
    CodeModification,
    group_into_chunks,
    segment_documents,
    split_by_speaker_turns,
    _merge_segment_results,
)
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.pipeline_factory import create_pipeline
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
    Provenance,
)
from qc_clean.schemas.gt_schemas import OpenCode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**kwargs) -> ProjectState:
    defaults = dict(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
        corpus=Corpus(documents=[
            Document(
                id="doc1",
                name="interview1.txt",
                content="We use AI for everything. It changed our workflow.\n\nData privacy is important to us.",
            ),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def _make_segment_response(
    applications=None, new_codes=None, modifications=None, memo=""
) -> SegmentCodingResponse:
    return SegmentCodingResponse(
        applications=applications or [],
        new_codes=new_codes or [],
        modifications=modifications or [],
        analytical_memo=memo,
    )


# ---------------------------------------------------------------------------
# Segmentation tests
# ---------------------------------------------------------------------------

class TestSegmentation:

    def test_segment_by_paragraphs(self):
        doc = Document(
            id="d1", name="doc.txt",
            content="First paragraph about AI.\n\nSecond paragraph about privacy.\n\nThird paragraph about workflows.",
        )
        segments = segment_documents([doc])
        # With 500-word target, these short paragraphs should be in one chunk
        assert len(segments) >= 1
        assert all(s["doc_id"] == "d1" for s in segments)

    def test_segment_by_speakers(self):
        doc = Document(
            id="d1", name="interview.txt",
            content="Alice: I think AI is great.\nAlice: It helps us a lot.\nBob: I agree with that.\nBob: We should use it more.",
            detected_speakers=["Alice", "Bob"],
        )
        segments = segment_documents([doc])
        # Each "Speaker:" line is a separate turn
        assert len(segments) == 4
        assert segments[0]["speaker"] == "Alice"
        assert segments[2]["speaker"] == "Bob"

    def test_segment_empty_doc(self):
        doc = Document(id="d1", name="empty.txt", content="")
        segments = segment_documents([doc])
        assert len(segments) == 0

    def test_segment_multiple_docs(self):
        docs = [
            Document(id="d1", name="doc1.txt", content="Content one."),
            Document(id="d2", name="doc2.txt", content="Content two."),
        ]
        segments = segment_documents(docs)
        assert len(segments) == 2
        doc_ids = {s["doc_id"] for s in segments}
        assert doc_ids == {"d1", "d2"}


class TestSplitBySpeakerTurns:

    def test_colon_format(self):
        text = "Alice: Hello there.\nBob: Hi Alice.\nAlice: How are you?"
        turns = split_by_speaker_turns(text, ["Alice", "Bob"])
        assert len(turns) == 3
        assert turns[0]["speaker"] == "Alice"
        assert "Hello" in turns[0]["text"]
        assert turns[1]["speaker"] == "Bob"

    def test_no_speakers(self):
        turns = split_by_speaker_turns("Some text here", [])
        assert len(turns) == 1
        assert turns[0]["text"] == "Some text here"

    def test_no_match(self):
        turns = split_by_speaker_turns("Just plain text", ["Alice"])
        assert len(turns) == 1


class TestGroupIntoChunks:

    def test_short_paragraphs_grouped(self):
        paras = ["Short one.", "Short two.", "Short three."]
        chunks = group_into_chunks(paras, target_words=500)
        assert len(chunks) == 1  # All fit in one chunk

    def test_long_paragraphs_split(self):
        long_para = "word " * 300  # 300 words
        paras = [long_para, long_para, long_para]
        chunks = group_into_chunks(paras, target_words=500)
        assert len(chunks) >= 2  # Should split across chunks

    def test_empty_input(self):
        chunks = group_into_chunks([], target_words=500)
        assert chunks == []

    def test_single_paragraph(self):
        chunks = group_into_chunks(["Hello world"], target_words=500)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"


# ---------------------------------------------------------------------------
# Merge logic tests
# ---------------------------------------------------------------------------

class TestMergeSegmentResults:

    def test_adds_new_codes(self):
        codebook = Codebook(methodology="grounded_theory")
        applications = []
        response = _make_segment_response(
            new_codes=[
                OpenCode(
                    code_name="AI Usage",
                    description="How AI is used",
                    properties=["automation"],
                    dimensions=["scope"],
                    supporting_quotes=["we use AI"],
                    frequency=1,
                    confidence=0.8,
                ),
            ],
        )
        segment = {"doc_id": "d1", "doc_name": "doc.txt", "text": "test", "speaker": ""}

        _merge_segment_results(codebook, applications, response, segment)
        assert len(codebook.codes) == 1
        assert codebook.codes[0].name == "AI Usage"

    def test_does_not_duplicate_codes(self):
        codebook = Codebook(
            methodology="grounded_theory",
            codes=[Code(id="AI_USAGE", name="AI Usage", description="existing")],
        )
        applications = []
        response = _make_segment_response(
            new_codes=[
                OpenCode(
                    code_name="AI Usage",  # same name
                    description="new description",
                    properties=[], dimensions=[],
                    supporting_quotes=[], frequency=1, confidence=0.8,
                ),
            ],
        )
        segment = {"doc_id": "d1", "doc_name": "doc.txt", "text": "test", "speaker": ""}

        _merge_segment_results(codebook, applications, response, segment)
        assert len(codebook.codes) == 1  # No duplicate

    def test_creates_applications(self):
        codebook = Codebook(
            methodology="grounded_theory",
            codes=[Code(id="AI_USAGE", name="AI Usage", description="desc")],
        )
        applications = []
        response = _make_segment_response(
            applications=[
                SegmentCodeApplication(
                    code_name="AI Usage",
                    quote="we use AI for everything",
                ),
            ],
        )
        segment = {"doc_id": "d1", "doc_name": "doc.txt", "text": "test", "speaker": "Alice"}

        _merge_segment_results(codebook, applications, response, segment)
        assert len(applications) == 1
        assert applications[0].code_id == "AI_USAGE"
        assert applications[0].doc_id == "d1"
        assert applications[0].speaker == "Alice"

    def test_applies_modifications(self):
        codebook = Codebook(
            methodology="grounded_theory",
            codes=[Code(id="AI_USAGE", name="AI Usage", description="old desc", properties=["p1"])],
        )
        applications = []
        response = _make_segment_response(
            modifications=[
                CodeModification(
                    code_name="AI Usage",
                    new_description="updated description",
                    new_properties=["p2"],
                ),
            ],
        )
        segment = {"doc_id": "d1", "doc_name": "doc.txt", "text": "test", "speaker": ""}

        _merge_segment_results(codebook, applications, response, segment)
        assert codebook.codes[0].description == "updated description"
        assert "p2" in codebook.codes[0].properties

    def test_increments_mention_count(self):
        codebook = Codebook(
            methodology="grounded_theory",
            codes=[Code(id="C1", name="Theme", description="d", mention_count=0)],
        )
        applications = []
        response = _make_segment_response(
            applications=[
                SegmentCodeApplication(code_name="Theme", quote="q1"),
                SegmentCodeApplication(code_name="Theme", quote="q2"),
            ],
        )
        segment = {"doc_id": "d1", "doc_name": "doc.txt", "text": "test", "speaker": ""}

        _merge_segment_results(codebook, applications, response, segment)
        assert codebook.codes[0].mention_count == 2


# ---------------------------------------------------------------------------
# Stage tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestGTConstantComparisonStage:

    def test_basic_execution(self):
        state = _make_state()

        call_count = 0
        def make_response(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First segment: create new codes
                return _make_segment_response(
                    new_codes=[
                        OpenCode(
                            code_name="AI Usage",
                            description="Use of AI",
                            properties=["automation"],
                            dimensions=["scope"],
                            supporting_quotes=["We use AI"],
                            frequency=1, confidence=0.8,
                        ),
                    ],
                    applications=[
                        SegmentCodeApplication(
                            code_name="AI Usage",
                            quote="We use AI for everything",
                        ),
                    ],
                    memo="Found AI usage theme",
                )
            else:
                # Subsequent segments: apply existing codes
                return _make_segment_response(
                    applications=[
                        SegmentCodeApplication(
                            code_name="AI Usage",
                            quote="It changed our workflow",
                        ),
                    ],
                )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=make_response)
            ctx = PipelineContext()
            result = asyncio.run(
                GTConstantComparisonStage(max_iterations=1).execute(
                    state, ctx
                )
            )

        assert len(result.codebook.codes) > 0
        assert len(result.code_applications) > 0
        assert result.iteration >= 1

    def test_saturation_stops_iteration(self):
        """Stage should stop when codebook stabilizes."""
        state = _make_state()

        # All segments return the same code — saturation after iteration 1
        stable_response = _make_segment_response(
            new_codes=[
                OpenCode(
                    code_name="Theme A",
                    description="A theme",
                    properties=[], dimensions=[],
                    supporting_quotes=["quote"],
                    frequency=1, confidence=0.8,
                ),
            ],
            applications=[
                SegmentCodeApplication(code_name="Theme A", quote="quote"),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=stable_response)
            ctx = PipelineContext()
            result = asyncio.run(
                GTConstantComparisonStage(max_iterations=5).execute(
                    state, ctx
                )
            )

        # Should stop before max_iterations due to saturation
        # (iteration 2 sees no change from iteration 1)
        assert result.iteration <= 3

    def test_memos_collected(self):
        state = _make_state()

        response = _make_segment_response(
            new_codes=[
                OpenCode(
                    code_name="Code A", description="d",
                    properties=[], dimensions=[],
                    supporting_quotes=["q"], frequency=1, confidence=0.7,
                ),
            ],
            memo="Interesting segment",
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            ctx = PipelineContext()
            result = asyncio.run(
                GTConstantComparisonStage(max_iterations=1).execute(
                    state, ctx
                )
            )

        memo_titles = [m.title for m in result.memos]
        assert "Constant Comparison Coding Memos" in memo_titles

    def test_stashes_open_codes_for_downstream(self):
        state = _make_state()

        response = _make_segment_response(
            new_codes=[
                OpenCode(
                    code_name="Code X", description="x",
                    properties=["p"], dimensions=["d"],
                    supporting_quotes=["q"], frequency=1, confidence=0.7,
                ),
            ],
        )

        ctx = PipelineContext()
        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            asyncio.run(
                GTConstantComparisonStage(max_iterations=1).execute(state, ctx)
            )

        assert ctx.gt_open_codes is not None
        assert ctx.gt_open_codes_text is not None

    def test_stage_name(self):
        assert GTConstantComparisonStage().name() == "gt_constant_comparison"

    def test_requires_human_review_flag(self):
        assert GTConstantComparisonStage(pause_for_review=True).requires_human_review() is True
        assert GTConstantComparisonStage(pause_for_review=False).requires_human_review() is False


# ---------------------------------------------------------------------------
# Pipeline factory integration
# ---------------------------------------------------------------------------

class TestPipelineFactory:

    def test_gt_pipeline_uses_constant_comparison(self):
        pipeline = create_pipeline("grounded_theory")
        stage_names = [s.name() for s in pipeline.stages]
        assert "gt_constant_comparison" in stage_names
        assert "gt_open_coding" not in stage_names

    def test_default_pipeline_unchanged(self):
        pipeline = create_pipeline("default")
        stage_names = [s.name() for s in pipeline.stages]
        assert "thematic_coding" in stage_names
        assert "gt_constant_comparison" not in stage_names
