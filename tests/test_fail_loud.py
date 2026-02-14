"""
Tests for fail-loud behavior.

Verifies that the system raises errors instead of silently producing
wrong output when upstream data is missing or invalid.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.pipeline.pipeline_engine import require_config
from qc_clean.core.pipeline.review import ReviewManager
from qc_clean.schemas.domain import (
    Code,
    Codebook,
    Corpus,
    Document,
    HumanReviewDecision,
    ProjectState,
    ReviewAction,
)


# ---------------------------------------------------------------------------
# require_config
# ---------------------------------------------------------------------------

class TestRequireConfig:

    def test_returns_value_when_present(self):
        config = {"_phase1_json": '{"codes": []}'}
        result = require_config(config, "_phase1_json", "perspective")
        assert result == '{"codes": []}'

    def test_raises_on_missing_key(self):
        config = {"model_name": "gpt-5-mini"}
        with pytest.raises(RuntimeError, match="requires config key '_phase1_json'"):
            require_config(config, "_phase1_json", "perspective")

    def test_raises_on_empty_string(self):
        config = {"_phase1_json": ""}
        with pytest.raises(RuntimeError, match="requires config key '_phase1_json'"):
            require_config(config, "_phase1_json", "perspective")

    def test_raises_on_none_value(self):
        config = {"_phase1_json": None}
        with pytest.raises(RuntimeError, match="requires config key '_phase1_json'"):
            require_config(config, "_phase1_json", "perspective")

    def test_error_message_includes_stage_name(self):
        config = {}
        with pytest.raises(RuntimeError, match="Stage 'synthesis'"):
            require_config(config, "_phase3_json", "synthesis")


# ---------------------------------------------------------------------------
# Downstream stages fail on missing config
# ---------------------------------------------------------------------------

class TestStageConfigDependencies:
    """Verify that downstream stages raise when upstream config is missing."""

    def _make_state(self):
        return ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="doc.txt", content="Some interview text."),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="Theme", description="A theme"),
            ]),
        )

    def test_perspective_requires_phase1(self):
        from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

        state = self._make_state()
        config = {"model_name": "gpt-5-mini"}  # missing _phase1_json

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_phase1_json"):
                asyncio.run(PerspectiveStage().execute(state, config))

    def test_relationship_requires_phase1_and_phase2(self):
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        state = self._make_state()
        config = {"model_name": "gpt-5-mini"}  # missing both

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_phase1_json"):
                asyncio.run(RelationshipStage().execute(state, config))

    def test_synthesis_requires_all_phases(self):
        from qc_clean.core.pipeline.stages.synthesis import SynthesisStage

        state = self._make_state()
        config = {"model_name": "gpt-5-mini"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_phase1_json"):
                asyncio.run(SynthesisStage().execute(state, config))

    def test_gt_axial_requires_open_codes(self):
        from qc_clean.core.pipeline.stages.gt_axial_coding import GTAxialCodingStage

        state = self._make_state()
        config = {"model_name": "gpt-5-mini"}  # missing _gt_open_codes_text

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_gt_open_codes_text"):
                asyncio.run(GTAxialCodingStage().execute(state, config))

    def test_gt_selective_requires_open_codes_and_axial(self):
        from qc_clean.core.pipeline.stages.gt_selective_coding import GTSelectiveCodingStage

        state = self._make_state()
        config = {"model_name": "gpt-5-mini"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_gt_open_codes_text"):
                asyncio.run(GTSelectiveCodingStage().execute(state, config))

    def test_gt_theory_requires_all_gt_phases(self):
        from qc_clean.core.pipeline.stages.gt_theory_integration import GTTheoryIntegrationStage

        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="doc.txt", content="Text"),
            ]),
            codebook=Codebook(codes=[
                Code(id="C1", name="Theme", description="A theme"),
            ]),
            core_categories=[{"category_name": "CC1", "definition": "def"}],
        )
        config = {"model_name": "gpt-5-mini"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="_gt_open_codes_text"):
                asyncio.run(GTTheoryIntegrationStage().execute(state, config))


# ---------------------------------------------------------------------------
# Review fail-loud
# ---------------------------------------------------------------------------

class TestReviewFailLoud:

    def _make_state(self):
        return ProjectState(
            codebook=Codebook(codes=[
                Code(id="C1", name="Theme A", description="desc"),
            ]),
        )

    def test_unknown_target_type_raises(self):
        state = self._make_state()
        mgr = ReviewManager(state)

        decision = HumanReviewDecision(
            target_type="nonexistent",
            target_id="C1",
            action=ReviewAction.APPROVE,
        )
        with pytest.raises(ValueError, match="Unknown target_type"):
            mgr.apply_decision(decision)

    def test_unsupported_application_action_raises(self):
        state = self._make_state()
        mgr = ReviewManager(state)

        decision = HumanReviewDecision(
            target_type="code_application",
            target_id="app1",
            action=ReviewAction.MERGE,  # not supported for applications
        )
        with pytest.raises(ValueError, match="not supported for code_application"):
            mgr.apply_decision(decision)

    def test_unsupported_codebook_action_raises(self):
        state = self._make_state()
        mgr = ReviewManager(state)

        decision = HumanReviewDecision(
            target_type="codebook",
            target_id="cb1",
            action=ReviewAction.REJECT,  # not supported for codebook
        )
        with pytest.raises(ValueError, match="not supported for codebook"):
            mgr.apply_decision(decision)

    def test_valid_actions_still_work(self):
        state = self._make_state()
        mgr = ReviewManager(state)

        # Approve code — should not raise
        decision = HumanReviewDecision(
            target_type="code",
            target_id="C1",
            action=ReviewAction.APPROVE,
        )
        mgr.apply_decision(decision)
        assert state.codebook.codes[0].provenance.value == "human"


# ---------------------------------------------------------------------------
# Constant comparison fail-loud on empty segments
# ---------------------------------------------------------------------------

class TestConstantComparisonFailLoud:

    def test_raises_on_empty_documents(self):
        from qc_clean.core.pipeline.stages.gt_constant_comparison import GTConstantComparisonStage

        state = ProjectState(
            corpus=Corpus(documents=[
                Document(id="d1", name="empty.txt", content=""),
            ]),
        )
        config = {"model_name": "gpt-5-mini"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler"):
            with pytest.raises(RuntimeError, match="No segments found"):
                asyncio.run(
                    GTConstantComparisonStage(max_iterations=1).execute(state, config)
                )
