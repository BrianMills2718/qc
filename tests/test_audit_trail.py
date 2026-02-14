"""
Tests for per-code reasoning (audit trail) and negative case analysis.

Covers:
- Reasoning field on LLM schemas (ThematicCode, OpenCode)
- Reasoning passthrough in adapters to domain Code
- Reasoning in CSV and markdown export
- Negative case stage execution (mocked LLM)
- Negative case stage skips when no codes
- Pipeline factory includes negative case stage
"""

import asyncio
import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.schemas.analysis_schemas import CodeHierarchy, ThematicCode
from qc_clean.schemas.gt_schemas import OpenCode
from qc_clean.schemas.domain import (
    AnalysisMemo,
    Code,
    Codebook,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
    Provenance,
)
from qc_clean.schemas.adapters import code_hierarchy_to_codebook, open_codes_to_codebook
from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.stages.negative_case import (
    NegativeCase,
    NegativeCaseResponse,
    NegativeCaseStage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**kwargs) -> ProjectState:
    defaults = dict(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(name="doc1.txt", content="Interview content about AI and work."),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def _sample_thematic_code(**overrides) -> ThematicCode:
    defaults = dict(
        id="AI_ADOPTION",
        name="AI Adoption",
        description="How organizations adopt AI",
        semantic_definition="References to AI implementation decisions",
        level=0,
        example_quotes=["We started using AI last year"],
        mention_count=5,
        discovery_confidence=0.8,
        reasoning="Multiple participants discussed AI adoption decisions in detail.",
    )
    defaults.update(overrides)
    return ThematicCode(**defaults)


def _sample_open_code(**overrides) -> OpenCode:
    defaults = dict(
        code_name="AI Adoption",
        description="How organizations adopt AI",
        properties=["adoption_speed", "resistance"],
        dimensions=["fast vs slow"],
        supporting_quotes=["We started using AI last year"],
        frequency=5,
        confidence=0.8,
        reasoning="Recurring pattern across interviews about organizational change.",
    )
    defaults.update(overrides)
    return OpenCode(**defaults)


# ---------------------------------------------------------------------------
# Reasoning field schema tests
# ---------------------------------------------------------------------------

class TestReasoningField:
    def test_thematic_code_default_empty(self):
        tc = ThematicCode(
            id="X", name="X", description="X", semantic_definition="X",
            level=0, example_quotes=["q"], mention_count=1,
            discovery_confidence=0.5,
        )
        assert tc.reasoning == ""

    def test_thematic_code_with_reasoning(self):
        tc = _sample_thematic_code()
        assert "Multiple participants" in tc.reasoning

    def test_open_code_default_empty(self):
        oc = OpenCode(
            code_name="X", description="X", properties=["p"],
            dimensions=["d"], supporting_quotes=["q"],
            frequency=1, confidence=0.5,
        )
        assert oc.reasoning == ""

    def test_open_code_with_reasoning(self):
        oc = _sample_open_code()
        assert "Recurring pattern" in oc.reasoning

    def test_domain_code_default_empty(self):
        c = Code(name="test")
        assert c.reasoning == ""

    def test_domain_code_with_reasoning(self):
        c = Code(name="test", reasoning="Because data.")
        assert c.reasoning == "Because data."


# ---------------------------------------------------------------------------
# Adapter passthrough tests
# ---------------------------------------------------------------------------

class TestReasoningAdapterPassthrough:
    def test_code_hierarchy_adapter_passes_reasoning(self):
        tc = _sample_thematic_code()
        hierarchy = CodeHierarchy(
            codes=[tc], total_codes=1, analysis_confidence=0.9,
        )
        codebook = code_hierarchy_to_codebook(hierarchy)
        assert codebook.codes[0].reasoning == tc.reasoning

    def test_open_codes_adapter_passes_reasoning(self):
        oc = _sample_open_code()
        codebook = open_codes_to_codebook([oc])
        assert codebook.codes[0].reasoning == oc.reasoning

    def test_empty_reasoning_passes_through(self):
        tc = _sample_thematic_code(reasoning="")
        hierarchy = CodeHierarchy(
            codes=[tc], total_codes=1, analysis_confidence=0.9,
        )
        codebook = code_hierarchy_to_codebook(hierarchy)
        assert codebook.codes[0].reasoning == ""


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

class TestReasoningExport:
    def test_csv_includes_reasoning_column(self, tmp_path):
        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="AI", description="test", reasoning="Strong data pattern."),
            ]),
        )
        paths = ProjectExporter().export_csv(state, str(tmp_path))
        codes_path = [p for p in paths if "codes.csv" in p][0]

        with open(codes_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "reasoning" in rows[0]
        assert rows[0]["reasoning"] == "Strong data pattern."

    def test_markdown_includes_audit_trail(self, tmp_path):
        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="AI", description="test", reasoning="Strong data pattern."),
                Code(name="Work", description="test2", reasoning="Frequent mentions."),
            ]),
        )
        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()

        assert "## Audit Trail" in content
        assert "**AI**: Strong data pattern." in content
        assert "**Work**: Frequent mentions." in content

    def test_markdown_no_audit_trail_when_no_reasoning(self, tmp_path):
        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="AI", description="test"),
            ]),
        )
        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()

        assert "## Audit Trail" not in content


