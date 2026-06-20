"""Application-level IRR: agreement on coding the SAME segment, not just the
same code list (built on the segment universe / exhaustive coding)."""

from qc_clean.core.pipeline.irr import (
    build_application_matrix,
    compute_cohens_kappa,
    compute_fleiss_kappa,
    compute_percent_agreement,
)


def test_application_matrix_segment_code_cells():
    # 2 passes. seg A: both DISTRUST (agree). seg B: pass0 ANXIETY, pass1 none (disagree).
    passes = [
        {"d#0": {"distrust"}, "d#10": {"anxiety"}},
        {"d#0": {"distrust"}, "d#10": set()},
    ]
    m = build_application_matrix(passes)
    assert m["d#0::distrust"] == [1, 1]
    assert m["d#10::anxiety"] == [1, 0]
    # percent agreement: 1 of 2 cells unanimous
    assert abs(compute_percent_agreement(m) - 0.5) < 1e-9


def test_application_matrix_perfect_agreement():
    passes = [
        {"d#0": {"trust"}, "d#5": {"trust", "power"}},
        {"d#0": {"trust"}, "d#5": {"trust", "power"}},
    ]
    m = build_application_matrix(passes)
    assert compute_percent_agreement(m) == 1.0
    assert compute_cohens_kappa(m) == 1.0  # 2 passes, total agreement


def test_application_matrix_three_passes_fleiss():
    passes = [
        {"d#0": {"a"}},
        {"d#0": {"a"}},
        {"d#0": {"a"}},
    ]
    m = build_application_matrix(passes)
    # single cell, all 3 present -> perfect
    assert compute_fleiss_kappa(m) == 1.0


def test_application_matrix_empty():
    assert build_application_matrix([{}, {}]) == {}


def test_run_irr_application_level_end_to_end():
    """run_irr_analysis(application_level=True) runs exhaustive passes and reports
    segment-level agreement alongside the codebook-discovery number."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from qc_clean.core.pipeline.irr import run_irr_analysis
    from qc_clean.core.segmentation import segment_corpus
    from qc_clean.schemas.analysis_schemas import (
        ExhaustiveCodingResponse, SegmentDecision, ThematicCode,
    )
    from qc_clean.schemas.domain import Corpus, Document, Methodology, ProjectConfig, ProjectState

    content = "Interviewer: How do you feel?\nDana: It honestly feels like distrust."
    doc = Document(id="d1", name="d.txt", content=content, detected_speakers=["Interviewer", "Dana"])
    state = ProjectState(name="t", config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
                         corpus=Corpus(documents=[doc]))
    state.segments = segment_corpus([doc])
    assert len(state.segments) == 2

    # Every pass returns the same decisions -> perfect application-level agreement.
    mock = ExhaustiveCodingResponse(
        codes=[ThematicCode(id="DISTRUST", name="Distrust", description="d",
                            semantic_definition="s", level=0, mention_count=1, discovery_confidence=0.8)],
        decisions=[SegmentDecision(segment_index=0, code_ids=[]),
                   SegmentDecision(segment_index=1, code_ids=["DISTRUST"])],
        total_codes=1, analysis_confidence=0.8,
    )
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(run_irr_analysis(state, num_passes=2, application_level=True))

    assert result.application_level is True
    assert result.application_units == 1            # one (segment, code) cell applied
    assert result.application_percent_agreement == 1.0
    assert result.application_cohens_kappa == 1.0
    assert result.application_interpretation == "almost perfect"
    # codebook-discovery metrics still present
    assert result.percent_agreement == 1.0
