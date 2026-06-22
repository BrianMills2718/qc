"""Tests for the evaluation-harness Phase 0 scorecard."""

import sqlite3

import pytest

from qc_clean.core.bench import d10_cost_latency_scorecard, d10_wall_clock_scorecard, phase0_scorecard
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
    assert card["grounding"]["grounding_rate_ci"]["successes"] == 1
    assert card["grounding"]["grounding_rate_ci"]["denominator"] == 2
    assert "coverage" in card and "coverage_rate" in card["coverage"]
    assert card["_meta"]["phase"] == 0


def test_scorecard_includes_reliability_and_stability_when_present():
    state = ProjectState(
        name="s",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="x")]),
        irr_result=IRRResult(num_passes=2, percent_agreement=0.9,
                             cohens_kappa=0.7, gwet_ac1=0.8, interpretation="substantial"),
        stability_result=StabilityResult(num_runs=5, overall_stability=0.8,
                                          stable_codes=["a"], moderate_codes=[],
                                          unstable_codes=["b"]),
    )
    card = phase0_scorecard(state)
    assert card["reliability_llm_pass_agreement"]["cohens_kappa"] == 0.7
    assert card["reliability_llm_pass_agreement"]["gwet_ac1"] == 0.8
    assert card["reliability_llm_pass_agreement"]["application_level"] is False
    assert card["reliability_llm_pass_agreement"]["prevalence"]["row_count"] == 0
    assert card["reliability_llm_pass_agreement"]["prevalence"]["rating_count"] == 0
    assert card["reliability_llm_pass_agreement"]["bootstrap_ci"]["status"] == "not_available"
    assert card["reliability_llm_pass_agreement"]["bootstrap_ci"]["population_size"] == 0
    assert "consistency not validity" in card["reliability_llm_pass_agreement"]["note"]
    assert card["stability"]["overall_stability"] == 0.8
    assert card["stability"]["unstable"] == 1


def test_scorecard_surfaces_application_level_reliability_metrics():
    state = ProjectState(
        name="s",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="x")]),
        irr_result=IRRResult(
            num_passes=2,
            percent_agreement=0.75,
            cohens_kappa=0.4,
            fleiss_kappa=0.4,
            gwet_ac1=0.6,
            interpretation="fair",
            coding_matrix={"code-a": [1, 1], "code-b": [1, 0]},
            application_level=True,
            application_units=3,
            application_percent_agreement=2 / 3,
            application_cohens_kappa=0.25,
            application_fleiss_kappa=0.25,
            application_gwet_ac1=0.5,
            application_interpretation="fair",
            application_matrix={
                "d#0::a": [1, 1],
                "d#1::b": [1, 0],
                "d#2::c": [0, 1],
            },
            segment_decision_units=4,
            segment_decision_percent_agreement=0.75,
            segment_decision_cohens_kappa=0.5,
            segment_decision_fleiss_kappa=0.5,
            segment_decision_gwet_ac1=0.65,
            segment_decision_interpretation="moderate",
            segment_decision_matrix={
                "d#0": ["coded", "coded"],
                "d#1": ["no_code", "coded"],
                "d#2": ["not_examined", "coded"],
                "d#3": ["no_code", "no_code"],
            },
        ),
    )

    reliability = phase0_scorecard(state)["reliability_llm_pass_agreement"]

    assert reliability["gwet_ac1"] == 0.6
    assert reliability["application_level"] is True
    assert reliability["prevalence"]["categories"]["present"]["count"] == 3
    assert reliability["prevalence"]["categories"]["present"]["rate"] == 0.75
    assert reliability["bootstrap_ci"]["status"] == "scored"
    assert reliability["bootstrap_ci"]["method"] == "row_bootstrap"
    assert reliability["bootstrap_ci"]["samples"] == 1000
    assert reliability["bootstrap_ci"]["population_size"] == 2
    assert set(reliability["bootstrap_ci"]["metrics"]) == {"percent_agreement", "gwet_ac1"}
    assert reliability["prevalence"]["row_patterns"] == {
        "all_absent": 0,
        "all_present": 1,
        "mixed": 1,
    }

    positive = reliability["application_positive_segment_code"]
    assert positive["units"] == 3
    assert positive["percent_agreement"] == 2 / 3
    assert positive["cohens_kappa"] == 0.25
    assert positive["fleiss_kappa"] == 0.25
    assert positive["gwet_ac1"] == 0.5
    assert positive["interpretation"] == "fair"
    assert positive["prevalence"]["row_count"] == 3
    assert positive["prevalence"]["rating_count"] == 6
    assert positive["prevalence"]["ratings_per_row"] == 2
    assert positive["prevalence"]["categories"]["present"]["count"] == 4
    assert positive["prevalence"]["categories"]["absent"]["rate"] == pytest.approx(1 / 3)
    assert positive["bootstrap_ci"]["status"] == "scored"
    assert positive["bootstrap_ci"]["population_size"] == 3
    assert positive["bootstrap_ci"]["metrics"]["percent_agreement"]["lower"] <= (
        positive["bootstrap_ci"]["metrics"]["percent_agreement"]["upper"]
    )

    segment = reliability["segment_decision"]
    assert segment["units"] == 4
    assert segment["percent_agreement"] == 0.75
    assert segment["cohens_kappa"] == 0.5
    assert segment["fleiss_kappa"] == 0.5
    assert segment["gwet_ac1"] == 0.65
    assert segment["interpretation"] == "moderate"
    assert segment["prevalence"]["row_count"] == 4
    assert segment["prevalence"]["rating_count"] == 8
    assert segment["prevalence"]["categories"]["coded"] == {"count": 4, "rate": 0.5}
    assert segment["prevalence"]["categories"]["no_code"] == {"count": 3, "rate": 0.375}
    assert segment["prevalence"]["categories"]["not_examined"] == {"count": 1, "rate": 0.125}
    assert segment["bootstrap_ci"]["status"] == "scored"
    assert segment["bootstrap_ci"]["unit"] == "categorical reliability matrix row"
    assert set(segment["bootstrap_ci"]["metrics"]) == {"percent_agreement", "gwet_ac1"}


def test_scorecard_reliability_bootstrap_can_be_disabled():
    state = ProjectState(
        name="s",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={"phase0_reliability_bootstrap": {"enabled": False}},
        ),
        corpus=Corpus(documents=[Document(name="d.txt", content="x")]),
        irr_result=IRRResult(
            num_passes=2,
            percent_agreement=1.0,
            gwet_ac1=1.0,
            coding_matrix={"code-a": [1, 1]},
            application_level=True,
            application_units=1,
            application_percent_agreement=1.0,
            application_gwet_ac1=1.0,
            application_matrix={"d#0::a": [1, 1]},
            segment_decision_units=1,
            segment_decision_percent_agreement=1.0,
            segment_decision_gwet_ac1=1.0,
            segment_decision_matrix={"d#0": ["coded", "coded"]},
        ),
    )

    reliability = phase0_scorecard(state)["reliability_llm_pass_agreement"]

    assert "bootstrap_ci" not in reliability
    assert "bootstrap_ci" not in reliability["application_positive_segment_code"]
    assert "bootstrap_ci" not in reliability["segment_decision"]


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
    traversal_card = phase0_scorecard(traversal)
    note_t = traversal_card["_meta"]["coverage_note"]
    assert traversal_card["coverage"]["coverage_rate_ci"]["successes"] == 0
    assert traversal_card["coverage"]["coverage_rate_ci"]["denominator"] == 1
    assert traversal_card["coverage"]["examined_rate_ci"]["successes"] == 0
    assert traversal_card["coverage"]["examined_rate_ci"]["denominator"] == 1
    assert traversal_card["coverage"]["coded_segment_rate"] is None
    assert traversal_card["coverage"]["coded_segment_rate_ci"]["successes"] == 0
    assert traversal_card["coverage"]["coded_segment_rate_ci"]["denominator"] == 0
    assert "traversal coverage only" in note_t
    assert "examined-and-judged coverage available" not in note_t

    # Examined mode: the segment carries a decision.
    examined = traversal.model_copy(deep=True)
    examined.segments[0].decision = "no_code"
    examined_card = phase0_scorecard(examined)
    note_e = examined_card["_meta"]["coverage_note"]
    assert examined_card["coverage"]["examined_rate_ci"]["successes"] == 1
    assert examined_card["coverage"]["examined_rate_ci"]["denominator"] == 1
    assert examined_card["coverage"]["coded_segment_rate"] == 0.0
    assert examined_card["coverage"]["coded_segment_rate_ci"]["successes"] == 0
    assert examined_card["coverage"]["coded_segment_rate_ci"]["denominator"] == 1
    assert "examined-and-judged coverage available" in note_e
    assert "traversal coverage only" not in note_e


def test_coverage_scorecard_reports_mixed_coded_segment_rate():
    content = "Alex: one.\nSam: two.\nRiley: three."
    doc = Document(name="d.txt", content=content)
    state = ProjectState(
        name="mixed",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[doc]),
        segments=[
            Segment(id="S1", doc_id=doc.id, index=0, start_char=0, end_char=9,
                    text="Alex: one", decision="coded"),
            Segment(id="S2", doc_id=doc.id, index=1, start_char=10, end_char=18,
                    text="Sam: two", decision="no_code"),
            Segment(id="S3", doc_id=doc.id, index=2, start_char=19, end_char=len(content),
                    text="Riley: three.", decision="coded"),
        ],
    )

    coverage = phase0_scorecard(state)["coverage"]

    assert coverage["coded_segments"] == 2
    assert coverage["examined_segments"] == 3
    assert coverage["coded_segment_rate"] == pytest.approx(2 / 3)
    assert coverage["coded_segment_rate_ci"]["method"] == "wilson"
    assert coverage["coded_segment_rate_ci"]["successes"] == 2
    assert coverage["coded_segment_rate_ci"]["denominator"] == 3
    assert coverage["coded_segment_rate_ci"]["lower"] <= coverage["coded_segment_rate"]
    assert coverage["coded_segment_rate_ci"]["upper"] >= coverage["coded_segment_rate"]


