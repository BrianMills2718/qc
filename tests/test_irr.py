"""
Tests for inter-rater reliability (IRR) module.

Covers pure metric functions, alignment logic, orchestration (mocked LLM),
and export integration.
"""

import asyncio
import csv
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from qc_clean.core.pipeline.irr import (
    PROMPT_SUFFIXES,
    align_codes,
    build_coding_matrix,
    compute_cohens_kappa,
    compute_fleiss_kappa,
    compute_percent_agreement,
    interpret_kappa,
    normalize_code_name,
    run_irr_analysis,
)
from qc_clean.schemas.domain import (
    Code,
    Codebook,
    Corpus,
    Document,
    IRRCodingPass,
    IRRResult,
    Methodology,
    ProjectConfig,
    ProjectState,
)


# ---------------------------------------------------------------------------
# normalize_code_name
# ---------------------------------------------------------------------------

class TestNormalizeCodeName:
    def test_lowercase(self):
        assert normalize_code_name("Work Life Balance") == "work life balance"

    def test_strip_punctuation(self):
        assert normalize_code_name("self-care (emotional)") == "selfcare emotional"

    def test_collapse_whitespace(self):
        assert normalize_code_name("  multiple   spaces  ") == "multiple spaces"

    def test_empty(self):
        assert normalize_code_name("") == ""

    def test_underscores_preserved(self):
        assert normalize_code_name("WORK_LIFE") == "work_life"


# ---------------------------------------------------------------------------
# align_codes
# ---------------------------------------------------------------------------

class TestAlignCodes:
    def test_full_overlap(self):
        passes = [["Theme A", "Theme B"], ["Theme A", "Theme B"]]
        aligned, unmatched = align_codes(passes)
        assert aligned == ["theme a", "theme b"]
        assert unmatched == []

    def test_no_overlap(self):
        passes = [["Theme A"], ["Theme B"]]
        aligned, unmatched = align_codes(passes)
        assert aligned == []
        assert sorted(unmatched) == ["theme a", "theme b"]

    def test_partial_overlap(self):
        passes = [["Theme A", "Theme B", "Theme C"], ["Theme A", "Theme C", "Theme D"]]
        aligned, unmatched = align_codes(passes)
        assert aligned == ["theme a", "theme c"]
        assert sorted(unmatched) == ["theme b", "theme d"]

    def test_case_insensitive(self):
        passes = [["Work Life Balance"], ["work life balance"]]
        aligned, unmatched = align_codes(passes)
        assert aligned == ["work life balance"]
        assert unmatched == []

    def test_three_passes(self):
        passes = [
            ["A", "B", "C"],
            ["A", "C", "D"],
            ["A", "D", "E"],
        ]
        aligned, unmatched = align_codes(passes)
        assert "a" in aligned
        assert "c" in aligned  # in passes 0 and 1
        assert "d" in aligned  # in passes 1 and 2
        assert "b" in unmatched  # only in pass 0
        assert "e" in unmatched  # only in pass 2

    def test_empty_passes(self):
        aligned, unmatched = align_codes([[], []])
        assert aligned == []
        assert unmatched == []

    def test_duplicate_within_pass(self):
        """A code appearing twice in the same pass should only count once."""
        passes = [["Theme A", "Theme A"], ["Theme B"]]
        aligned, unmatched = align_codes(passes)
        assert aligned == []
        assert sorted(unmatched) == ["theme a", "theme b"]


# ---------------------------------------------------------------------------
# build_coding_matrix
# ---------------------------------------------------------------------------

class TestBuildCodingMatrix:
    def test_basic(self):
        passes = [["A", "B"], ["A", "C"]]
        aligned = ["a", "b", "c"]
        matrix = build_coding_matrix(passes, aligned)
        assert matrix["a"] == [1, 1]
        assert matrix["b"] == [1, 0]
        assert matrix["c"] == [0, 1]

    def test_empty(self):
        matrix = build_coding_matrix([[], []], [])
        assert matrix == {}


# ---------------------------------------------------------------------------
# compute_percent_agreement
# ---------------------------------------------------------------------------

