"""Evaluation-harness Phase 0 scorecard (see docs/EVALUATION_HARNESS.md).

Phase 0 = the cheap, deterministic, no-new-human metrics computable directly from
a saved ``ProjectState``: the D1 grounding rate, plus reliability/stability
summaries when present. This is the harness skeleton; richer metrics (gold-vs
agreement, bias, calibration) and the ``prompt_eval`` integration come later.

Deterministic and LLM-free so it can run in CI and be diffed across runs.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict

from qc_clean.core.grounding import verify_grounding
from qc_clean.core.segmentation import compute_coverage


def phase0_scorecard(state) -> Dict[str, Any]:
    """Compute the Phase 0 scorecard for one project state."""
    card: Dict[str, Any] = {
        "project": state.name,
        "methodology": state.config.methodology.value,
        "documents": state.corpus.num_documents,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        # D1 — grounding (the headline structural-rigor metric).
        "grounding": asdict(verify_grounding(state)),
        # D2 — coverage over the segment universe (INV-8 denominator).
        "coverage": asdict(compute_coverage(state)),
        "data_warnings": list(state.data_warnings),
    }

    # D5 — consistency (reported, NOT validity; see theory doc §11/§15).
    if state.irr_result is not None:
        card["reliability_llm_pass_agreement"] = {
            "percent_agreement": state.irr_result.percent_agreement,
            "cohens_kappa": state.irr_result.cohens_kappa,
            "fleiss_kappa": state.irr_result.fleiss_kappa,
            "interpretation": state.irr_result.interpretation,
            "note": "code-DISCOVERY agreement, not application-level; consistency not validity",
        }
    if state.stability_result is not None:
        card["stability"] = {
            "overall_stability": state.stability_result.overall_stability,
            "stable": len(state.stability_result.stable_codes),
            "moderate": len(state.stability_result.moderate_codes),
            "unstable": len(state.stability_result.unstable_codes),
        }

    # Honest framing so a reader never mistakes Phase 0 for a SOTA claim.
    # The coverage note depends on whether this run was exhaustive: in "examined"
    # mode every segment carries a coding decision, so examined-and-judged
    # coverage is real; in "traversal" mode only touched segments are counted.
    if card["coverage"].get("mode") == "examined":
        coverage_note = (
            "examined-and-judged coverage available: every segment carries a coding "
            "decision (INV-8 exhaustive mode). Use `examined_rate` as the defensible "
            "denominator; `covered_rate` still reports only segments with anchored evidence."
        )
    else:
        coverage_note = (
            "traversal coverage only (segments with anchored evidence); examined-and-judged "
            "coverage is NOT available — re-run with `--exhaustive` for per-segment decisions (INV-8)"
        )
    card["_meta"] = {
        "phase": 0,
        "claims": "capability only — not a SOTA/parity claim (needs gold + baselines; see EVALUATION_HARNESS.md §7)",
        "coverage_note": coverage_note,
        "cost_note": "LLM cost is in the observability DB, not in ProjectState; queried separately",
    }
    return card