def test_scorecard_grounding_rate_one_when_no_applications():
    state = ProjectState(
        name="empty",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[]),
    )
    grounding = phase0_scorecard(state)["grounding"]
    assert grounding["grounding_rate"] == 1.0
    assert grounding["grounding_rate_ci"]["denominator"] == 0
    assert grounding["grounding_rate_ci"]["lower"] is None


def test_scorecard_reports_d3_not_available_without_application_gold():
    state = ProjectState(name="no d3 gold")

    d3 = phase0_scorecard(state)["application_validity_d3"]

    assert d3["status"] == "not_available"
    assert "application gold" in d3["reason"]
    assert "not evidence" in d3["note"]


def test_scorecard_scores_d3_application_gold_exact_span_and_code():
    content = "AI helped here. AI failed later. AI only appeared."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI helped")
    first_end = first_start + len("AI helped here.")
    second_start = content.index("AI failed")
    second_end = second_start + len("AI failed later.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": first_start,
                        "end_char": first_end,
                    },
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": second_start,
                        "end_char": second_end,
                    },
                ]
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[first_start:first_end],
                start_char=first_start,
                end_char=first_end,
            ),
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[extra_start:extra_end],
                start_char=extra_start,
                end_char=extra_end,
            ),
            CodeApplication(
                id="unanchored-app",
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text="AI somewhere",
            ),
        ],
    )

    d3 = phase0_scorecard(state)["application_validity_d3"]

    assert d3["status"] == "scored"
    assert d3["gold_count"] == 2
    assert d3["predicted_count"] == 3
    assert d3["true_positives"] == 1
    assert d3["false_positives"] == 2
    assert d3["false_negatives"] == 1
    assert d3["recall"] == 0.5
    assert d3["precision"] == pytest.approx(1 / 3)
    assert d3["f1"] == pytest.approx(0.4)
    assert d3["matched_gold_keys"] == [f"AI_USE|{doc.id}|{first_start}:{first_end}"]
    assert d3["missed_gold_keys"] == [f"AI_USE|{doc.id}|{second_start}:{second_end}"]
    assert d3["extra_predicted_keys"] == [f"AI_USE|{doc.id}|{extra_start}:{extra_end}"]
    assert d3["unscored_predicted_anchors"] == [
        "unanchored-app|code=AI_USE|doc=d1|missing-span-or-segment"
    ]
    assert d3["recall_ci"]["method"] == "wilson"
    assert d3["precision_ci"]["method"] == "wilson"
    assert d3["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert d3["f1_bootstrap_ci"]["metric"] == "f1"
    assert d3["f1_bootstrap_ci"]["confidence_level"] == 0.95
    assert d3["f1_bootstrap_ci"]["samples"] == 1000
    assert d3["f1_bootstrap_ci"]["seed"] == 0
    assert d3["f1_bootstrap_ci"]["population_size"] == 4
    assert d3["f1_bootstrap_ci"]["lower"] <= d3["f1_bootstrap_ci"]["upper"]
    agreement = d3["system_gold_agreement"]
    assert agreement["status"] == "scored"
    assert agreement["unit"] == "exact code/source-anchor key"
    assert agreement["raters"] == ["gold", "system"]
    assert agreement["row_count"] == 3
    assert agreement["gold_positive_count"] == 2
    assert agreement["system_positive_count"] == 2
    assert agreement["percent_agreement"] == pytest.approx(1 / 3)
    assert agreement["cohens_kappa"] == pytest.approx(-0.5)
    assert agreement["gwet_ac1"] == pytest.approx(-0.2)
    assert agreement["krippendorff_alpha"] == pytest.approx(-0.25)
    assert agreement["prevalence"]["row_count"] == 3
    assert agreement["prevalence"]["rating_count"] == 6
    assert agreement["prevalence"]["categories"]["present"]["count"] == 4
    assert agreement["prevalence"]["categories"]["present"]["rate"] == pytest.approx(2 / 3)
    assert agreement["prevalence"]["row_patterns"] == {
        "all_absent": 0,
        "all_present": 1,
        "mixed": 2,
    }
    assert "not semantic equivalence" in agreement["note"]
    assert d3["human_ceiling_comparison"]["status"] == "not_available"
    assert "versioned gold-set package" in d3["human_ceiling_comparison"]["reason"]
    overlap = d3["span_overlap"]
    assert overlap["status"] == "scored"
    assert overlap["metric"] == "char_span_iou_same_code_doc"
    assert overlap["gold_span_count"] == 2
    assert overlap["predicted_span_count"] == 2
    assert overlap["unscored_gold_count"] == 0
    assert overlap["unscored_predicted_count"] == 1
    assert overlap["mean_best_gold_iou"] == pytest.approx(0.5)
    assert overlap["mean_best_predicted_iou"] == pytest.approx(0.5)
    assert overlap["gold_best_overlaps"][0]["best_modified_hausdorff_distance"] == 0.0
    assert overlap["mean_best_gold_modified_hausdorff_distance"] is not None
    assert overlap["mean_best_predicted_modified_hausdorff_distance"] is not None


def test_scorecard_scores_d3_baselines_against_same_gold():
    content = "AI helped here. AI failed later. AI only appeared."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI helped")
    first_end = first_start + len("AI helped here.")
    second_start = content.index("AI failed")
    second_end = second_start + len("AI failed later.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": first_start,
                        "end_char": first_end,
                    },
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": second_start,
                        "end_char": second_end,
                    },
                ],
                "application_baselines": [
                    {
                        "name": "single_prompt",
                        "description": "Generic one-shot baseline.",
                        "code_applications": [
                            {
                                "code_id": "AI_USE",
                                "doc_id": doc.id,
                                "start_char": second_start,
                                "end_char": second_end,
                            },
                            {
                                "code_id": "AI_USE",
                                "doc_id": doc.id,
                                "start_char": extra_start,
                                "end_char": extra_end,
                            },
                        ],
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[first_start:first_end],
                start_char=first_start,
                end_char=first_end,
            )
        ],
    )

    d3 = phase0_scorecard(state)["application_validity_d3"]

    baseline = d3["baselines"]["single_prompt"]
    assert d3["recall"] == 0.5
    assert d3["precision"] == 1.0
    assert d3["f1"] == pytest.approx(2 / 3)
    assert baseline["description"] == "Generic one-shot baseline."
    assert baseline["true_positives"] == 1
    assert baseline["false_positives"] == 1
    assert baseline["false_negatives"] == 1
    assert baseline["recall"] == 0.5
    assert baseline["precision"] == 0.5
    assert baseline["f1"] == 0.5
    assert baseline["recall_ci"]["method"] == "wilson"
    assert baseline["precision_ci"]["method"] == "wilson"
    assert d3["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert baseline["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert baseline["f1_bootstrap_ci"]["samples"] == d3["f1_bootstrap_ci"]["samples"]
    delta_ci = baseline["system_minus_baseline_ci"]
    assert delta_ci["method"] == "paired_key_universe_bootstrap"
    assert delta_ci["samples"] == d3["f1_bootstrap_ci"]["samples"]
    assert delta_ci["seed"] == d3["f1_bootstrap_ci"]["seed"]
    assert set(delta_ci["deltas"]) == {"recall", "precision", "f1"}
    for interval in delta_ci["deltas"].values():
        assert interval["lower"] <= interval["upper"]
    assert baseline["matched_gold_keys"] == [f"AI_USE|{doc.id}|{second_start}:{second_end}"]
    assert baseline["missed_gold_keys"] == [f"AI_USE|{doc.id}|{first_start}:{first_end}"]
    assert baseline["extra_predicted_keys"] == [f"AI_USE|{doc.id}|{extra_start}:{extra_end}"]
    assert baseline["system_minus_baseline"]["recall"] == 0.0
    assert baseline["system_minus_baseline"]["precision"] == 0.5
    assert baseline["system_minus_baseline"]["f1"] == pytest.approx(1 / 6)
    assert "local paired exact-key bootstrap intervals" in d3["baseline_note"]


def test_scorecard_d3_baseline_bootstrap_disable_suppresses_delta_ci():
    content = "AI helped here. AI failed later."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI helped")
    first_end = first_start + len("AI helped here.")
    second_start = content.index("AI failed")
    second_end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_exact_bootstrap": {"enabled": False},
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": first_start,
                        "end_char": first_end,
                    },
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": second_start,
                        "end_char": second_end,
                    },
                ],
                "application_baselines": [
                    {
                        "name": "single_prompt",
                        "code_applications": [
                            {
                                "code_id": "AI_USE",
                                "doc_id": doc.id,
                                "start_char": second_start,
                                "end_char": second_end,
                            }
                        ],
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[first_start:first_end],
                start_char=first_start,
                end_char=first_end,
            )
        ],
    )

    d3 = phase0_scorecard(state)["application_validity_d3"]
    baseline = d3["baselines"]["single_prompt"]

    assert "f1_bootstrap_ci" not in d3
    assert "f1_bootstrap_ci" not in baseline
    assert "system_minus_baseline_ci" not in baseline