class TestPercentAgreement:
    def test_perfect_agreement(self):
        matrix = {"a": [1, 1], "b": [1, 1], "c": [0, 0]}
        assert compute_percent_agreement(matrix) == 1.0

    def test_no_agreement(self):
        matrix = {"a": [1, 0], "b": [0, 1]}
        assert compute_percent_agreement(matrix) == 0.0

    def test_partial_agreement(self):
        matrix = {"a": [1, 1], "b": [1, 0], "c": [0, 0], "d": [0, 1]}
        assert compute_percent_agreement(matrix) == 0.5

    def test_empty(self):
        assert compute_percent_agreement({}) == 0.0


# ---------------------------------------------------------------------------
# compute_cohens_kappa
# ---------------------------------------------------------------------------

class TestCohensKappa:
    def test_perfect_agreement(self):
        matrix = {"a": [1, 1], "b": [1, 1], "c": [0, 0]}
        assert compute_cohens_kappa(matrix) == 1.0

    def test_complete_disagreement(self):
        """Complete disagreement gives kappa = -1."""
        matrix = {"a": [1, 0], "b": [0, 1], "c": [1, 0], "d": [0, 1]}
        kappa = compute_cohens_kappa(matrix)
        assert abs(kappa - (-1.0)) < 0.01

    def test_known_value(self):
        """Test with a hand-calculated example.

        2 raters, 10 items:
        Both present: 4, R1 only: 1, R2 only: 2, Both absent: 3
        Po = (4+3)/10 = 0.7
        Pe = (5/10)*(6/10) + (5/10)*(4/10) = 0.30 + 0.20 = 0.50
        kappa = (0.7 - 0.5) / (1 - 0.5) = 0.4
        """
        matrix = {
            "i1": [1, 1], "i2": [1, 1], "i3": [1, 1], "i4": [1, 1],
            "i5": [1, 0], "i6": [0, 1], "i7": [0, 1],
            "i8": [0, 0], "i9": [0, 0], "i10": [0, 0],
        }
        kappa = compute_cohens_kappa(matrix)
        assert abs(kappa - 0.4) < 0.01

    def test_requires_two_passes(self):
        matrix = {"a": [1, 1, 0]}
        with pytest.raises(ValueError, match="exactly 2 passes"):
            compute_cohens_kappa(matrix)

    def test_empty(self):
        assert compute_cohens_kappa({}) == 0.0


# ---------------------------------------------------------------------------
# compute_fleiss_kappa
# ---------------------------------------------------------------------------

class TestFleissKappa:
    def test_perfect_agreement(self):
        matrix = {"a": [1, 1, 1], "b": [0, 0, 0]}
        assert compute_fleiss_kappa(matrix) == 1.0

    def test_known_value_three_raters(self):
        """3 raters, 4 items. Hand-calculated:

        items: [1,1,1], [1,1,0], [0,0,1], [0,0,0]
        k=3, n=4, categories={0,1}

        P_i for each item:
        [1,1,1]: n1=3,n0=0 -> (3*2+0)/6 = 1.0
        [1,1,0]: n1=2,n0=1 -> (2*1+1*0)/6 = 2/6 = 0.333
        [0,0,1]: n1=1,n0=2 -> (1*0+2*1)/6 = 2/6 = 0.333
        [0,0,0]: n1=0,n0=3 -> (0+3*2)/6 = 1.0

        P_bar = (1+0.333+0.333+1)/4 = 0.6667

        total_present = 3+2+1+0 = 6, total = 12
        p1 = 6/12 = 0.5, p0 = 0.5
        Pe = 0.25 + 0.25 = 0.5

        kappa = (0.6667-0.5)/(1-0.5) = 0.3333
        """
        matrix = {
            "i1": [1, 1, 1],
            "i2": [1, 1, 0],
            "i3": [0, 0, 1],
            "i4": [0, 0, 0],
        }
        kappa = compute_fleiss_kappa(matrix)
        assert abs(kappa - 0.3333) < 0.01

    def test_matches_cohens_for_two_raters(self):
        """Fleiss' kappa should equal Cohen's kappa for 2 raters."""
        matrix = {
            "i1": [1, 1], "i2": [1, 1], "i3": [1, 1], "i4": [1, 1],
            "i5": [1, 0], "i6": [0, 1], "i7": [0, 1],
            "i8": [0, 0], "i9": [0, 0], "i10": [0, 0],
        }
        ck = compute_cohens_kappa(matrix)
        fk = compute_fleiss_kappa(matrix)
        assert abs(ck - fk) < 0.01

    def test_empty(self):
        assert compute_fleiss_kappa({}) == 0.0


