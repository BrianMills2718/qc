"""Tests for the evaluation-harness Phase 0 scorecard."""

from qc_clean.core.bench import phase0_scorecard
from qc_clean.core.grounding import resolve_span
from qc_clean.schemas.domain import (
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    IRRResult,
    Methodology,
    ProjectConfig,
    ProjectState,
    Segment,
    StabilityResult,
)


def test_scorecard_grounding_rate_reflects_anchors():
    content = "Alex: autonomy matters more than oversight here."
    doc = Document(name="d.txt", content=content)
    m = resolve_span("autonomy matters", content)
    state = ProjectState(
        name="study",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[Code(id="C1", name="Autonomy", description="d")]),
        code_applications=[
            # anchored + verifiable
            CodeApplication(code_id="C1", doc_id=doc.id, quote_text="autonomy matters",
                            start_char=m.start_char, end_char=m.end_char, quote_hash=m.quote_hash),
            # unanchored (no hash)
            CodeApplication(code_id="C1", doc_id=doc.id, quote_text="oversight"),
        ],
    )
    card = phase0_scorecard(state)
    assert card["project"] == "study"
    assert card["code_applications"] == 2
    assert card["grounding"]["anchored_verified"] == 1
    assert card["grounding"]["anchored_no_hash"] == 1
    assert abs(card["grounding"]["grounding_rate"] - 0.5) < 1e-9
    assert "coverage" in card and "coverage_rate" in card["coverage"]
    assert card["_meta"]["phase"] == 0


def test_scorecard_includes_reliability_and_stability_when_present():
    state = ProjectState(
        name="s",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="x")]),
        irr_result=IRRResult(num_passes=2, percent_agreement=0.9,
                             cohens_kappa=0.7, interpretation="substantial"),
        stability_result=StabilityResult(num_runs=5, overall_stability=0.8,
                                          stable_codes=["a"], moderate_codes=[],
                                          unstable_codes=["b"]),
    )
    card = phase0_scorecard(state)
    assert card["reliability_llm_pass_agreement"]["cohens_kappa"] == 0.7
    assert "consistency not validity" in card["reliability_llm_pass_agreement"]["note"]
    assert card["stability"]["overall_stability"] == 0.8
    assert card["stability"]["unstable"] == 1


def test_coverage_note_is_conditional_on_exhaustive_mode():
    """F6: the scorecard's coverage_note must not claim 'traversal only' once
    every segment carries a coding decision (exhaustive mode), and must not claim
    examined-and-judged coverage when no segment was judged."""
    content = "Alex: autonomy matters here."
    doc = Document(name="d.txt", content=content)

    # Traversal mode: a segment exists but has no decision.
    traversal = ProjectState(
        name="t",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[doc]),
        segments=[Segment(id="S1", doc_id=doc.id, index=0, start_char=0,
                          end_char=len(content), text=content, decision=None)],
    )
    note_t = phase0_scorecard(traversal)["_meta"]["coverage_note"]
    assert "traversal coverage only" in note_t
    assert "examined-and-judged coverage available" not in note_t

    # Examined mode: the segment carries a decision.
    examined = traversal.model_copy(deep=True)
    examined.segments[0].decision = "no_code"
    note_e = phase0_scorecard(examined)["_meta"]["coverage_note"]
    assert "examined-and-judged coverage available" in note_e
    assert "traversal coverage only" not in note_e


def test_scorecard_grounding_rate_one_when_no_applications():
    state = ProjectState(
        name="empty",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[]),
    )
    assert phase0_scorecard(state)["grounding"]["grounding_rate"] == 1.0