def test_scorecard_invalid_d3_baseline_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "application_gold": [
                    {"code_id": "AI_USE", "doc_id": "d1", "segment_id": "s1"},
                ],
                "application_baselines": [
                    {"name": "duplicate", "code_applications": []},
                    {"name": "duplicate", "code_applications": []},
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="Duplicate D3 baseline"):
        phase0_scorecard(state)


def test_scorecard_d3_compares_exact_metrics_to_human_ceiling_package():
    content = "AI helped here."
    doc = Document(id="d1", name="d.txt", content=content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": _versioned_d3_package(
                    [
                        {
                            "code_id": "AI_USE",
                            "doc_id": doc.id,
                            "start_char": 0,
                            "end_char": len(content),
                        }
                    ],
                    {
                        "recall": 0.9,
                        "precision": 0.8,
                        "f1": 0.85,
                        "cohens_kappa": 0.72,
                        "gwet_ac1": 0.81,
                    },
                )
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content,
                start_char=0,
                end_char=len(content),
            )
        ],
    )

    comparison = phase0_scorecard(state)["application_validity_d3"]["human_ceiling_comparison"]
    agreement = phase0_scorecard(state)["application_validity_d3"]["system_gold_agreement"]

    assert comparison["status"] == "scored"
    assert comparison["gold_split"] == "held_out"
    assert comparison["prompt_frozen"] is True
    assert comparison["contamination_checked"] is True
    assert comparison["system_meets_all_comparable_metrics"] is True
    assert comparison["metrics"]["recall"] == {
        "system_value": 1.0,
        "human_value": 0.9,
        "system_minus_human": pytest.approx(0.1),
        "meets_or_exceeds_human": True,
    }
    assert comparison["metrics"]["precision"]["system_minus_human"] == pytest.approx(0.2)
    assert comparison["metrics"]["f1"]["system_minus_human"] == pytest.approx(0.15)
    assert comparison["chance_corrected_agreement"]["status"] == "reported"
    assert comparison["chance_corrected_agreement"]["metrics"] == {
        "cohens_kappa": 0.72,
        "gwet_ac1": 0.81,
    }
    assert agreement["percent_agreement"] == 1.0
    assert agreement["cohens_kappa"] == 1.0
    assert agreement["gwet_ac1"] == 1.0
    assert agreement["krippendorff_alpha"] == 1.0
    assert agreement["prevalence"]["row_patterns"]["all_present"] == 1
    assert comparison["non_comparable_human_metrics"] == []
    assert "not expert-parity evidence" in comparison["note"]


def test_scorecard_human_ceiling_noncomparable_metrics_are_not_scored():
    content = "AI helped here."
    doc = Document(id="d1", name="d.txt", content=content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": _versioned_d3_package(
                    [
                        {
                            "code_id": "AI_USE",
                            "doc_id": doc.id,
                            "start_char": 0,
                            "end_char": len(content),
                        }
                    ],
                    {
                        "cohens_kappa": 0.72,
                        "fleiss_kappa": "not-recorded",
                        "krippendorffs_alpha": 0.68,
                        "notes": "No exact-score ceiling.",
                    },
                )
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content,
                start_char=0,
                end_char=len(content),
            )
        ],
    )

    comparison = phase0_scorecard(state)["application_validity_d3"]["human_ceiling_comparison"]

    assert comparison["status"] == "metadata_only"
    assert "no numeric recall, precision, or f1" in comparison["reason"]
    assert comparison["human_metrics"] == {
        "cohens_kappa": 0.72,
        "fleiss_kappa": "not-recorded",
        "krippendorffs_alpha": 0.68,
        "notes": "No exact-score ceiling.",
    }
    assert comparison["chance_corrected_agreement"]["status"] == "reported"
    assert comparison["chance_corrected_agreement"]["metrics"] == {
        "cohens_kappa": 0.72,
        "krippendorff_alpha": 0.68,
    }
    assert comparison["chance_corrected_agreement"]["non_numeric_metrics"] == [
        "fleiss_kappa"
    ]
    assert "does not compare system chance-corrected agreement" in (
        comparison["chance_corrected_agreement"]["note"]
    )
    assert comparison["non_comparable_human_metrics"] == ["notes"]


def test_scorecard_reports_codebook_quality_unavailable_without_eval_data():
    state = ProjectState(
        name="no-quality-eval",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    d4 = phase0_scorecard(state)["codebook_quality_d4"]

    assert d4["status"] == "not_available"
    assert "codebook_quality_evaluations" in d4["reason"]
    assert "not evidence" in d4["note"]


def test_scorecard_scores_codebook_quality_rubric_outcomes():
    state = ProjectState(
        name="quality-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "codebook_quality_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "evaluator_type": "llm_judge",
                        "clarity": 0.8,
                        "specificity": 0.7,
                        "usefulness": 0.9,
                        "grounding": 1.0,
                    },
                    {
                        "evaluator": "expert-1",
                        "evaluator_type": "human_expert",
                        "scope": "individual_code",
                        "code_id": "C1",
                        "clarity": 0.6,
                        "specificity": 0.9,
                        "usefulness": 0.7,
                        "grounding": 0.8,
                    },
                ],
            },
        ),
    )

    d4 = phase0_scorecard(state)["codebook_quality_d4"]

    assert d4["status"] == "scored"
    assert d4["total_evaluations"] == 2
    assert d4["evaluator_types"] == {"human_expert": 1, "llm_judge": 1}
    assert d4["overall_mean"] == pytest.approx(0.8)
    assert d4["overall_mean_ci"]["method"] == "rubric_mean_bootstrap"
    assert d4["overall_mean_ci"]["population_size"] == 2
    assert d4["overall_mean_ci"]["samples"] == 1000
    assert d4["metric_summary"]["clarity"]["mean"] == pytest.approx(0.7)
    assert d4["metric_summary"]["clarity"]["min"] == 0.6
    assert d4["metric_summary"]["clarity"]["max"] == 0.8
    assert d4["metric_summary"]["clarity"]["mean_ci"]["population_size"] == 2
    assert d4["metric_summary"]["specificity"]["mean"] == pytest.approx(0.8)
    assert d4["by_evaluator_type"]["llm_judge"]["overall_mean"] == pytest.approx(0.85)
    assert d4["by_evaluator_type"]["llm_judge"]["overall_mean_ci"][
        "population_size"
    ] == 1
    assert d4["by_evaluator_type"]["llm_judge"]["metric_summary"]["clarity"][
        "mean_ci"
    ]["population_size"] == 1
    assert d4["by_evaluator_type"]["human_expert"]["overall_mean"] == pytest.approx(0.75)
    assert "not blind expert-panel evidence" in d4["note"]


def test_scorecard_codebook_quality_bootstrap_can_be_disabled():
    state = ProjectState(
        name="quality-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_rubric_bootstrap": {"enabled": False},
                "codebook_quality_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "evaluator_type": "llm_judge",
                        "clarity": 0.8,
                        "specificity": 0.7,
                        "usefulness": 0.9,
                        "grounding": 1.0,
                    },
                ],
            },
        ),
    )

    d4 = phase0_scorecard(state)["codebook_quality_d4"]

    assert d4["status"] == "scored"
    assert "overall_mean_ci" not in d4
    assert "mean_ci" not in d4["metric_summary"]["clarity"]
    assert "overall_mean_ci" not in d4["by_evaluator_type"]["llm_judge"]


def test_scorecard_invalid_codebook_quality_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "codebook_quality_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "clarity": 1.2,
                        "specificity": 0.7,
                        "usefulness": 0.9,
                        "grounding": 1.0,
                    }
                ]
            }
        ),
    )

    with pytest.raises(ValueError, match="codebook_quality_evaluations"):
        phase0_scorecard(state)


def test_scorecard_reports_gt_fidelity_unavailable_without_eval_data():
    state = ProjectState(
        name="no-gt-fidelity-eval",
        config=ProjectConfig(methodology=Methodology.GROUNDED_THEORY),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    d8 = phase0_scorecard(state)["gt_fidelity_d8"]

    assert d8["status"] == "not_available"
    assert "gt_fidelity_evaluations" in d8["reason"]
    assert "not evidence" in d8["note"]


def test_scorecard_scores_gt_fidelity_rubric_outcomes():
    state = ProjectState(
        name="gt-fidelity-eval",
        config=ProjectConfig(
            methodology=Methodology.GROUNDED_THEORY,
            extra={
                "gt_fidelity_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "evaluator_type": "llm_judge",
                        "constant_comparison": 0.8,
                        "category_development": 0.7,
                        "memo_quality": 0.9,
                        "saturation_justification": 0.6,
                    },
                    {
                        "evaluator": "expert-1",
                        "evaluator_type": "human_expert",
                        "scope": "category",
                        "artifact_id": "C1",
                        "constant_comparison": 0.6,
                        "category_development": 0.8,
                        "memo_quality": 0.7,
                        "saturation_justification": 0.5,
                    },
                ],
            },
        ),
    )

    d8 = phase0_scorecard(state)["gt_fidelity_d8"]

    assert d8["status"] == "scored"
    assert d8["total_evaluations"] == 2
    assert d8["evaluator_types"] == {"human_expert": 1, "llm_judge": 1}
    assert d8["scopes"] == {"category": 1, "grounded_theory_pipeline": 1}
    assert d8["overall_mean"] == pytest.approx(0.7)
    assert d8["overall_mean_ci"]["method"] == "rubric_mean_bootstrap"
    assert d8["overall_mean_ci"]["population_size"] == 2
    assert d8["metric_summary"]["constant_comparison"]["mean"] == pytest.approx(0.7)
    assert d8["metric_summary"]["constant_comparison"]["min"] == 0.6
    assert d8["metric_summary"]["constant_comparison"]["max"] == 0.8
    assert d8["metric_summary"]["constant_comparison"]["mean_ci"][
        "population_size"
    ] == 2
    assert d8["metric_summary"]["category_development"]["mean"] == pytest.approx(0.75)
    assert d8["by_evaluator_type"]["llm_judge"]["overall_mean"] == pytest.approx(0.75)
    assert d8["by_evaluator_type"]["llm_judge"]["overall_mean_ci"][
        "population_size"
    ] == 1
    assert d8["by_evaluator_type"]["human_expert"]["overall_mean"] == pytest.approx(0.65)
    assert d8["by_scope"]["category"]["overall_mean"] == pytest.approx(0.65)
    assert d8["by_scope"]["category"]["overall_mean_ci"]["population_size"] == 1
    assert d8["by_scope"]["category"]["metric_summary"]["memo_quality"]["mean_ci"][
        "population_size"
    ] == 1
    assert "not expert-rubric acceptance" in d8["note"]


