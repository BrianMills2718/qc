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

from pydantic import BaseModel, Field, ValidationError, model_validator

from qc_clean.core.grounding import verify_grounding
from qc_clean.core.segmentation import compute_coverage
from qc_clean.schemas.domain import ClaimAnchor, ClaimKind, ProjectState


_D7_GOLD_EXTRA_KEY = "disconfirmation_gold"


class DisconfirmationGoldAnchor(BaseModel):
    """Human/adjudicated contrary-evidence anchor used for D7 scoring."""

    target_claim_id: str = Field(description="AnalyticClaim ID the gold contrary evidence challenges")
    doc_id: str = Field(description="Document containing the contrary evidence")
    start_char: int | None = Field(default=None, description="Start offset of the gold source span")
    end_char: int | None = Field(default=None, description="End offset of the gold source span")
    segment_id: str | None = Field(default=None, description="Segment ID when span offsets are unavailable")
    quote_text: str = Field(default="", description="Optional evidence text for human inspection")

    @model_validator(mode="after")
    def require_exact_key(self) -> "DisconfirmationGoldAnchor":
        """Require a deterministic comparison key for every gold record."""
        has_start = self.start_char is not None
        has_end = self.end_char is not None
        if has_start != has_end:
            raise ValueError("D7 gold anchors must provide both start_char and end_char")
        if has_start and has_end:
            if self.start_char is None or self.end_char is None:
                raise ValueError("D7 gold span offsets are incomplete")
            if self.start_char < 0 or self.end_char <= self.start_char:
                raise ValueError("D7 gold span offsets must satisfy 0 <= start_char < end_char")
            return self
        if not self.segment_id:
            raise ValueError("D7 gold anchors require span offsets or a segment_id")
        return self


def phase0_scorecard(state: ProjectState) -> Dict[str, Any]:
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
        # D7 — disconfirmation quality when human/adjudicated gold is present.
        "disconfirmation_d7": disconfirmation_d7_scorecard(state),
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


def disconfirmation_d7_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score negative-case contrary anchors against D7 gold, if available."""
    gold = _d7_gold_annotations(state)
    if not gold:
        return {
            "status": "not_available",
            "reason": (
                "No D7 disconfirmation gold annotations found at "
                f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}']; scoring requires "
                "human/adjudicated contrary-evidence anchors."
            ),
            "note": "D7 is gold-dependent; absence of this section is not evidence of disconfirmation quality.",
        }

    gold_keys = {_key_for_gold(anchor) for anchor in gold}
    predicted_keys, unscored_predicted = _predicted_disconfirmation_keys(state)

    matched = sorted(gold_keys & predicted_keys)
    missed = sorted(gold_keys - predicted_keys)
    extra = sorted(predicted_keys - gold_keys)
    true_positives = len(matched)
    false_positives = len(extra) + len(unscored_predicted)
    false_negatives = len(missed)
    recall = _safe_div(true_positives, true_positives + false_negatives)
    precision = _safe_div(true_positives, true_positives + false_positives)
    f1 = _safe_div(2 * precision * recall, precision + recall)

    return {
        "status": "scored",
        "gold_source": f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}']",
        "gold_count": len(gold_keys),
        "predicted_count": len(predicted_keys) + len(unscored_predicted),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "matched_gold_keys": matched,
        "missed_gold_keys": missed,
        "extra_predicted_keys": extra,
        "unscored_predicted_anchors": unscored_predicted,
        "note": (
            "Exact target-claim/source-anchor D7 score. This is a measurement substrate, "
            "not a SOTA/parity claim without a held-out adjudicated benchmark."
        ),
    }


def _d7_gold_annotations(state: ProjectState) -> list[DisconfirmationGoldAnchor]:
    """Load D7 gold annotations from project config metadata."""
    raw = state.config.extra.get(_D7_GOLD_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and "contrary_evidence" in raw:
        raw = raw["contrary_evidence"]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_D7_GOLD_EXTRA_KEY}'] must be a list of D7 gold anchors"
        )
    try:
        return [DisconfirmationGoldAnchor.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 disconfirmation gold annotations: {exc}") from exc


def _predicted_disconfirmation_keys(state: ProjectState) -> tuple[set[str], list[str]]:
    """Return scoreable predicted D7 keys and unscoreable anchor descriptions."""
    keys: set[str] = set()
    unscored: list[str] = []
    for claim in state.claims:
        if claim.claim_kind != ClaimKind.NEGATIVE_CASE:
            continue
        if not claim.scope.claim_ids:
            unscored.append(f"{claim.id}|missing-target-claim")
            continue
        if not claim.contrary_anchors:
            unscored.append(f"{claim.id}|missing-contrary-anchor")
            continue
        for target_claim_id in claim.scope.claim_ids:
            for anchor in claim.contrary_anchors:
                key = _key_for_anchor(
                    target_claim_id=target_claim_id,
                    doc_id=anchor.doc_id,
                    start_char=anchor.start_char,
                    end_char=anchor.end_char,
                    segment_id=anchor.segment_id,
                )
                if key is None:
                    unscored.append(_unscored_anchor_description(claim.id, target_claim_id, anchor))
                    continue
                keys.add(key)
    return keys, sorted(unscored)


def _key_for_gold(anchor: DisconfirmationGoldAnchor) -> str:
    """Build the exact comparison key for a gold D7 anchor."""
    key = _key_for_anchor(
        target_claim_id=anchor.target_claim_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        segment_id=anchor.segment_id,
    )
    if key is None:
        raise ValueError("D7 gold anchor validation failed to produce a comparison key")
    return key


def _key_for_anchor(
    *,
    target_claim_id: str,
    doc_id: str,
    start_char: int | None,
    end_char: int | None,
    segment_id: str | None,
) -> str | None:
    """Build an exact D7 comparison key from claim identity plus source anchor."""
    if start_char is not None and end_char is not None:
        return f"{target_claim_id}|{doc_id}|{start_char}:{end_char}"
    if segment_id:
        return f"{target_claim_id}|{doc_id}|segment:{segment_id}"
    return None


def _unscored_anchor_description(claim_id: str, target_claim_id: str, anchor: ClaimAnchor) -> str:
    """Describe a predicted contrary anchor that cannot enter exact D7 scoring."""
    return (
        f"{claim_id}|target={target_claim_id}|doc={anchor.doc_id}|"
        "missing-span-or-segment"
    )


def _safe_div(numerator: float, denominator: float) -> float:
    """Return zero for undefined score fractions."""
    if denominator == 0:
        return 0.0
    return numerator / denominator
