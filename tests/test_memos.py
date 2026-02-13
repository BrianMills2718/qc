"""
Tests for analytical memo generation across pipeline stages and exports.

Covers:
- Schema tests: analytical_memo field is optional, parses correctly
- Stage extraction tests: each stage produces a memo when LLM returns one
- Export tests: markdown and CSV include memos
"""

import asyncio
import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.schemas.analysis_schemas import (
    AnalysisSynthesis,
    CodeHierarchy,
    EntityMapping,
    SpeakerAnalysis,
)
from qc_clean.schemas.gt_schemas import TheoreticalModel
from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
from qc_clean.core.pipeline.stages.gt_axial_coding import AxialRelationshipsResponse
from qc_clean.core.pipeline.stages.gt_selective_coding import CoreCategoriesResponse
from qc_clean.core.export.data_exporter import ProjectExporter
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**kwargs) -> ProjectState:
    """Create a minimal ProjectState for testing."""
    defaults = dict(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(name="doc1.txt", content="Interview content here about AI and work."),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def _make_gt_state(**kwargs) -> ProjectState:
    """Create a minimal GT ProjectState for testing."""
    defaults = dict(
        name="test_gt_project",
        config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
        corpus=Corpus(documents=[
            Document(name="doc1.txt", content="Interview content here about AI and work."),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestAnalyticalMemoField:
    """Test that analytical_memo field works correctly on all schemas."""

    def test_code_hierarchy_default_empty(self):
        ch = CodeHierarchy(codes=[], total_codes=0, analysis_confidence=0.9)
        assert ch.analytical_memo == ""

    def test_code_hierarchy_with_memo(self):
        ch = CodeHierarchy(
            codes=[], total_codes=0, analysis_confidence=0.9,
            analytical_memo="Key decisions made during coding."
        )
        assert ch.analytical_memo == "Key decisions made during coding."

    def test_speaker_analysis_default_empty(self):
        sa = SpeakerAnalysis(
            participants=[], consensus_themes=[], divergent_viewpoints=[],
            perspective_mapping={},
        )
        assert sa.analytical_memo == ""

    def test_entity_mapping_default_empty(self):
        em = EntityMapping(
            entities=[], relationships=[],
            cause_effect_chains=[], conceptual_connections=[],
        )
        assert em.analytical_memo == ""

    def test_analysis_synthesis_default_empty(self):
        s = AnalysisSynthesis(
            executive_summary="test", key_findings=[],
            cross_cutting_patterns=[], actionable_recommendations=[],
            confidence_assessment={},
        )
        assert s.analytical_memo == ""

    def test_theoretical_model_default_empty(self):
        tm = TheoreticalModel(
            model_name="test", core_categories=["cat"],
            theoretical_framework="fw", propositions=[],
            conceptual_relationships=[], scope_conditions=[],
            implications=[], future_research=[],
        )
        assert tm.analytical_memo == ""

    def test_open_codes_response_default_empty(self):
        ocr = OpenCodesResponse(open_codes=[])
        assert ocr.analytical_memo == ""

    def test_axial_relationships_response_default_empty(self):
        arr = AxialRelationshipsResponse(axial_relationships=[])
        assert arr.analytical_memo == ""

    def test_core_categories_response_default_empty(self):
        ccr = CoreCategoriesResponse(core_categories=[])
        assert ccr.analytical_memo == ""

    def test_round_trip_json(self):
        """analytical_memo survives JSON serialization/deserialization."""
        ch = CodeHierarchy(
            codes=[], total_codes=0, analysis_confidence=0.9,
            analytical_memo="Round-trip test memo."
        )
        json_str = ch.model_dump_json()
        parsed = CodeHierarchy.model_validate_json(json_str)
        assert parsed.analytical_memo == "Round-trip test memo."

    def test_parse_without_memo_field(self):
        """Parsing JSON without analytical_memo uses default."""
        data = {"codes": [], "total_codes": 0, "analysis_confidence": 0.9}
        ch = CodeHierarchy.model_validate(data)
        assert ch.analytical_memo == ""


# ---------------------------------------------------------------------------
# Stage extraction tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestThematicCodingStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        mock_response = CodeHierarchy(
            codes=[], total_codes=0, analysis_confidence=0.8,
            analytical_memo="Thematic coding revealed strong AI themes.",
        )

        state = _make_state()
        config = {}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                ThematicCodingStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Thematic Coding Analysis Memo"
        assert result.memos[0].memo_type == "coding"
        assert "AI themes" in result.memos[0].content

    def test_no_memo_when_empty(self):
        from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage

        mock_response = CodeHierarchy(
            codes=[], total_codes=0, analysis_confidence=0.8,
            analytical_memo="",
        )

        state = _make_state()
        config = {}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                ThematicCodingStage().execute(state, config)
            )

        assert len(result.memos) == 0


class TestPerspectiveStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.perspective import PerspectiveStage

        mock_response = SpeakerAnalysis(
            participants=[], consensus_themes=[], divergent_viewpoints=[],
            perspective_mapping={},
            analytical_memo="Speaker analysis identified tensions.",
        )

        state = _make_state()
        config = {"_phase1_json": "{}"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                PerspectiveStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Perspective Analysis Memo"
        assert result.memos[0].memo_type == "pattern"


class TestRelationshipStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.relationship import RelationshipStage

        mock_response = EntityMapping(
            entities=["AI", "Work"],
            relationships=[],
            cause_effect_chains=["AI leads to efficiency"],
            conceptual_connections=["AI connects to work"],
            analytical_memo="Relationship mapping found clear causal chain.",
        )

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                RelationshipStage().execute(state, config)
            )

        # Should have LLM analytical memo + causal chains memo
        memo_titles = [m.title for m in result.memos]
        assert "Relationship Mapping Memo" in memo_titles
        assert "Causal Chains & Conceptual Connections" in memo_titles


class TestSynthesisStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.synthesis import SynthesisStage

        mock_response = AnalysisSynthesis(
            executive_summary="Summary",
            key_findings=["finding1"],
            cross_cutting_patterns=["pattern1"],
            actionable_recommendations=[],
            confidence_assessment={},
            analytical_memo="Synthesis integrated all phases coherently.",
        )

        state = _make_state()
        config = {"_phase1_json": "{}", "_phase2_json": "{}", "_phase3_json": "{}"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                SynthesisStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Synthesis & Recommendations Memo"
        assert result.memos[0].memo_type == "theoretical"


class TestGTOpenCodingStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage

        mock_response = OpenCodesResponse(
            open_codes=[],
            analytical_memo="Open coding surfaced unexpected themes.",
        )

        state = _make_gt_state()
        config = {}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                GTOpenCodingStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Open Coding Memo"
        assert result.memos[0].memo_type == "coding"


class TestGTAxialCodingStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.gt_axial_coding import GTAxialCodingStage

        mock_response = AxialRelationshipsResponse(
            axial_relationships=[],
            analytical_memo="Axial coding revealed paradigm model.",
        )

        state = _make_gt_state(
            codebook=Codebook(codes=[
                Code(name="test_code", description="test"),
            ]),
        )
        config = {"_gt_open_codes_text": "test codes"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                GTAxialCodingStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Axial Coding Memo"
        assert result.memos[0].memo_type == "methodological"


class TestGTSelectiveCodingStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.gt_selective_coding import GTSelectiveCodingStage
        from qc_clean.schemas.gt_schemas import CoreCategory

        mock_response = CoreCategoriesResponse(
            core_categories=[
                CoreCategory(
                    category_name="Core1",
                    definition="Definition",
                    central_phenomenon="Phenomenon",
                    related_categories=["cat1"],
                    theoretical_properties=["prop1"],
                    explanatory_power="High",
                    integration_rationale="Central",
                ),
            ],
            analytical_memo="Selective coding identified the core phenomenon.",
        )

        state = _make_gt_state(
            codebook=Codebook(codes=[
                Code(name="test_code", description="test"),
            ]),
        )
        config = {"_gt_open_codes_text": "codes", "_gt_axial_text": "axial"}

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                GTSelectiveCodingStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Selective Coding Memo"
        assert result.memos[0].memo_type == "theoretical"


class TestGTTheoryIntegrationStageMemo:
    def test_memo_extracted(self):
        from qc_clean.core.pipeline.stages.gt_theory_integration import GTTheoryIntegrationStage
        from qc_clean.schemas.domain import CoreCategoryResult

        mock_response = TheoreticalModel(
            model_name="Test Theory",
            core_categories=["cat1"],
            theoretical_framework="Framework",
            propositions=["p1"],
            conceptual_relationships=["r1"],
            scope_conditions=["s1"],
            implications=["i1"],
            future_research=["f1"],
            analytical_memo="Theory integration produced a coherent model.",
        )

        state = _make_gt_state(
            core_categories=[
                CoreCategoryResult(
                    category_name="Core1",
                    definition="def",
                    central_phenomenon="phen",
                    related_categories=["cat"],
                    theoretical_properties=["prop"],
                    explanatory_power="high",
                    integration_rationale="rationale",
                ),
            ],
        )
        config = {
            "_gt_open_codes_text": "codes",
            "_gt_axial_text": "axial",
            "_gt_core_text": "core",
        }

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(
                GTTheoryIntegrationStage().execute(state, config)
            )

        assert len(result.memos) == 1
        assert result.memos[0].title == "Theory Integration Memo"
        assert result.memos[0].memo_type == "theoretical"


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

class TestMarkdownExportMemos:
    def test_memos_included_in_markdown(self, tmp_path):
        state = _make_state(
            memos=[
                AnalysisMemo(
                    memo_type="coding",
                    title="Thematic Coding Analysis Memo",
                    content="Found strong AI themes in interview data.",
                ),
                AnalysisMemo(
                    memo_type="pattern",
                    title="Perspective Analysis Memo",
                    content="Speaker showed internal tensions.",
                ),
            ],
        )

        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()

        assert "## Analytical Memos" in content
        assert "### Thematic Coding Analysis Memo" in content
        assert "Found strong AI themes" in content
        assert "### Perspective Analysis Memo" in content
        assert "*Type: coding" in content
        assert "*Type: pattern" in content

    def test_no_memo_section_when_empty(self, tmp_path):
        state = _make_state()

        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()

        assert "## Analytical Memos" not in content


class TestCSVExportMemos:
    def test_memos_csv_created(self, tmp_path):
        state = _make_state(
            memos=[
                AnalysisMemo(
                    memo_type="coding",
                    title="Test Memo",
                    content="Memo content here.",
                    code_refs=["CODE_1", "CODE_2"],
                    doc_refs=["doc1"],
                ),
            ],
        )

        paths = ProjectExporter().export_csv(state, str(tmp_path))
        memo_paths = [p for p in paths if "memos.csv" in p]
        assert len(memo_paths) == 1

        with open(memo_paths[0], newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["memo_type"] == "coding"
        assert rows[0]["title"] == "Test Memo"
        assert rows[0]["content"] == "Memo content here."
        assert rows[0]["code_refs"] == "CODE_1;CODE_2"

    def test_no_memos_csv_when_empty(self, tmp_path):
        state = _make_state()

        paths = ProjectExporter().export_csv(state, str(tmp_path))
        memo_paths = [p for p in paths if "memos.csv" in p]
        assert len(memo_paths) == 0