# ---------------------------------------------------------------------------
# interpret_kappa
# ---------------------------------------------------------------------------

class TestInterpretKappa:
    def test_poor(self):
        assert interpret_kappa(-0.1) == "poor"

    def test_slight(self):
        assert interpret_kappa(0.1) == "slight"

    def test_fair(self):
        assert interpret_kappa(0.3) == "fair"

    def test_moderate(self):
        assert interpret_kappa(0.5) == "moderate"

    def test_substantial(self):
        assert interpret_kappa(0.7) == "substantial"

    def test_almost_perfect(self):
        assert interpret_kappa(0.9) == "almost perfect"


# ---------------------------------------------------------------------------
# Orchestration tests (mocked LLM)
# ---------------------------------------------------------------------------

def _make_project(methodology="default"):
    meth = Methodology.GROUNDED_THEORY if methodology == "grounded_theory" else Methodology.DEFAULT
    return ProjectState(
        name="Test Project",
        config=ProjectConfig(methodology=meth),
        corpus=Corpus(documents=[
            Document(name="interview1.txt", content="This is test interview content about work life balance.")
        ]),
    )


def _mock_thematic_execute(codes_per_call):
    """Return an async side_effect that populates state with given codes."""
    call_count = [0]

    async def side_effect(self_stage, state, config):
        idx = call_count[0]
        call_count[0] += 1
        names = codes_per_call[idx % len(codes_per_call)]
        state.codebook = Codebook(codes=[
            Code(name=name, description=f"Description of {name}")
            for name in names
        ])
        return state

    return side_effect


class TestOrchestration:
    def test_correct_pass_count(self):
        state = _make_project()
        codes = [["Theme A", "Theme B"]] * 3

        with patch(
            "qc_clean.core.pipeline.stages.thematic_coding.ThematicCodingStage.execute",
            new=_mock_thematic_execute(codes),
        ):
            result = asyncio.run(run_irr_analysis(state, num_passes=3))

        assert result.num_passes == 3
        assert len(result.passes) == 3

    def test_different_suffixes_per_pass(self):
        state = _make_project()
        codes = [["Theme A"]] * 3

        with patch(
            "qc_clean.core.pipeline.stages.thematic_coding.ThematicCodingStage.execute",
            new=_mock_thematic_execute(codes),
        ):
            result = asyncio.run(run_irr_analysis(state, num_passes=3))

        suffixes = [p.prompt_suffix for p in result.passes]
        assert suffixes[0] == PROMPT_SUFFIXES[0]
        assert suffixes[1] == PROMPT_SUFFIXES[1]
        assert suffixes[2] == PROMPT_SUFFIXES[2]

    def test_multi_model_rotation(self):
        state = _make_project()
        codes = [["Theme A"]] * 4

        with patch(
            "qc_clean.core.pipeline.stages.thematic_coding.ThematicCodingStage.execute",
            new=_mock_thematic_execute(codes),
        ):
            result = asyncio.run(run_irr_analysis(
                state, num_passes=4, models=["gpt-5-mini", "claude-sonnet-4-5-20250929"]
            ))

        models_used = [p.model_name for p in result.passes]
        assert models_used == ["gpt-5-mini", "claude-sonnet-4-5-20250929", "gpt-5-mini", "claude-sonnet-4-5-20250929"]

    def test_result_saved_to_state(self):
        state = _make_project()
        codes = [["Theme A", "Theme B"]] * 2

        with patch(
            "qc_clean.core.pipeline.stages.thematic_coding.ThematicCodingStage.execute",
            new=_mock_thematic_execute(codes),
        ):
            result = asyncio.run(run_irr_analysis(state, num_passes=2))

        # Verify the result can be assigned to state
        state.irr_result = result
        assert state.irr_result is not None
        assert state.irr_result.num_passes == 2

    def test_gt_methodology_routing(self):
        """Grounded theory projects should use GTOpenCodingStage."""
        state = _make_project(methodology="grounded_theory")
        codes = [["Concept A"]] * 2

        with patch(
            "qc_clean.core.pipeline.stages.gt_open_coding.GTOpenCodingStage.execute",
            new=_mock_thematic_execute(codes),
        ):
            result = asyncio.run(run_irr_analysis(state, num_passes=2))

        assert result.num_passes == 2
        assert len(result.passes) == 2


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------