def test_scorecard_gt_fidelity_bootstrap_can_be_disabled():
    state = ProjectState(
        name="gt-fidelity-eval",
        config=ProjectConfig(
            methodology=Methodology.GROUNDED_THEORY,
            extra={
                "phase0_rubric_bootstrap": {"enabled": False},
                "gt_fidelity_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "evaluator_type": "llm_judge",
                        "constant_comparison": 0.8,
                        "category_development": 0.7,
                        "memo_quality": 0.9,
                        "saturation_justification": 0.6,
                    },
                ],
            },
        ),
    )

    d8 = phase0_scorecard(state)["gt_fidelity_d8"]

    assert d8["status"] == "scored"
    assert "overall_mean_ci" not in d8
    assert "mean_ci" not in d8["metric_summary"]["constant_comparison"]
    assert "overall_mean_ci" not in d8["by_evaluator_type"]["llm_judge"]
    assert "overall_mean_ci" not in d8["by_scope"]["grounded_theory_pipeline"]


def test_scorecard_invalid_gt_fidelity_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "gt_fidelity_evaluations": [
                    {
                        "evaluator": "judge-a",
                        "constant_comparison": 1.2,
                        "category_development": 0.7,
                        "memo_quality": 0.9,
                        "saturation_justification": 0.6,
                    }
                ]
            }
        ),
    )

    with pytest.raises(ValueError, match="gt_fidelity_evaluations"):
        phase0_scorecard(state)


def test_scorecard_reports_interpretive_preference_unavailable_without_eval_data():
    state = ProjectState(
        name="no-preference-eval",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    d9 = phase0_scorecard(state)["interpretive_preference_d9"]

    assert d9["status"] == "not_available"
    assert "interpretive_preference_evaluations" in d9["reason"]
    assert "not evidence" in d9["note"]


def test_scorecard_scores_interpretive_preference_outcomes():
    state = ProjectState(
        name="preference-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "interpretive_preference_evaluations": [
                    {
                        "case_id": "latent-1",
                        "evaluator": "expert-a",
                        "preferred": "system",
                    },
                    {
                        "case_id": "latent-2",
                        "evaluator": "expert-a",
                        "preferred": "human",
                    },
                    {
                        "case_id": "latent-3",
                        "evaluator": "expert-b",
                        "preferred": "tie",
                        "criterion": "latent_meaning",
                    },
                    {
                        "case_id": "latent-4",
                        "evaluator": "expert-b",
                        "preferred": "system",
                        "criterion": "latent_meaning",
                    },
                ],
            },
        ),
    )

    d9 = phase0_scorecard(state)["interpretive_preference_d9"]

    assert d9["status"] == "scored"
    assert d9["total_cases"] == 4
    assert d9["system_wins"] == 2
    assert d9["human_wins"] == 1
    assert d9["ties"] == 1
    assert d9["non_tie_cases"] == 3
    assert d9["tie_rate"] == pytest.approx(0.25)
    assert d9["tie_rate_ci"]["method"] == "wilson"
    assert d9["tie_rate_ci"]["successes"] == 1
    assert d9["tie_rate_ci"]["denominator"] == 4
    assert d9["system_preference_rate"] == pytest.approx(2 / 3)
    assert d9["system_preference_ci"]["method"] == "wilson"
    assert d9["system_preference_ci"]["successes"] == 2
    assert d9["system_preference_ci"]["denominator"] == 3
    assert d9["non_inferiority_assessment"]["status"] == "not_available"
    assert "protocol metadata" in d9["non_inferiority_assessment"]["reason"]
    assert d9["by_evaluator"]["expert-a"]["system_preference_rate"] == pytest.approx(0.5)
    assert d9["by_evaluator"]["expert-a"]["tie_rate_ci"]["successes"] == 0
    assert d9["by_evaluator"]["expert-a"]["tie_rate_ci"]["denominator"] == 2
    assert d9["by_evaluator"]["expert-b"]["tie_rate"] == pytest.approx(0.5)
    assert d9["by_evaluator"]["expert-b"]["tie_rate_ci"]["successes"] == 1
    assert d9["by_evaluator"]["expert-b"]["tie_rate_ci"]["denominator"] == 2
    assert d9["by_criterion"]["latent_meaning"]["non_tie_cases"] == 1
    assert d9["by_criterion"]["latent_meaning"]["tie_rate_ci"]["successes"] == 1
    assert d9["by_criterion"]["latent_meaning"]["tie_rate_ci"]["denominator"] == 2
    assert "not blind expert-parity evidence" in d9["note"]


def test_scorecard_d9_non_inferiority_requires_pre_registration():
    state = ProjectState(
        name="preference-margin",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "interpretive_preference_evaluations": {
                    "interpretive_preference_evaluations": [
                        {"case_id": f"system-{idx}", "preferred": "system"}
                        for idx in range(5)
                    ] + [{"case_id": "human-1", "preferred": "human"}],
                    "protocol": {
                        "protocol_id": "d9-margin-v1",
                        "non_inferiority_margin": 0.2,
                        "registered_before_evaluation": False,
                    },
                }
            },
        ),
    )

    assessment = phase0_scorecard(state)["interpretive_preference_d9"][
        "non_inferiority_assessment"
    ]

    assert assessment["status"] == "not_registered"
    assert assessment["meets_non_inferiority"] is False
    assert assessment["protocol"]["protocol_id"] == "d9-margin-v1"
    assert assessment["system_minus_human"] == pytest.approx(2 / 3)
    assert assessment["required_lower_bound"] == pytest.approx(-0.2)
    assert "not registered" in assessment["reason"]


def test_scorecard_d9_registered_non_inferiority_margin_passes_and_fails():
    passing = ProjectState(
        name="preference-margin-pass",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "interpretive_preference_evaluations": {
                    "interpretive_preference_evaluations": [
                        {"case_id": f"system-{idx}", "preferred": "system"}
                        for idx in range(5)
                    ] + [{"case_id": "human-1", "preferred": "human"}],
                    "protocol": {
                        "protocol_id": "d9-margin-v1",
                        "non_inferiority_margin": 0.2,
                        "registered_before_evaluation": True,
                    },
                }
            },
        ),
    )
    failing = ProjectState(
        name="preference-margin-fail",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "interpretive_preference_evaluations": {
                    "interpretive_preference_evaluations": [
                        {"case_id": f"system-{idx}", "preferred": "system"}
                        for idx in range(2)
                    ] + [
                        {"case_id": f"human-{idx}", "preferred": "human"}
                        for idx in range(4)
                    ],
                    "protocol": {
                        "protocol_id": "d9-margin-v1",
                        "non_inferiority_margin": 0.2,
                        "registered_before_evaluation": True,
                    },
                }
            },
        ),
    )

    passing_assessment = phase0_scorecard(passing)["interpretive_preference_d9"][
        "non_inferiority_assessment"
    ]
    failing_assessment = phase0_scorecard(failing)["interpretive_preference_d9"][
        "non_inferiority_assessment"
    ]

    assert passing_assessment["status"] == "scored"
    assert passing_assessment["meets_non_inferiority"] is True
    assert passing_assessment["system_minus_human_ci"]["lower"] > -0.2
    assert failing_assessment["status"] == "scored"
    assert failing_assessment["meets_non_inferiority"] is False
    assert failing_assessment["system_minus_human_ci"]["lower"] < -0.2


def test_scorecard_invalid_interpretive_preference_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "interpretive_preference_evaluations": [
                    {
                        "case_id": "latent-1",
                        "evaluator": "expert-a",
                        "preferred": "machine",
                    }
                ]
            }
        ),
    )

    with pytest.raises(ValueError, match="interpretive_preference_evaluations"):
        phase0_scorecard(state)


