"""Tests for the evaluation-harness Phase 0 scorecard."""

from qc_clean.core.bench import phase0_scorecard
from qc_clean.core.grounding import resolve_span
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
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


def test_scorecard_includes_category_saturation_diagnostic():
    doc = Document(name="d.txt", content="Trust varied by context.")
    state = ProjectState(
        name="gt",
        config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="TRUST",
                name="Trust",
                properties=["institutional"],
                dimensions=["low-high"],
            )
        ]),
        code_applications=[
            CodeApplication(
                code_id="TRUST",
                doc_id=doc.id,
                quote_text="Trust varied by context.",
            )
        ],
    )

    diagnostic = phase0_scorecard(state)["category_saturation"]

    assert diagnostic["status"] == "diagnostic"
    assert diagnostic["all_categories_adequate"] is True
    assert diagnostic["adequate_count"] == 1
    assert "diagnostic only" in diagnostic["note"]


def test_scorecard_reports_d7_unavailable_without_gold():
    state = ProjectState(
        name="no-gold",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="AI failed here.")]),
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]

    assert d7["status"] == "not_available"
    assert "gold" in d7["reason"]
    assert "recall" not in d7
    assert "precision" not in d7


def test_scorecard_computes_d7_perfect_match_against_gold():
    content = "AI improved delivery. AI failed for this team."
    doc = Document(id="d1", name="d.txt", content=content)
    start = content.index("AI failed")
    end = len(content)
    state = ProjectState(
        name="gold",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "disconfirmation_gold": [
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": doc.id,
                        "start_char": start,
                        "end_char": end,
                        "quote_text": content[start:end],
                    },
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(
                    doc_id=doc.id,
                    start_char=start,
                    end_char=end,
                    quote_text=content[start:end],
                ),
            ),
        ],
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]

    assert d7["status"] == "scored"
    assert d7["true_positives"] == 1
    assert d7["false_positives"] == 0
    assert d7["false_negatives"] == 0
    assert d7["recall"] == 1.0
    assert d7["precision"] == 1.0
    assert d7["f1"] == 1.0
    assert d7["matched_gold_keys"] == [f"claim-ai|{doc.id}|{start}:{end}"]
    assert d7["missed_gold_keys"] == []
    assert d7["extra_predicted_keys"] == []


def test_scorecard_computes_d7_false_positive_and_false_negative():
    content = "AI failed here. AI also failed later. AI only succeeded elsewhere."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI failed")
    first_end = first_start + len("AI failed here.")
    second_start = content.index("AI also")
    second_end = second_start + len("AI also failed later.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
        name="mixed",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "disconfirmation_gold": [
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": doc.id,
                        "start_char": first_start,
                        "end_char": first_end,
                    },
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": doc.id,
                        "start_char": second_start,
                        "end_char": second_end,
                    },
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(doc_id=doc.id, start_char=first_start, end_char=first_end),
            ),
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(doc_id=doc.id, start_char=extra_start, end_char=extra_end),
            ),
        ],
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]

    assert d7["status"] == "scored"
    assert d7["gold_count"] == 2
    assert d7["predicted_count"] == 2
    assert d7["true_positives"] == 1
    assert d7["false_positives"] == 1
    assert d7["false_negatives"] == 1
    assert d7["recall"] == 0.5
    assert d7["precision"] == 0.5
    assert d7["f1"] == 0.5
    assert d7["matched_gold_keys"] == [f"claim-ai|{doc.id}|{first_start}:{first_end}"]
    assert d7["missed_gold_keys"] == [f"claim-ai|{doc.id}|{second_start}:{second_end}"]
    assert d7["extra_predicted_keys"] == [f"claim-ai|{doc.id}|{extra_start}:{extra_end}"]


def _negative_case_claim(target_claim_id: str, anchor: ClaimAnchor) -> AnalyticClaim:
    return AnalyticClaim(
        claim_kind=ClaimKind.NEGATIVE_CASE,
        source_stage="negative_case_analysis",
        claim_text="Contrary evidence was found.",
        scope=ClaimScope(claim_ids=[target_claim_id]),
        origin_object_type="negative_case",
        origin_object_id=f"negative:{target_claim_id}:{anchor.start_char}",
        contrary_anchors=[anchor],
    )