class TestExportIntegration:
    def _make_state_with_irr(self):
        state = _make_project()
        state.codebook = Codebook(codes=[
            Code(name="Theme A", description="desc"),
        ])
        state.irr_result = IRRResult(
            num_passes=2,
            passes=[
                IRRCodingPass(pass_index=0, prompt_suffix="", model_name="gpt-5-mini",
                              codes_discovered=["Theme A", "Theme B"]),
                IRRCodingPass(pass_index=1, prompt_suffix="Focus on nuance", model_name="gpt-5-mini",
                              codes_discovered=["Theme A", "Theme C"]),
            ],
            aligned_codes=["theme a"],
            unmatched_codes=["theme b", "theme c"],
            coding_matrix={
                "theme a": [1, 1],
                "theme b": [1, 0],
                "theme c": [0, 1],
            },
            percent_agreement=0.333,
            cohens_kappa=0.0,
            fleiss_kappa=0.0,
            interpretation="slight",
        )
        return state

    def test_markdown_includes_irr(self, tmp_path):
        from qc_clean.core.export.data_exporter import ProjectExporter

        state = self._make_state_with_irr()
        out = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(out))

        content = out.read_text()
        assert "## Inter-Rater Reliability" in content
        assert "Percent agreement" in content
        assert "Cohen's kappa" in content
        assert "Coding Matrix" in content

    def test_markdown_omits_irr_when_absent(self, tmp_path):
        from qc_clean.core.export.data_exporter import ProjectExporter

        state = _make_project()
        out = tmp_path / "report.md"
        ProjectExporter().export_markdown(state, str(out))

        content = out.read_text()
        assert "Inter-Rater Reliability" not in content

    def test_csv_writes_irr_matrix(self, tmp_path):
        from qc_clean.core.export.data_exporter import ProjectExporter

        state = self._make_state_with_irr()
        paths = ProjectExporter().export_csv(state, str(tmp_path))

        irr_paths = [p for p in paths if Path(p).name == "irr_matrix.csv"]
        assert len(irr_paths) == 1

        with open(irr_paths[0], newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Header + 3 data rows
        assert len(rows) == 4
        assert rows[0] == ["code_name", "pass_1", "pass_2", "agreement"]

    def test_csv_no_irr_matrix_when_absent(self, tmp_path):
        from qc_clean.core.export.data_exporter import ProjectExporter

        state = _make_project()
        paths = ProjectExporter().export_csv(state, str(tmp_path))

        irr_paths = [p for p in paths if Path(p).name == "irr_matrix.csv"]
        assert len(irr_paths) == 0


# ---------------------------------------------------------------------------
# Domain model tests
# ---------------------------------------------------------------------------

class TestDomainModel:
    def test_irr_result_on_project_state(self):
        state = ProjectState(name="Test")
        assert state.irr_result is None

        state.irr_result = IRRResult(num_passes=3)
        assert state.irr_result.num_passes == 3

    def test_irr_result_serialization(self):
        state = ProjectState(name="Test")
        state.irr_result = IRRResult(
            num_passes=2,
            aligned_codes=["code a"],
            coding_matrix={"code a": [1, 1]},
            percent_agreement=1.0,
            cohens_kappa=1.0,
            interpretation="almost perfect",
        )
        # Round-trip through JSON
        json_str = state.model_dump_json()
        restored = ProjectState.model_validate_json(json_str)
        assert restored.irr_result is not None
        assert restored.irr_result.cohens_kappa == 1.0
        assert restored.irr_result.coding_matrix == {"code a": [1, 1]}