def test_scorecard_reports_confidence_calibration_unavailable_without_eval_data():
    state = ProjectState(
        name="no-calibration-eval",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    calibration = phase0_scorecard(state)["confidence_calibration"]

    assert calibration["status"] == "not_available"
    assert "confidence_calibration_evaluations" in calibration["reason"]
    assert "not evidence" in calibration["note"]


def test_scorecard_scores_confidence_calibration_outcomes():
    state = ProjectState(
        name="calibration-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "confidence_calibration_evaluations": [
                    {
                        "item_id": "theme-correct",
                        "surface": "thematic_coding",
                        "confidence": 0.9,
                        "correct": True,
                    },
                    {
                        "item_id": "theme-wrong",
                        "surface": "thematic_coding",
                        "confidence": 0.8,
                        "correct": False,
                    },
                    {
                        "item_id": "negative-correct-rejection",
                        "surface": "negative_case",
                        "confidence": 0.2,
                        "correct": False,
                    },
                    {
                        "item_id": "negative-correct",
                        "surface": "negative_case",
                        "confidence": 0.4,
                        "correct": True,
                    },
                ],
            },
        ),
    )

    calibration = phase0_scorecard(state)["confidence_calibration"]

    assert calibration["status"] == "scored"
    assert calibration["total_records"] == 4
    assert calibration["correct_records"] == 2
    assert calibration["incorrect_records"] == 2
    assert calibration["accuracy"] == pytest.approx(0.5)
    assert calibration["accuracy_ci"]["method"] == "wilson"
    assert calibration["accuracy_ci"]["successes"] == 2
    assert calibration["accuracy_ci"]["denominator"] == 4
    assert calibration["mean_confidence"] == pytest.approx(0.575)
    assert calibration["brier_score"] == pytest.approx(0.2625)
    assert calibration["brier_score_ci"]["method"] == "calibration_record_bootstrap"
    assert calibration["brier_score_ci"]["metric"] == "brier_score"
    assert calibration["brier_score_ci"]["population_size"] == 4
    assert calibration["expected_calibration_error"] == pytest.approx(0.425)
    assert calibration["expected_calibration_error_ci"]["metric"] == (
        "expected_calibration_error"
    )
    assert calibration["expected_calibration_error_ci"]["population_size"] == 4
    assert calibration["bin_count"] == 10
    bins = calibration["calibration_bins"]
    assert len(bins) == 10
    assert bins[0]["count"] == 0
    assert bins[0]["accuracy_ci"]["lower"] is None
    assert bins[0]["accuracy_ci"]["upper"] is None
    assert bins[2]["count"] == 1
    assert bins[2]["accuracy"] == 0.0
    assert bins[2]["accuracy_ci"]["successes"] == 0
    assert bins[2]["accuracy_ci"]["denominator"] == 1
    assert bins[2]["mean_confidence"] == pytest.approx(0.2)
    assert bins[2]["calibration_gap"] == pytest.approx(0.2)
    assert bins[9]["upper_inclusive"] is True
    assert bins[9]["count"] == 1
    assert bins[9]["accuracy"] == 1.0
    assert bins[9]["mean_confidence"] == pytest.approx(0.9)
    thematic = calibration["by_surface"]["thematic_coding"]
    assert thematic["total_records"] == 2
    assert thematic["accuracy"] == pytest.approx(0.5)
    assert thematic["accuracy_ci"]["successes"] == 1
    assert thematic["accuracy_ci"]["denominator"] == 2
    assert thematic["mean_confidence"] == pytest.approx(0.85)
    assert thematic["brier_score"] == pytest.approx(0.325)
    assert thematic["brier_score_ci"]["population_size"] == 2
    assert thematic["expected_calibration_error"] == pytest.approx(0.45)
    assert thematic["expected_calibration_error_ci"]["population_size"] == 2
    assert "not evidence that system confidence is calibrated" in calibration["note"]


def test_scorecard_confidence_calibration_bootstrap_can_be_disabled():
    state = ProjectState(
        name="calibration-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_calibration_bootstrap": {"enabled": False},
                "confidence_calibration_evaluations": [
                    {
                        "item_id": "theme-correct",
                        "surface": "thematic_coding",
                        "confidence": 0.9,
                        "correct": True,
                    },
                    {
                        "item_id": "theme-wrong",
                        "surface": "thematic_coding",
                        "confidence": 0.8,
                        "correct": False,
                    },
                ],
            },
        ),
    )

    calibration = phase0_scorecard(state)["confidence_calibration"]

    assert calibration["status"] == "scored"
    assert "brier_score_ci" not in calibration
    assert "expected_calibration_error_ci" not in calibration
    assert "brier_score_ci" not in calibration["by_surface"]["thematic_coding"]


def test_scorecard_invalid_confidence_calibration_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "confidence_calibration_evaluations": [
                    {
                        "item_id": "theme-correct",
                        "surface": "thematic_coding",
                        "confidence": 1.2,
                        "correct": True,
                    }
                ]
            }
        ),
    )

    with pytest.raises(ValueError, match="confidence_calibration_evaluations"):
        phase0_scorecard(state)


def test_scorecard_d3_f1_bootstrap_configurable_and_disableable():
    content = "AI helped here."
    doc = Document(id="d1", name="d.txt", content=content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_exact_bootstrap": {
                    "samples": 25,
                    "confidence_level": 0.8,
                    "seed": 7,
                },
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": 0,
                        "end_char": len(content),
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content,
                start_char=0,
                end_char=len(content),
            )
        ],
    )

    d3 = phase0_scorecard(state)["application_validity_d3"]

    assert d3["f1_bootstrap_ci"]["samples"] == 25
    assert d3["f1_bootstrap_ci"]["confidence_level"] == 0.8
    assert d3["f1_bootstrap_ci"]["seed"] == 7

    disabled = state.model_copy(deep=True)
    disabled.config.extra = dict(disabled.config.extra)
    disabled.config.extra["phase0_exact_bootstrap"] = {"enabled": False}

    disabled_d3 = phase0_scorecard(disabled)["application_validity_d3"]

    assert "f1_bootstrap_ci" not in disabled_d3


def test_scorecard_d3_span_overlap_scores_near_boundary_match():
    content = "0123456789abcdefghij0123456789"
    doc = Document(id="d1", name="d.txt", content=content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": 10,
                        "end_char": 20,
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[15:25],
                start_char=15,
                end_char=25,
            )
        ],
    )

    d3 = phase0_scorecard(state)["application_validity_d3"]

    assert d3["true_positives"] == 0
    assert d3["false_positives"] == 1
    assert d3["false_negatives"] == 1
    overlap = d3["span_overlap"]
    assert overlap["status"] == "scored"
    assert overlap["mean_best_gold_iou"] == pytest.approx(5 / 15)
    assert overlap["mean_best_predicted_iou"] == pytest.approx(5 / 15)
    assert overlap["mean_best_gold_modified_hausdorff_distance"] == pytest.approx(1.5)
    assert overlap["mean_best_predicted_modified_hausdorff_distance"] == pytest.approx(1.5)
    assert overlap["gold_best_overlaps"] == [
        {
            "gold_key": "AI_USE|d1|10:20",
            "best_predicted_key": "AI_USE|d1|15:25",
            "best_iou": pytest.approx(5 / 15),
            "best_modified_hausdorff_distance": pytest.approx(1.5),
        }
    ]


def test_scorecard_d3_span_overlap_counts_unscored_records():
    content = "AI helped here."
    doc = Document(id="d1", name="d.txt", content=content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "application_gold": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc.id,
                        "start_char": 0,
                        "end_char": len(content),
                    },
                    {"code_id": "AI_USE", "doc_id": doc.id, "segment_id": "seg-1"},
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content,
                start_char=0,
                end_char=len(content),
            ),
            CodeApplication(
                id="unanchored-app",
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text="AI somewhere",
            ),
        ],
    )

    overlap = phase0_scorecard(state)["application_validity_d3"]["span_overlap"]

    assert overlap["status"] == "scored"
    assert overlap["gold_span_count"] == 1
    assert overlap["predicted_span_count"] == 1
    assert overlap["unscored_gold_count"] == 1
    assert overlap["unscored_predicted_count"] == 1
    assert overlap["mean_best_gold_iou"] == 1.0
    assert overlap["mean_best_gold_modified_hausdorff_distance"] == 0.0


def test_scorecard_invalid_d3_gold_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "application_gold": [
                    {"code_id": "AI_USE", "doc_id": "d1", "segment_id": "s1"},
                    {"code_id": "AI_USE", "doc_id": "d1", "segment_id": "s1"},
                ]
            }
        )
    )

    with pytest.raises(ValueError, match="Duplicate D3 application gold"):
        phase0_scorecard(state)


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