# ---------------------------------------------------------------------------
# Negative case stage tests
# ---------------------------------------------------------------------------

class TestNegativeCaseStage:
    def test_produces_memo(self):
        mock_response = NegativeCaseResponse(
            negative_cases=[
                NegativeCase(
                    code_name="AI Adoption",
                    disconfirming_evidence="One participant said they abandoned AI.",
                    explanation="This contradicts the positive adoption narrative.",
                    implication="The code may need a sub-category for failed adoptions.",
                ),
            ],
            overall_assessment="The codebook fits most data well but misses adoption failures.",
            analytical_memo="Found important counter-evidence.",
        )

        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="AI Adoption", description="test"),
            ]),
        )
        ctx = PipelineContext()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                NegativeCaseStage().execute(state, ctx)
            )

        # Should have negative case memo + analytical memo
        assert len(result.memos) == 2
        nc_memo = [m for m in result.memos if m.memo_type == "negative_case"][0]
        assert "Negative Case Analysis" in nc_memo.title
        assert "abandoned AI" in nc_memo.content
        assert "adoption failures" in nc_memo.content

        ana_memo = [m for m in result.memos if m.title == "Negative Case Analysis Memo"][0]
        assert "counter-evidence" in ana_memo.content

    def test_skips_when_no_codes(self):
        state = _make_state()  # empty codebook
        stage = NegativeCaseStage()
        assert stage.can_execute(state) is False

    def test_runs_when_codes_exist(self):
        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="test", description="test"),
            ]),
        )
        stage = NegativeCaseStage()
        assert stage.can_execute(state) is True

    def test_no_analytical_memo_when_empty(self):
        mock_response = NegativeCaseResponse(
            negative_cases=[],
            overall_assessment="Codebook fits well.",
            analytical_memo="",
        )

        state = _make_state(
            codebook=Codebook(codes=[
                Code(name="test", description="test"),
            ]),
        )
        ctx = PipelineContext()

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                NegativeCaseStage().execute(state, ctx)
            )

        # Should have negative case memo only (no analytical memo)
        assert len(result.memos) == 1
        assert result.memos[0].memo_type == "negative_case"


# ---------------------------------------------------------------------------
# Pipeline factory tests
# ---------------------------------------------------------------------------

class TestPipelineFactoryIncludesNegativeCase:
    def test_default_pipeline_has_negative_case(self):
        from qc_clean.core.pipeline.pipeline_factory import create_pipeline
        pipeline = create_pipeline("default")
        stage_names = [s.name() for s in pipeline.stages]
        assert "negative_case_analysis" in stage_names
        # Should be after synthesis, before cross_interview
        synth_idx = stage_names.index("synthesis")
        nc_idx = stage_names.index("negative_case_analysis")
        assert nc_idx > synth_idx

    def test_gt_pipeline_has_negative_case(self):
        from qc_clean.core.pipeline.pipeline_factory import create_pipeline
        pipeline = create_pipeline("grounded_theory")
        stage_names = [s.name() for s in pipeline.stages]
        assert "negative_case_analysis" in stage_names
        # Should be after gt_theory_integration, before cross_interview
        theory_idx = stage_names.index("gt_theory_integration")
        nc_idx = stage_names.index("negative_case_analysis")
        assert nc_idx > theory_idx
