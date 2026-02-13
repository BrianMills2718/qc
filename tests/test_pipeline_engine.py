"""
Tests for the pipeline engine (qc_clean.core.pipeline).
Uses mock stages to test orchestration logic without LLM calls.
"""

import pytest
import asyncio

from qc_clean.schemas.domain import (
    AnalysisPhaseResult,
    Code,
    Codebook,
    Corpus,
    Document,
    PipelineStatus,
    ProjectState,
)
from qc_clean.core.pipeline.pipeline_engine import AnalysisPipeline, PipelineStage


# ---------------------------------------------------------------------------
# Mock stages
# ---------------------------------------------------------------------------

class PassthroughStage(PipelineStage):
    def __init__(self, stage_name: str):
        self._name = stage_name

    def name(self) -> str:
        return self._name

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.data_warnings.append(f"executed:{self._name}")
        return state


class ReviewStage(PipelineStage):
    """Stage that pauses for human review."""
    def __init__(self, stage_name: str):
        self._name = stage_name

    def name(self) -> str:
        return self._name

    def requires_human_review(self) -> bool:
        return True

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.data_warnings.append(f"executed:{self._name}")
        return state


class ConditionalStage(PipelineStage):
    """Stage that skips if codebook is empty."""
    def name(self) -> str:
        return "conditional"

    def can_execute(self, state: ProjectState) -> bool:
        return len(state.codebook.codes) > 0

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        state.data_warnings.append("executed:conditional")
        return state


class FailingStage(PipelineStage):
    def name(self) -> str:
        return "failing"

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        raise RuntimeError("Stage failed!")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAnalysisPipeline:
    def test_empty_pipeline(self):
        pipeline = AnalysisPipeline(stages=[])
        state = ProjectState()
        result = asyncio.run(
            pipeline.run(state, {})
        )
        assert result.pipeline_status == PipelineStatus.COMPLETED

    def test_sequential_execution(self):
        stages = [PassthroughStage("a"), PassthroughStage("b"), PassthroughStage("c")]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()

        result = asyncio.run(
            pipeline.run(state, {})
        )

        assert result.pipeline_status == PipelineStatus.COMPLETED
        assert result.data_warnings == ["executed:a", "executed:b", "executed:c"]
        assert len(result.phase_results) == 3
        assert all(pr.status == PipelineStatus.COMPLETED for pr in result.phase_results)

    def test_pause_for_review(self):
        stages = [PassthroughStage("first"), ReviewStage("review"), PassthroughStage("after")]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()

        result = asyncio.run(
            pipeline.run(state, {})
        )

        # Should pause after the review stage
        assert result.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW
        assert result.current_phase == "review"
        # The "after" stage should NOT have executed
        assert "executed:after" not in result.data_warnings
        assert "executed:review" in result.data_warnings

    def test_resume_after_review(self):
        stages = [PassthroughStage("first"), ReviewStage("review"), PassthroughStage("after")]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()

        # First run - pauses at review
        state = asyncio.run(
            pipeline.run(state, {})
        )
        assert state.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW

        # Resume from review
        state = asyncio.run(
            pipeline.run(state, {}, resume_from="review")
        )
        assert state.pipeline_status == PipelineStatus.COMPLETED
        assert "executed:after" in state.data_warnings

    def test_conditional_skip(self):
        stages = [ConditionalStage()]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()  # empty codebook

        result = asyncio.run(
            pipeline.run(state, {})
        )

        assert result.pipeline_status == PipelineStatus.COMPLETED
        assert "executed:conditional" not in result.data_warnings
        assert result.phase_results[0].status == PipelineStatus.SKIPPED

    def test_conditional_executes_when_met(self):
        stages = [ConditionalStage()]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState(
            codebook=Codebook(codes=[Code(id="C1", name="Theme")])
        )

        result = asyncio.run(
            pipeline.run(state, {})
        )

        assert result.pipeline_status == PipelineStatus.COMPLETED
        assert "executed:conditional" in result.data_warnings

    def test_failing_stage(self):
        stages = [PassthroughStage("good"), FailingStage()]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()

        with pytest.raises(RuntimeError, match="Stage failed!"):
            asyncio.run(
                pipeline.run(state, {})
            )

        # The good stage should have completed, failing stage should be failed
        assert state.pipeline_status == PipelineStatus.FAILED
        good_result = state.get_phase_result("good")
        assert good_result.status == PipelineStatus.COMPLETED
        fail_result = state.get_phase_result("failing")
        assert fail_result.status == PipelineStatus.FAILED
        assert "Stage failed!" in fail_result.error_message

    def test_phase_results_recorded(self):
        stages = [PassthroughStage("stage1")]
        pipeline = AnalysisPipeline(stages=stages)
        state = ProjectState()

        result = asyncio.run(
            pipeline.run(state, {})
        )

        pr = result.get_phase_result("stage1")
        assert pr is not None
        assert pr.status == PipelineStatus.COMPLETED
        assert pr.started_at is not None
        assert pr.completed_at is not None

    def test_on_stage_complete_callback(self):
        callback_log = []

        async def on_complete(state):
            callback_log.append(state.current_phase)

        stages = [PassthroughStage("a"), PassthroughStage("b")]
        pipeline = AnalysisPipeline(stages=stages, on_stage_complete=on_complete)
        state = ProjectState()

        asyncio.run(
            pipeline.run(state, {})
        )

        assert callback_log == ["a", "b"]