def test_scorecard_reports_prompt_injection_unavailable_without_eval_data():
    state = ProjectState(
        name="no-injection-eval",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    inv7 = phase0_scorecard(state)["prompt_injection_inv7"]

    assert inv7["status"] == "not_available"
    assert "prompt_injection_evaluations" in inv7["reason"]
    assert "not evidence" in inv7["note"]


def test_scorecard_reports_bias_counterfactual_unavailable_without_eval_data():
    state = ProjectState(
        name="no-bias-eval",
        config=ProjectConfig(methodology=Methodology.THEMATIC_ANALYSIS),
        corpus=Corpus(documents=[Document(name="d.txt", content="Participant text.")]),
    )

    d6 = phase0_scorecard(state)["bias_counterfactual_d6"]

    assert d6["status"] == "not_available"
    assert "bias_counterfactual_evaluations" in d6["reason"]
    assert "not evidence" in d6["note"]


def test_d10_cost_latency_unavailable_when_db_missing(tmp_path):
    state = ProjectState(id="project-cost", name="Cost")

    d10 = d10_cost_latency_scorecard(state, tmp_path / "missing.db")

    assert d10["status"] == "not_available"
    assert "not found" in d10["reason"]
    assert "estimate" in d10["note"]


def test_d10_cost_latency_scores_matching_project_trace_rows(tmp_path):
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    state = ProjectState(
        id="project-cost",
        name="Cost",
        corpus=Corpus(documents=[
            Document(name="a.txt", content="A"),
            Document(name="b.txt", content="B"),
        ]),
    )
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.thematic_coding",
        trace_id=f"qualitative_coding/project/{state.id}",
        model="gpt-5-mini",
        cost=0.10,
        marginal_cost=0.08,
        latency_s=1.5,
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
    )
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.negative_case_analysis",
        trace_id=f"qualitative_coding/project/{state.id}/recode/2",
        model="gpt-5-mini",
        cost=0.20,
        marginal_cost=0.16,
        latency_s=2.5,
        prompt_tokens=200,
        completion_tokens=60,
        total_tokens=260,
    )
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.other",
        trace_id="qualitative_coding/project/other",
        model="gpt-5-mini",
        cost=9.99,
        marginal_cost=9.99,
        latency_s=9.0,
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
    )

    d10 = d10_cost_latency_scorecard(state, db_path)

    assert d10["status"] == "scored"
    assert d10["trace_match"]["mode"] == "prefix"
    assert d10["call_count"] == 2
    assert d10["errored_calls"] == 0
    assert d10["total_cost_usd"] == pytest.approx(0.30)
    assert d10["total_marginal_cost_usd"] == pytest.approx(0.24)
    assert d10["total_tokens"] == 400
    assert d10["prompt_tokens"] == 300
    assert d10["completion_tokens"] == 100
    assert d10["summed_latency_s"] == pytest.approx(4.0)
    assert d10["mean_latency_s"] == pytest.approx(2.0)
    assert d10["max_latency_s"] == pytest.approx(2.5)
    assert d10["cost_per_document_usd"] == pytest.approx(0.15)
    assert d10["latency_per_document_s"] == pytest.approx(2.0)
    assert d10["models"] == {"gpt-5-mini": 2}
    assert d10["tasks"] == {
        "qualitative_coding.negative_case_analysis": 1,
        "qualitative_coding.thematic_coding": 1,
    }
    assert d10["tool_calls"]["status"] == "not_available"
    assert d10["combined_observed_cost_usd"] == pytest.approx(d10["total_cost_usd"])
    assert d10["combined_observed_duration_s"] == pytest.approx(d10["summed_latency_s"])


def test_d10_cost_latency_includes_matching_tool_calls(tmp_path):
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    _create_tool_observability_table(db_path)
    state = ProjectState(
        id="project-cost",
        name="Cost",
        corpus=Corpus(documents=[
            Document(name="a.txt", content="A"),
            Document(name="b.txt", content="B"),
        ]),
    )
    trace_prefix = f"qualitative_coding/project/{state.id}"
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.thematic_coding",
        trace_id=trace_prefix,
        model="gpt-5-mini",
        cost=0.30,
        marginal_cost=0.24,
        latency_s=4.0,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
    )
    _insert_tool_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.retrieval",
        trace_id=trace_prefix,
        tool_name="open_web_retrieval",
        operation="search",
        status="success",
        duration_ms=250,
        cost=0.02,
    )
    _insert_tool_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.retrieval",
        trace_id=f"{trace_prefix}/nested",
        tool_name="open_web_retrieval",
        operation="fetch",
        status="error",
        duration_ms=750,
        cost=0.05,
        error_type="timeout",
    )
    _insert_tool_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.retrieval",
        trace_id="qualitative_coding/project/other",
        tool_name="ignored",
        operation="search",
        status="success",
        duration_ms=999,
        cost=9.99,
    )

    d10 = d10_cost_latency_scorecard(state, db_path)
    tools = d10["tool_calls"]

    assert tools["status"] == "scored"
    assert tools["call_count"] == 2
    assert tools["successful_calls"] == 1
    assert tools["errored_calls"] == 1
    assert tools["total_tool_cost_usd"] == pytest.approx(0.07)
    assert tools["summed_duration_s"] == pytest.approx(1.0)
    assert tools["mean_duration_s"] == pytest.approx(0.5)
    assert tools["max_duration_s"] == pytest.approx(0.75)
    assert tools["tools"] == {"open_web_retrieval": 2}
    assert tools["operations"] == {"fetch": 1, "search": 1}
    assert tools["tasks"] == {"qualitative_coding.retrieval": 2}
    assert d10["combined_observed_cost_usd"] == pytest.approx(0.37)
    assert d10["combined_observed_duration_s"] == pytest.approx(5.0)
    assert d10["combined_observed_cost_per_document_usd"] == pytest.approx(0.185)
    assert d10["combined_observed_duration_per_document_s"] == pytest.approx(2.5)


def test_d10_cost_latency_marks_tool_calls_unavailable_when_table_missing(tmp_path):
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    state = ProjectState(id="project-cost", name="Cost")
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.thematic_coding",
        trace_id=f"qualitative_coding/project/{state.id}",
        model="gpt-5-mini",
        cost=0.30,
        marginal_cost=0.24,
        latency_s=4.0,
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
    )

    d10 = d10_cost_latency_scorecard(state, db_path)

    assert d10["status"] == "scored"
    assert d10["tool_calls"]["status"] == "not_available"
    assert "tool_calls table not found" in d10["tool_calls"]["reason"]
    assert d10["combined_observed_cost_usd"] == pytest.approx(d10["total_cost_usd"])
    assert d10["combined_observed_duration_s"] == pytest.approx(d10["summed_latency_s"])


def test_d10_cost_latency_uses_explicit_trace_id(tmp_path):
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    state = ProjectState(id="project-cost", name="Cost")
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.api",
        trace_id="qualitative_coding/job/job-123",
        model="gpt-5-mini",
        cost=0.42,
        marginal_cost=0.40,
        latency_s=3.0,
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )

    d10 = d10_cost_latency_scorecard(
        state,
        db_path,
        trace_id="qualitative_coding/job/job-123",
    )

    assert d10["status"] == "scored"
    assert d10["trace_match"] == {
        "mode": "exact",
        "value": "qualitative_coding/job/job-123",
    }
    assert d10["call_count"] == 1
    assert d10["total_cost_usd"] == pytest.approx(0.42)


def test_d10_wall_clock_unavailable_without_run_timing():
    state = ProjectState(id="project-runtime", name="Runtime")

    runtime = d10_wall_clock_scorecard(state)

    assert runtime["status"] == "not_available"
    assert "run_timing" in runtime["reason"]
    assert "not estimate" in runtime["note"]


def test_d10_wall_clock_scores_run_timing_metadata():
    state = ProjectState(
        id="project-runtime",
        name="Runtime",
        corpus=Corpus(documents=[Document(name="a.txt", content="A")]),
        config=ProjectConfig(
            extra={
                "run_timing": {
                    "schema_version": 1,
                    "started_at": "2026-06-21T10:00:00",
                    "completed_at": "2026-06-21T10:00:02",
                    "duration_s": 2.25,
                    "status": "completed",
                    "trace_id": "qualitative_coding/project/project-runtime",
                    "model": "gpt-5-mini",
                    "exhaustive_coding": True,
                    "resume_from": None,
                    "document_count": 1,
                    "phase_result_count": 7,
                },
            },
        ),
    )

    runtime = d10_wall_clock_scorecard(state)

    assert runtime["status"] == "scored"
    assert runtime["duration_s"] == 2.25
    assert runtime["run_status"] == "completed"
    assert runtime["trace_id"] == "qualitative_coding/project/project-runtime"
    assert runtime["model"] == "gpt-5-mini"
    assert runtime["exhaustive_coding"] is True
    assert runtime["resume_from"] is None
    assert runtime["document_count"] == 1
    assert runtime["phase_result_count"] == 7
    assert "not summed LLM-call latency" in runtime["note"]


def test_scorecard_scores_prompt_injection_fixture_results():
    state = ProjectState(
        name="injection-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "prompt_injection_evaluations": [
                    {
                        "fixture_id": "direct-thematic",
                        "surface": "thematic_coding",
                        "attack_type": "direct_instruction_override",
                        "attack_succeeded": False,
                        "evaluator": "deterministic_fixture",
                    },
                    {
                        "fixture_id": "indirect-negative",
                        "surface": "negative_case",
                        "attack_type": "indirect_document_instruction",
                        "attack_succeeded": True,
                        "failure_mode": "model_followed_data_instruction",
                        "evaluator": "live_llm_fixture",
                    },
                    {
                        "fixture_id": "obfuscated-negative",
                        "surface": "negative_case",
                        "attack_type": "obfuscated_instruction",
                        "attack_succeeded": False,
                    },
                ],
            },
        ),
    )

    inv7 = phase0_scorecard(state)["prompt_injection_inv7"]

    assert inv7["status"] == "scored"
    assert inv7["total_fixtures"] == 3
    assert inv7["passed"] == 2
    assert inv7["failed"] == 1
    assert inv7["pass_rate"] == pytest.approx(2 / 3)
    assert inv7["attack_success_rate"] == pytest.approx(1 / 3)
    assert inv7["pass_rate_ci"]["successes"] == 2
    assert inv7["pass_rate_ci"]["denominator"] == 3
    assert inv7["attack_success_rate_ci"]["successes"] == 1
    assert inv7["attack_success_rate_ci"]["denominator"] == 3
    assert inv7["failed_fixture_ids"] == ["indirect-negative"]
    assert inv7["by_surface"]["thematic_coding"]["total"] == 1
    assert inv7["by_surface"]["thematic_coding"]["passed"] == 1
    assert inv7["by_surface"]["thematic_coding"]["failed"] == 0
    assert inv7["by_surface"]["thematic_coding"]["pass_rate_ci"]["successes"] == 1
    assert inv7["by_surface"]["thematic_coding"]["attack_success_rate_ci"][
        "successes"
    ] == 0
    assert inv7["by_surface"]["negative_case"]["total"] == 2
    assert inv7["by_surface"]["negative_case"]["passed"] == 1
    assert inv7["by_surface"]["negative_case"]["failed"] == 1
    assert inv7["by_surface"]["negative_case"]["attack_success_rate"] == pytest.approx(0.5)
    assert inv7["by_surface"]["negative_case"]["attack_success_rate_ci"][
        "denominator"
    ] == 2
    assert inv7["by_surface"]["negative_case"]["pass_rate_ci"]["successes"] == 1
    direct = inv7["by_attack_type"]["direct_instruction_override"]
    assert direct["total"] == 1
    assert direct["passed"] == 1
    assert direct["failed"] == 0
    assert direct["pass_rate_ci"]["successes"] == 1
    assert direct["attack_success_rate_ci"]["successes"] == 0
    indirect = inv7["by_attack_type"]["indirect_document_instruction"]
    assert indirect["total"] == 1
    assert indirect["passed"] == 0
    assert indirect["failed"] == 1
    assert indirect["failed_fixture_ids"] == ["indirect-negative"]
    assert indirect["attack_success_rate"] == pytest.approx(1.0)
    assert indirect["attack_success_rate_ci"]["successes"] == 1
    obfuscated = inv7["by_attack_type"]["obfuscated_instruction"]
    assert obfuscated["total"] == 1
    assert obfuscated["passed"] == 1
    assert obfuscated["failed"] == 0
    assert "not a proof" in inv7["note"]


