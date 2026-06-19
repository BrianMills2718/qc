"""INV-6 regression: disconfirmation must cover the final claim set.

Negative-case analysis runs last in every pipeline (verified in
test_pipeline_engine) and must challenge the cross-interview claims, not only the
codebook. These tests lock in the plumbing that surfaces the cross-interview
``cross_case`` memo to the disconfirmation prompt.
"""

from qc_clean.core.pipeline.stages.negative_case import _format_cross_interview_claims
from qc_clean.schemas.domain import (
    AnalysisMemo,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
)


def _state(**kwargs) -> ProjectState:
    defaults = dict(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d1.txt", content="content")]),
    )
    defaults.update(kwargs)
    return ProjectState(**defaults)


def test_no_cross_interview_memo_returns_empty():
    # Single-doc corpora never run cross-interview; disconfirmation should not
    # invent a section.
    state = _state()
    assert _format_cross_interview_claims(state) == ""


def test_returns_cross_case_memo_content():
    state = _state(memos=[
        AnalysisMemo(memo_type="coding", title="x", content="not this"),
        AnalysisMemo(
            memo_type="cross_case",
            title="Cross-Interview Pattern Analysis",
            content="Consensus: trust matters. Divergent: autonomy.",
        ),
    ])
    out = _format_cross_interview_claims(state)
    assert "Consensus: trust matters" in out
    assert "not this" not in out


def test_returns_latest_cross_case_memo():
    state = _state(memos=[
        AnalysisMemo(memo_type="cross_case", title="x", content="OLD"),
        AnalysisMemo(memo_type="cross_case", title="x", content="NEW"),
    ])
    assert _format_cross_interview_claims(state) == "NEW"
