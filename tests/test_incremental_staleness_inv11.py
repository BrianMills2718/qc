"""INV-11 regression: incremental recode must flag stale higher-order outputs.

`project recode` does not recompute perspective/entities/synthesis/GT outputs.
When the corpus changes, those become stale; the system must flag them rather
than silently retain them as if current. These tests cover the detector.
"""

from qc_clean.core.pipeline.stages.incremental_coding import (
    _stale_higher_order_outputs,
)
from qc_clean.schemas.domain import (
    Corpus,
    CoreCategoryResult,
    Document,
    Entity,
    Methodology,
    PerspectiveAnalysis,
    ProjectConfig,
    ProjectState,
    Synthesis,
)


def _state(**kwargs) -> ProjectState:
    defaults = dict(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d1.txt", content="content")]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def test_no_higher_order_outputs_returns_empty():
    assert _stale_higher_order_outputs(_state()) == []


def test_detects_populated_outputs():
    state = _state(
        synthesis=Synthesis(executive_summary="s"),
        perspective_analysis=PerspectiveAnalysis(),
        entities=[Entity(name="X")],
        core_categories=[CoreCategoryResult(category_name="C")],
    )
    stale = _stale_higher_order_outputs(state)
    assert "synthesis" in stale
    assert "perspective_analysis" in stale
    assert "entities" in stale
    assert "core_categories" in stale


def test_empty_collections_not_flagged():
    # An empty entities list is not a stale output.
    state = _state(entities=[], core_categories=[])
    assert _stale_higher_order_outputs(state) == []


def test_markdown_export_surfaces_data_warnings(tmp_path):
    """data_warnings must be rendered in the Markdown report, not silently
    dropped while stale synthesis/etc. are rendered (INV-11)."""
    from qc_clean.core.export.data_exporter import ProjectExporter

    state = _state(
        synthesis=Synthesis(executive_summary="stale summary"),
        data_warnings=["Incremental recode ... did not recompute: synthesis."],
    )
    out = tmp_path / "report.md"
    ProjectExporter().export_markdown(state, str(out))
    text = out.read_text()
    assert "Data warnings" in text
    assert "did not recompute: synthesis" in text