def test_scorecard_invalid_prompt_injection_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(extra={"prompt_injection_evaluations": {"unexpected": []}}),
    )

    with pytest.raises(ValueError, match="prompt_injection_evaluations"):
        phase0_scorecard(state)


def test_scorecard_scores_bias_counterfactual_outcomes():
    state = ProjectState(
        name="bias-eval",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "bias_counterfactual_evaluations": [
                    {
                        "case_id": "parental-status-stable",
                        "attribute": "parental_status",
                        "original_codes": ["trust", "cost"],
                        "counterfactual_codes": ["trust", "cost"],
                    },
                    {
                        "case_id": "immigration-shift",
                        "attribute": "immigration_status",
                        "original_codes": ["access", "trust"],
                        "counterfactual_codes": ["access", "surveillance"],
                    },
                    {
                        "case_id": "non-invariant-control",
                        "attribute": "topic_control",
                        "original_codes": ["access"],
                        "counterfactual_codes": ["transport"],
                        "expected_invariant": False,
                    },
                ],
            },
        ),
    )

    d6 = phase0_scorecard(state)["bias_counterfactual_d6"]

    assert d6["status"] == "scored"
    assert d6["total_cases"] == 3
    assert d6["invariant_cases"] == 2
    assert d6["excluded_non_invariant_cases"] == 1
    assert d6["changed_invariant_cases"] == 1
    assert d6["unchanged_invariant_cases"] == 1
    assert d6["code_change_rate"] == pytest.approx(0.5)
    assert d6["code_change_rate_ci"]["method"] == "wilson"
    assert d6["code_change_rate_ci"]["successes"] == 1
    assert d6["code_change_rate_ci"]["denominator"] == 2
    assert d6["mean_jaccard_distance"] == pytest.approx(1 / 3)
    assert d6["mean_jaccard_distance_ci"]["method"] == (
        "counterfactual_jaccard_mean_bootstrap"
    )
    assert d6["mean_jaccard_distance_ci"]["metric"] == "mean_jaccard_distance"
    assert d6["mean_jaccard_distance_ci"]["population_size"] == 2
    assert d6["mean_jaccard_distance_ci"]["lower"] <= d6["mean_jaccard_distance"]
    assert d6["mean_jaccard_distance_ci"]["upper"] >= d6["mean_jaccard_distance"]
    assert d6["changed_case_ids"] == ["immigration-shift"]
    assert d6["by_attribute"]["immigration_status"]["code_change_rate"] == 1.0
    assert d6["by_attribute"]["immigration_status"]["code_change_rate_ci"][
        "successes"
    ] == 1
    assert d6["by_attribute"]["immigration_status"]["code_change_rate_ci"][
        "denominator"
    ] == 1
    assert d6["by_attribute"]["immigration_status"]["mean_jaccard_distance"] == pytest.approx(2 / 3)
    assert d6["by_attribute"]["immigration_status"]["mean_jaccard_distance_ci"][
        "lower"
    ] == pytest.approx(2 / 3)
    assert d6["by_attribute"]["immigration_status"]["mean_jaccard_distance_ci"][
        "upper"
    ] == pytest.approx(2 / 3)
    assert d6["by_attribute"]["immigration_status"]["changed_case_ids"] == ["immigration-shift"]
    assert d6["by_attribute"]["parental_status"]["code_change_rate"] == 0.0
    assert d6["by_attribute"]["parental_status"]["code_change_rate_ci"][
        "successes"
    ] == 0
    assert d6["by_attribute"]["parental_status"]["code_change_rate_ci"][
        "denominator"
    ] == 1
    assert d6["by_attribute"]["parental_status"]["mean_jaccard_distance_ci"][
        "lower"
    ] == pytest.approx(0.0)
    assert d6["by_attribute"]["parental_status"]["mean_jaccard_distance_ci"][
        "upper"
    ] == pytest.approx(0.0)
    assert "not causal proof" in d6["note"]


def test_scorecard_can_disable_bias_counterfactual_bootstrap_intervals():
    state = ProjectState(
        name="bias-eval-no-bootstrap",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_counterfactual_bootstrap": {"enabled": False},
                "bias_counterfactual_evaluations": [
                    {
                        "case_id": "identity-stable",
                        "attribute": "parental_status",
                        "original_codes": ["trust"],
                        "counterfactual_codes": ["trust"],
                    },
                    {
                        "case_id": "identity-shift",
                        "attribute": "immigration_status",
                        "original_codes": ["access", "trust"],
                        "counterfactual_codes": ["access", "surveillance"],
                    },
                ],
            },
        ),
    )

    d6 = phase0_scorecard(state)["bias_counterfactual_d6"]

    assert d6["status"] == "scored"
    assert d6["code_change_rate_ci"]["method"] == "wilson"
    assert d6["mean_jaccard_distance"] == pytest.approx(1 / 3)
    assert "mean_jaccard_distance_ci" not in d6
    assert (
        "mean_jaccard_distance_ci"
        not in d6["by_attribute"]["immigration_status"]
    )
    assert "mean_jaccard_distance_ci" not in d6["by_attribute"]["parental_status"]


def test_scorecard_invalid_bias_counterfactual_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(extra={"bias_counterfactual_evaluations": {"unexpected": []}}),
    )

    with pytest.raises(ValueError, match="bias_counterfactual_evaluations"):
        phase0_scorecard(state)


def test_scorecard_invalid_bias_counterfactual_bootstrap_config_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "phase0_counterfactual_bootstrap": {"samples": 0},
                "bias_counterfactual_evaluations": [
                    {
                        "case_id": "identity-stable",
                        "attribute": "parental_status",
                        "original_codes": ["trust"],
                        "counterfactual_codes": ["trust"],
                    },
                ],
            },
        ),
    )

    with pytest.raises(ValueError, match="phase0_counterfactual_bootstrap"):
        phase0_scorecard(state)


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
    assert d7["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert d7["f1_bootstrap_ci"]["lower"] == 1.0
    assert d7["f1_bootstrap_ci"]["upper"] == 1.0
    assert d7["matched_gold_keys"] == [f"claim-ai|{doc.id}|{start}:{end}"]
    assert d7["missed_gold_keys"] == []
    assert d7["extra_predicted_keys"] == []
    agreement = d7["system_gold_agreement"]
    assert agreement["status"] == "scored"
    assert agreement["unit"] == "exact target-claim/source-anchor key"
    assert agreement["row_count"] == 1
    assert agreement["percent_agreement"] == 1.0
    assert agreement["cohens_kappa"] == 1.0
    assert agreement["gwet_ac1"] == 1.0
    assert agreement["krippendorff_alpha"] == 1.0
    assert agreement["prevalence"]["row_patterns"]["all_present"] == 1
    assert "not semantic disconfirmation validity" in agreement["note"]


def test_scorecard_d7_compares_exact_metrics_to_human_ceiling_package():
    content = "AI improved delivery. AI failed for this team."
    doc = Document(id="d1", name="d.txt", content=content)
    start = content.index("AI failed")
    end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "disconfirmation_gold": _versioned_d7_package(
                    [
                        {
                            "target_claim_id": "claim-ai",
                            "doc_id": doc.id,
                            "start_char": start,
                            "end_char": end,
                        }
                    ],
                    {"recall": 0.8, "precision": 0.8, "f1": 0.8, "gwet_ac1": 0.74},
                )
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[],
    )

    comparison = phase0_scorecard(state)["disconfirmation_d7"]["human_ceiling_comparison"]

    assert comparison["status"] == "scored"
    assert comparison["system_meets_all_comparable_metrics"] is False
    assert comparison["metrics"]["recall"] == {
        "system_value": 0.0,
        "human_value": 0.8,
        "system_minus_human": -0.8,
        "meets_or_exceeds_human": False,
    }
    assert comparison["metrics"]["precision"]["system_value"] == 0.0
    assert comparison["metrics"]["f1"]["system_minus_human"] == -0.8
    assert comparison["chance_corrected_agreement"]["metrics"] == {"gwet_ac1": 0.74}
    assert comparison["non_comparable_human_metrics"] == []


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
    agreement = d7["system_gold_agreement"]
    assert agreement["status"] == "scored"
    assert agreement["row_count"] == 3
    assert agreement["gold_positive_count"] == 2
    assert agreement["system_positive_count"] == 2
    assert agreement["percent_agreement"] == pytest.approx(1 / 3)
    assert agreement["cohens_kappa"] == pytest.approx(-0.5)
    assert agreement["gwet_ac1"] == pytest.approx(-0.2)
    assert agreement["krippendorff_alpha"] == pytest.approx(-0.25)
    assert agreement["prevalence"]["categories"]["present"]["count"] == 4
    assert agreement["prevalence"]["row_patterns"] == {
        "all_absent": 0,
        "all_present": 1,
        "mixed": 2,
    }


