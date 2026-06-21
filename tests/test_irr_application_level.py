"""Application-level IRR: agreement on coding the SAME segment, not just the
same code list (built on the segment universe / exhaustive coding)."""

from qc_clean.core.pipeline.irr import (
    build_application_matrix,
    build_segment_decision_matrix,
    compute_categorical_cohens_kappa,
    compute_categorical_fleiss_kappa,
    compute_categorical_percent_agreement,
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


def test_segment_decision_matrix_counts_no_code_agreement():
    passes = [
        {"d#0": "no_code", "d#10": "coded"},
        {"d#0": "no_code", "d#10": "coded"},
    ]
    m = build_segment_decision_matrix(passes)
    assert m["d#0"] == ["no_code", "no_code"]
    assert m["d#10"] == ["coded", "coded"]
    assert compute_categorical_percent_agreement(m) == 1.0
    assert compute_categorical_cohens_kappa(m) == 1.0


def test_segment_decision_matrix_disagreement_and_missing_decision():
    passes = [
        {"d#0": "no_code", "d#10": "coded", "d#20": "coded"},
        {"d#0": "coded", "d#10": "coded"},  # d#20 missing -> not_examined
    ]
    m = build_segment_decision_matrix(passes)
    assert m["d#0"] == ["no_code", "coded"]
    assert m["d#10"] == ["coded", "coded"]
    assert m["d#20"] == ["coded", "not_examined"]
    assert abs(compute_categorical_percent_agreement(m) - (1 / 3)) < 1e-9


def test_segment_decision_matrix_three_passes_fleiss():
    passes = [
        {"d#0": "no_code", "d#10": "coded"},
        {"d#0": "no_code", "d#10": "coded"},
        {"d#0": "no_code", "d#10": "coded"},
    ]
    m = build_segment_decision_matrix(passes)
    assert compute_categorical_fleiss_kappa(m) == 1.0


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
    assert result.segment_decision_units == 2
    first_seg_key = f"{state.segments[0].doc_id}#{state.segments[0].start_char}"
    assert result.segment_decision_matrix[first_seg_key] == ["no_code", "no_code"]
    assert result.segment_decision_percent_agreement == 1.0
    assert result.segment_decision_cohens_kappa == 1.0
    assert result.segment_decision_interpretation == "almost perfect"
    # codebook-discovery metrics still present
    assert result.percent_agreement == 1.0


def test_run_irr_application_level_all_no_code_reports_segment_agreement():
    """All-no-code passes have no positive cells, but segment decisions still agree."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from qc_clean.core.pipeline.irr import run_irr_analysis
    from qc_clean.core.segmentation import segment_corpus
    from qc_clean.schemas.analysis_schemas import ExhaustiveCodingResponse, SegmentDecision
    from qc_clean.schemas.domain import Corpus, Document, Methodology, ProjectConfig, ProjectState

    content = "Interviewer: Anything else?\nDana: No."
    doc = Document(id="d1", name="d.txt", content=content, detected_speakers=["Interviewer", "Dana"])
    state = ProjectState(name="t", config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
                         corpus=Corpus(documents=[doc]))
    state.segments = segment_corpus([doc])

    mock = ExhaustiveCodingResponse(
        codes=[],
        decisions=[SegmentDecision(segment_index=0, code_ids=[]),
                   SegmentDecision(segment_index=1, code_ids=[])],
        total_codes=0, analysis_confidence=0.8,
    )
    with patch("qc_clean.core.llm.llm_handler.LLMHandler") as MockLLM:
        MockLLM.return_value.extract_structured = AsyncMock(return_value=mock)
        result = asyncio.run(run_irr_analysis(state, num_passes=2, application_level=True))

    assert result.application_units == 0
    assert result.application_percent_agreement is None
    assert result.application_cohens_kappa is None
    assert result.application_interpretation == "no positive code applications compared"
    assert result.segment_decision_units == 2
    assert result.segment_decision_percent_agreement == 1.0
    assert result.segment_decision_cohens_kappa == 1.0
    assert result.segment_decision_interpretation == "almost perfect"