class TestPipelineFactory:
    def test_create_default_pipeline(self):
        from qc_clean.core.pipeline.pipeline_factory import create_pipeline
        pipeline = create_pipeline(methodology="default")
        assert len(pipeline.stages) == 6
        names = [s.name() for s in pipeline.stages]
        assert names == [
            "ingest", "thematic_coding", "perspective",
            "relationship", "synthesis", "cross_interview",
        ]

    def test_create_gt_pipeline(self):
        from qc_clean.core.pipeline.pipeline_factory import create_pipeline
        pipeline = create_pipeline(methodology="grounded_theory")
        assert len(pipeline.stages) == 6
        names = [s.name() for s in pipeline.stages]
        assert names == [
            "ingest",
            "gt_open_coding",
            "gt_axial_coding",
            "gt_selective_coding",
            "gt_theory_integration",
            "cross_interview",
        ]

    def test_human_review_stages(self):
        from qc_clean.core.pipeline.pipeline_factory import create_pipeline
        pipeline = create_pipeline(methodology="default", enable_human_review=True)
        coding_stage = pipeline.stages[1]
        assert coding_stage.requires_human_review() is True


class TestIngestStage:
    def test_ingest_basic(self):
        from qc_clean.core.pipeline.stages.ingest import IngestStage

        stage = IngestStage()
        state = ProjectState()
        config = {
            "interviews": [
                {"name": "test.txt", "content": "Hello world."},
                {"name": "truncated.txt", "content": "This ends mid-sentence with"},
            ]
        }

        result = asyncio.run(
            stage.execute(state, config)
        )

        assert result.corpus.num_documents == 2
        assert result.corpus.documents[0].name == "test.txt"
        assert result.corpus.documents[0].is_truncated is False
        assert result.corpus.documents[1].is_truncated is True
        assert len(result.data_warnings) == 1
        assert "truncated" in result.data_warnings[0]

    def test_ingest_skip_if_populated(self):
        from qc_clean.core.pipeline.stages.ingest import IngestStage

        stage = IngestStage()
        state = ProjectState(
            corpus=Corpus(documents=[Document(name="existing.txt", content="data")])
        )

        result = asyncio.run(
            stage.execute(state, {})
        )

        # Should not overwrite existing corpus
        assert result.corpus.num_documents == 1
        assert result.corpus.documents[0].name == "existing.txt"

    def test_speaker_detection(self):
        from qc_clean.core.pipeline.stages.ingest import IngestStage

        stage = IngestStage()
        state = ProjectState()
        config = {
            "interviews": [{
                "name": "interview.txt",
                "content": "Interviewer: How are you?\nJane Smith: I'm doing great.\nInterviewer: Tell me more.\nJane Smith: Sure thing.",
            }]
        }

        result = asyncio.run(
            stage.execute(state, config)
        )

        doc = result.corpus.documents[0]
        assert "Interviewer" in doc.detected_speakers
        assert "Jane Smith" in doc.detected_speakers

    def test_speaker_detection_timestamp_format(self):
        from qc_clean.core.pipeline.stages.ingest import IngestStage

        stage = IngestStage()
        state = ProjectState()
        config = {
            "interviews": [{
                "name": "focus_group.txt",
                "content": "Todd Helmus   0:03\nSome dialog here.\n\nJane Doe   1:45\nMore dialog.\n\nTodd Helmus   3:22\nBack again.",
            }]
        }

        result = asyncio.run(
            stage.execute(state, config)
        )

        doc = result.corpus.documents[0]
        assert "Todd Helmus" in doc.detected_speakers
        assert "Jane Doe" in doc.detected_speakers
        assert len(doc.detected_speakers) == 2

    def test_speaker_detection_on_preloaded_docs(self):
        from qc_clean.core.pipeline.stages.ingest import IngestStage

        stage = IngestStage()
        # Simulate add-docs: corpus already populated, no speakers detected
        state = ProjectState(
            corpus=Corpus(documents=[
                Document(
                    name="interview.txt",
                    content="Alice Smith   0:01\nHello.\n\nBob Jones   0:05\nHi.",
                    detected_speakers=[],
                )
            ])
        )

        result = asyncio.run(
            stage.execute(state, {})
        )

        doc = result.corpus.documents[0]
        assert "Alice Smith" in doc.detected_speakers
        assert "Bob Jones" in doc.detected_speakers


class TestResumeValidation:
    """Regression tests for resume_from validation."""

    def test_invalid_resume_from_raises(self):
        """Invalid resume_from should raise ValueError, not silently skip."""
        pipeline = AnalysisPipeline(stages=[
            PassthroughStage("stage1"),
            PassthroughStage("stage2"),
        ])
        state = ProjectState(name="test")

        with pytest.raises(ValueError, match="Invalid resume_from"):
            asyncio.run(
                pipeline.run(state, {}, resume_from="nonexistent_stage")
            )

    def test_valid_resume_from_works(self):
        """Valid resume_from should skip prior stages and run the rest."""
        pipeline = AnalysisPipeline(stages=[
            PassthroughStage("stage1"),
            PassthroughStage("stage2"),
            PassthroughStage("stage3"),
        ])
        state = ProjectState(name="test")

        result = asyncio.run(
            pipeline.run(state, {}, resume_from="stage1")
        )
        # stage1 skipped, stage2+3 run => 2 phase results
        assert len(result.phase_results) == 2
        assert result.phase_results[0].phase_name == "stage2"
        assert result.phase_results[1].phase_name == "stage3"