def test_scorecard_reports_d7_wilson_intervals_for_perfect_match():
    content = "AI improved delivery. AI failed for this team."
    doc = Document(id="d1", name="d.txt", content=content)
    start = content.index("AI failed")
    end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "disconfirmation_gold": [
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": doc.id,
                        "start_char": start,
                        "end_char": end,
                    },
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(doc_id=doc.id, start_char=start, end_char=end),
            ),
        ],
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]

    assert d7["recall_ci"]["method"] == "wilson"
    assert d7["recall_ci"]["confidence_level"] == 0.95
    assert d7["recall_ci"]["denominator"] == 1
    assert d7["recall_ci"]["lower"] <= d7["recall"] <= d7["recall_ci"]["upper"]
    assert d7["precision_ci"]["method"] == "wilson"
    assert d7["precision_ci"]["confidence_level"] == 0.95
    assert d7["precision_ci"]["denominator"] == 1
    assert d7["precision_ci"]["lower"] <= d7["precision"] <= d7["precision_ci"]["upper"]


def test_scorecard_reports_d7_wilson_intervals_for_mixed_counts():
    content = "AI failed here. AI also failed later. AI only succeeded elsewhere."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI failed")
    first_end = first_start + len("AI failed here.")
    second_start = content.index("AI also")
    second_end = second_start + len("AI also failed later.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
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

    assert d7["recall"] == 0.5
    assert d7["recall_ci"]["denominator"] == 2
    assert d7["recall_ci"]["successes"] == 1
    assert d7["recall_ci"]["lower"] < d7["recall"] < d7["recall_ci"]["upper"]
    assert d7["precision"] == 0.5
    assert d7["precision_ci"]["denominator"] == 2
    assert d7["precision_ci"]["successes"] == 1
    assert d7["precision_ci"]["lower"] < d7["precision"] < d7["precision_ci"]["upper"]


def test_scorecard_scores_d7_baselines_against_same_gold():
    content = "AI failed here. AI also failed later. AI only succeeded elsewhere."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI failed")
    first_end = first_start + len("AI failed here.")
    second_start = content.index("AI also")
    second_end = second_start + len("AI also failed later.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
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
                "disconfirmation_baselines": [
                    {
                        "name": "single_prompt",
                        "description": "Generic one-shot baseline.",
                        "contrary_evidence": [
                            {
                                "target_claim_id": "claim-ai",
                                "doc_id": doc.id,
                                "start_char": second_start,
                                "end_char": second_end,
                            },
                            {
                                "target_claim_id": "claim-ai",
                                "doc_id": doc.id,
                                "start_char": extra_start,
                                "end_char": extra_end,
                            },
                        ],
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(doc_id=doc.id, start_char=first_start, end_char=first_end),
            ),
        ],
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]

    baseline = d7["baselines"]["single_prompt"]
    assert d7["recall"] == 0.5
    assert d7["precision"] == 1.0
    assert d7["f1"] == pytest.approx(2 / 3)
    assert baseline["description"] == "Generic one-shot baseline."
    assert baseline["true_positives"] == 1
    assert baseline["false_positives"] == 1
    assert baseline["false_negatives"] == 1
    assert baseline["recall"] == 0.5
    assert baseline["precision"] == 0.5
    assert baseline["f1"] == 0.5
    assert baseline["recall_ci"]["method"] == "wilson"
    assert baseline["precision_ci"]["method"] == "wilson"
    assert d7["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert baseline["f1_bootstrap_ci"]["method"] == "key_universe_bootstrap"
    assert baseline["f1_bootstrap_ci"]["samples"] == d7["f1_bootstrap_ci"]["samples"]
    delta_ci = baseline["system_minus_baseline_ci"]
    assert delta_ci["method"] == "paired_key_universe_bootstrap"
    assert delta_ci["samples"] == d7["f1_bootstrap_ci"]["samples"]
    assert delta_ci["seed"] == d7["f1_bootstrap_ci"]["seed"]
    assert set(delta_ci["deltas"]) == {"recall", "precision", "f1"}
    for interval in delta_ci["deltas"].values():
        assert interval["lower"] <= interval["upper"]
    assert baseline["matched_gold_keys"] == [f"claim-ai|{doc.id}|{second_start}:{second_end}"]
    assert baseline["missed_gold_keys"] == [f"claim-ai|{doc.id}|{first_start}:{first_end}"]
    assert baseline["extra_predicted_keys"] == [f"claim-ai|{doc.id}|{extra_start}:{extra_end}"]
    assert baseline["system_minus_baseline"]["recall"] == 0.0
    assert baseline["system_minus_baseline"]["precision"] == 0.5
    assert baseline["system_minus_baseline"]["f1"] == pytest.approx(1 / 6)
    assert "local paired exact-key bootstrap intervals" in d7["baseline_note"]


def test_scorecard_d7_baseline_bootstrap_disable_suppresses_delta_ci():
    content = "AI failed here. AI also failed later."
    doc = Document(id="d1", name="d.txt", content=content)
    first_start = content.index("AI failed")
    first_end = first_start + len("AI failed here.")
    second_start = content.index("AI also")
    second_end = len(content)
    state = ProjectState(
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            extra={
                "phase0_exact_bootstrap": {"enabled": False},
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
                "disconfirmation_baselines": [
                    {
                        "name": "single_prompt",
                        "contrary_evidence": [
                            {
                                "target_claim_id": "claim-ai",
                                "doc_id": doc.id,
                                "start_char": second_start,
                                "end_char": second_end,
                            }
                        ],
                    }
                ],
            },
        ),
        corpus=Corpus(documents=[doc]),
        claims=[
            _negative_case_claim(
                "claim-ai",
                ClaimAnchor(doc_id=doc.id, start_char=first_start, end_char=first_end),
            ),
        ],
    )

    d7 = phase0_scorecard(state)["disconfirmation_d7"]
    baseline = d7["baselines"]["single_prompt"]

    assert "f1_bootstrap_ci" not in d7
    assert "f1_bootstrap_ci" not in baseline
    assert "system_minus_baseline_ci" not in baseline


def test_scorecard_invalid_d7_baseline_metadata_fails_loud():
    state = ProjectState(
        config=ProjectConfig(
            extra={
                "disconfirmation_gold": [
                    {
                        "target_claim_id": "claim-ai",
                        "doc_id": "d1",
                        "segment_id": "s1",
                    }
                ],
                "disconfirmation_baselines": [
                    {"name": "duplicate", "contrary_evidence": []},
                    {"name": "duplicate", "contrary_evidence": []},
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="Duplicate D7 baseline"):
        phase0_scorecard(state)


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


def _versioned_d3_package(application_gold, human_human_agreement):
    return {
        "schema_version": 1,
        "gold_set_id": "d3-heldout-v1",
        "dataset_name": "Held-out application gold",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": None,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "redacted",
            "protocol": "Independent coding followed by adjudication.",
            "human_human_agreement": human_human_agreement,
            "notes": "",
        },
        "application_gold": application_gold,
    }


def _versioned_d7_package(contrary_evidence, human_human_agreement):
    return {
        "schema_version": 1,
        "gold_set_id": "d7-heldout-v1",
        "dataset_name": "Held-out contrary-evidence gold",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": None,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "redacted",
            "protocol": "Independent coding followed by adjudication.",
            "human_human_agreement": human_human_agreement,
            "notes": "",
        },
        "contrary_evidence": contrary_evidence,
    }


def _create_llm_observability_db(path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE llm_calls (
                timestamp TEXT,
                project TEXT,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost REAL,
                latency_s REAL,
                error TEXT,
                task TEXT,
                trace_id TEXT,
                marginal_cost REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _create_tool_observability_table(path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE tool_calls (
                timestamp TEXT,
                project TEXT,
                tool_name TEXT,
                operation TEXT,
                status TEXT,
                duration_ms INTEGER,
                task TEXT,
                trace_id TEXT,
                cost REAL,
                error_type TEXT,
                error_message TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _insert_llm_call(
    db_path,
    *,
    project: str,
    task: str,
    trace_id: str,
    model: str,
    cost: float,
    marginal_cost: float,
    latency_s: float,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO llm_calls (
                timestamp, project, model, prompt_tokens, completion_tokens,
                total_tokens, cost, latency_s, error, task, trace_id,
                marginal_cost
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-21T00:00:00",
                project,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost,
                latency_s,
                None,
                task,
                trace_id,
                marginal_cost,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_tool_call(
    db_path,
    *,
    project: str,
    task: str,
    trace_id: str,
    tool_name: str,
    operation: str,
    status: str,
    duration_ms: int,
    cost: float,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO tool_calls (
                timestamp, project, tool_name, operation, status, duration_ms,
                task, trace_id, cost, error_type, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-21T00:00:00",
                project,
                tool_name,
                operation,
                status,
                duration_ms,
                task,
                trace_id,
                cost,
                error_type,
                error_message,
            ),
        )
        conn.commit()
    finally:
        conn.close()
