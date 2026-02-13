"""
Tests for multi-run stability analysis.

Covers:
- Pure functions: compute_code_stability, classify_stability
- Orchestrator: run_stability_analysis with mocked LLM
- Export: markdown and CSV include stability results
"""

import asyncio
import csv
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.pipeline.irr import (
    build_coding_matrix,
    classify_stability,
    compute_code_stability,
    normalize_code_name,
    run_stability_analysis,
)
from qc_clean.schemas.analysis_schemas import CodeHierarchy, ThematicCode
from qc_clean.schemas.domain import (
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
    StabilityResult,
)
from qc_clean.core.export.data_exporter import ProjectExporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_state(**kwargs) -> ProjectState:
    defaults = dict(
        name="test_project",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[
            Document(
                name="interview1.txt",
                content="We use AI for everything. It changed our workflow.",
            ),
        ]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def _make_code_hierarchy(code_names: list[str]) -> CodeHierarchy:
    """Build a CodeHierarchy with the given code names."""
    codes = [
        ThematicCode(
            id=name.upper().replace(" ", "_"),
            name=name,
            description=f"Description of {name}",
            semantic_definition=f"Definition of {name}",
            level=0,
            example_quotes=[f"Quote about {name.lower()}"],
            mention_count=3,
            discovery_confidence=0.7,
        )
        for name in code_names
    ]
    return CodeHierarchy(
        codes=codes,
        total_codes=len(codes),
        analysis_confidence=0.8,
    )


# ---------------------------------------------------------------------------
# Pure function tests
# ---------------------------------------------------------------------------

class TestComputeCodeStability:

    def test_all_present(self):
        matrix = {"code_a": [1, 1, 1, 1, 1]}
        result = compute_code_stability(matrix)
        assert result["code_a"] == 1.0

    def test_all_absent(self):
        matrix = {"code_a": [0, 0, 0, 0, 0]}
        result = compute_code_stability(matrix)
        assert result["code_a"] == 0.0

    def test_mixed(self):
        matrix = {"code_a": [1, 1, 0, 1, 0]}
        result = compute_code_stability(matrix)
        assert result["code_a"] == pytest.approx(0.6)

    def test_empty_matrix(self):
        result = compute_code_stability({})
        assert result == {}

    def test_multiple_codes(self):
        matrix = {
            "always": [1, 1, 1],
            "sometimes": [1, 0, 1],
            "rarely": [0, 0, 1],
        }
        result = compute_code_stability(matrix)
        assert result["always"] == pytest.approx(1.0)
        assert result["sometimes"] == pytest.approx(2 / 3)
        assert result["rarely"] == pytest.approx(1 / 3)


class TestClassifyStability:

    def test_classification_thresholds(self):
        scores = {
            "high": 0.9,       # stable
            "threshold": 0.8,  # stable (>= 0.8)
            "medium": 0.6,     # moderate
            "low": 0.3,        # unstable
            "zero": 0.0,       # unstable
        }
        stable, moderate, unstable = classify_stability(scores)
        assert "high" in stable
        assert "threshold" in stable
        assert "medium" in moderate
        assert "low" in unstable
        assert "zero" in unstable

    def test_empty_scores(self):
        stable, moderate, unstable = classify_stability({})
        assert stable == []
        assert moderate == []
        assert unstable == []

    def test_all_stable(self):
        scores = {"a": 1.0, "b": 0.9, "c": 0.8}
        stable, moderate, unstable = classify_stability(scores)
        assert len(stable) == 3
        assert moderate == []
        assert unstable == []

    def test_custom_thresholds(self):
        scores = {"a": 0.7, "b": 0.4}
        stable, moderate, unstable = classify_stability(
            scores, stable_threshold=0.6, moderate_threshold=0.3
        )
        assert "a" in stable
        assert "b" in moderate


# ---------------------------------------------------------------------------
# Domain model tests
# ---------------------------------------------------------------------------

class TestStabilityResult:

    def test_default_values(self):
        sr = StabilityResult(num_runs=5)
        assert sr.num_runs == 5
        assert sr.overall_stability == 0.0
        assert sr.stable_codes == []
        assert sr.moderate_codes == []
        assert sr.unstable_codes == []

    def test_round_trip_json(self):
        sr = StabilityResult(
            num_runs=5,
            code_stability={"code_a": 0.8, "code_b": 0.4},
            stable_codes=["code_a"],
            unstable_codes=["code_b"],
            overall_stability=0.6,
            model_name="gpt-5-mini",
        )
        json_str = sr.model_dump_json()
        restored = StabilityResult.model_validate_json(json_str)
        assert restored.num_runs == 5
        assert restored.code_stability == {"code_a": 0.8, "code_b": 0.4}

    def test_project_state_has_stability_result(self):
        state = ProjectState()
        assert state.stability_result is None
        state.stability_result = StabilityResult(num_runs=3)
        assert state.stability_result.num_runs == 3


# ---------------------------------------------------------------------------
# Orchestrator tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestRunStabilityAnalysis:

    def test_basic_stability_analysis(self):
        """Stability analysis should run N identical passes and compute scores."""
        state = _make_state()

        # Simulate 3 runs that produce slightly different codes
        responses = [
            _make_code_hierarchy(["AI Adoption", "Workflow Change", "Data Privacy"]),
            _make_code_hierarchy(["AI Adoption", "Workflow Change"]),
            _make_code_hierarchy(["AI Adoption", "Workflow Change", "Data Privacy"]),
        ]
        call_count = 0

        async def mock_extract(prompt, schema):
            nonlocal call_count
            resp = responses[call_count]
            call_count += 1
            return resp

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=mock_extract)
            result = asyncio.run(run_stability_analysis(state, num_runs=3))

        assert result.num_runs == 3
        assert result.model_name == "gpt-5-mini"

        # AI Adoption and Workflow Change appear in all 3 runs
        assert result.code_stability["ai adoption"] == pytest.approx(1.0)
        assert result.code_stability["workflow change"] == pytest.approx(1.0)
        # Data Privacy appears in 2/3 runs
        assert result.code_stability["data privacy"] == pytest.approx(2 / 3)

        # Classification
        assert "ai adoption" in result.stable_codes
        assert "workflow change" in result.stable_codes
        assert "data privacy" in result.moderate_codes
        assert len(result.unstable_codes) == 0

        # Overall stability
        assert result.overall_stability > 0.5

        # Run details
        assert len(result.run_details) == 3

    def test_identical_runs_give_perfect_stability(self):
        """If all runs produce the same codes, stability should be 1.0."""
        state = _make_state()
        response = _make_code_hierarchy(["Theme A", "Theme B"])

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=response)
            result = asyncio.run(run_stability_analysis(state, num_runs=3))

        assert result.overall_stability == pytest.approx(1.0)
        assert len(result.stable_codes) == 2
        assert len(result.moderate_codes) == 0
        assert len(result.unstable_codes) == 0

    def test_completely_different_runs(self):
        """If every run produces different codes, stability should be low."""
        state = _make_state()

        responses = [
            _make_code_hierarchy(["Alpha"]),
            _make_code_hierarchy(["Beta"]),
            _make_code_hierarchy(["Gamma"]),
        ]
        call_count = 0

        async def mock_extract(prompt, schema):
            nonlocal call_count
            resp = responses[call_count]
            call_count += 1
            return resp

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(side_effect=mock_extract)
            result = asyncio.run(run_stability_analysis(state, num_runs=3))

        # Each code appears in only 1/3 runs
        assert len(result.unstable_codes) == 3
        assert len(result.stable_codes) == 0
        assert result.overall_stability == pytest.approx(1 / 3)

    def test_gt_methodology_uses_gt_stage(self):
        """GT methodology should use GTOpenCodingStage, not ThematicCodingStage."""
        from qc_clean.core.pipeline.stages.gt_open_coding import OpenCodesResponse
        from qc_clean.schemas.gt_schemas import OpenCode

        state = _make_state(
            config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY)
        )

        mock_response = OpenCodesResponse(
            open_codes=[
                OpenCode(
                    code_name="GT Code",
                    description="A grounded theory code",
                    properties=["p"],
                    dimensions=["d"],
                    supporting_quotes=["quote"],
                    frequency=1,
                    confidence=0.7,
                ),
            ],
        )

        with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
            instance = MockLLM.return_value
            instance.extract_structured = AsyncMock(return_value=mock_response)
            result = asyncio.run(run_stability_analysis(state, num_runs=2))

        assert result.num_runs == 2
        assert "gt code" in result.code_stability


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

class TestStabilityExport:

    def test_markdown_includes_stability(self, tmp_path):
        state = _make_state()
        state.stability_result = StabilityResult(
            num_runs=5,
            code_stability={"ai adoption": 1.0, "rare theme": 0.2},
            stable_codes=["ai adoption"],
            moderate_codes=[],
            unstable_codes=["rare theme"],
            overall_stability=0.6,
            model_name="gpt-5-mini",
        )

        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()

        assert "## Multi-Run Stability Analysis" in content
        assert "Overall stability" in content
        assert "ai adoption" in content
        assert "Stable" in content

    def test_markdown_omits_stability_when_absent(self, tmp_path):
        state = _make_state()
        output_file = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(output_file))
        content = output_file.read_text()
        assert "Stability" not in content

    def test_csv_includes_stability(self, tmp_path):
        state = _make_state()
        state.stability_result = StabilityResult(
            num_runs=5,
            code_stability={"ai adoption": 1.0, "rare theme": 0.2},
            stable_codes=["ai adoption"],
            unstable_codes=["rare theme"],
            overall_stability=0.6,
            model_name="gpt-5-mini",
        )

        paths = ProjectExporter().export_csv(state, str(tmp_path))
        stability_paths = [p for p in paths if "stability.csv" in p]
        assert len(stability_paths) == 1

        with open(stability_paths[0], newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        ai_row = [r for r in rows if r["code_name"] == "ai adoption"][0]
        assert ai_row["classification"] == "stable"
        assert float(ai_row["stability_score"]) == 1.0

        rare_row = [r for r in rows if r["code_name"] == "rare theme"][0]
        assert rare_row["classification"] == "unstable"

    def test_csv_omits_stability_when_absent(self, tmp_path):
        state = _make_state()
        paths = ProjectExporter().export_csv(state, str(tmp_path))
        filenames = [p.split("/")[-1] for p in paths]
        assert "stability.csv" not in filenames
