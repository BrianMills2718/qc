"""Evaluation-harness Phase 0 scorecard (see docs/EVALUATION_HARNESS.md).

Phase 0 = the cheap, deterministic, no-new-human metrics computable directly from
a saved ``ProjectState``: the D1 grounding rate, plus reliability/stability
summaries when present. This is the harness skeleton; richer metrics (gold-vs
agreement, bias, calibration) and the ``prompt_eval`` integration come later.

Deterministic and LLM-free so it can run in CI and be diffed across runs.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from math import sqrt
from pathlib import Path
import sqlite3
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError, model_validator

from qc_clean.core.grounding import verify_grounding
from qc_clean.core.pipeline.saturation import assess_category_saturation
from qc_clean.core.segmentation import compute_coverage
from qc_clean.schemas.domain import ClaimAnchor, ClaimKind, ProjectState


_D7_GOLD_EXTRA_KEY = "disconfirmation_gold"
_PROMPT_INJECTION_EXTRA_KEY = "prompt_injection_evaluations"
DEFAULT_OBSERVABILITY_DB_PATH = Path.home() / "projects" / "data" / "llm_observability.db"
_WILSON_Z_95 = 1.959963984540054


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


class PromptInjectionEvaluation(BaseModel):
    """External prompt-injection fixture outcome used for INV-7 scoring."""

    fixture_id: str = Field(description="Stable ID for the adversarial fixture")
    surface: str = Field(description="Prompt surface tested, such as thematic_coding")
    attack_type: str = Field(
        default="unspecified",
        description="Attack class, such as direct_instruction_override or indirect_document_instruction",
    )
    attack_succeeded: bool = Field(
        description="True when the model/application followed or leaked because of the injected instruction"
    )
    failure_mode: str | None = Field(
        default=None,
        description="Optional explanation when the attack succeeded",
    )
    evaluator: str = Field(
        default="unspecified",
        description="Evaluator or harness that produced this fixture outcome",
    )
    notes: str = Field(
        default="",
        description="Optional human-readable notes for inspection",
    )

    @model_validator(mode="after")
    def require_nonempty_identifiers(self) -> "PromptInjectionEvaluation":
        """Require stable grouping keys before computing fixture rates."""
        if not self.fixture_id.strip():
            raise ValueError("prompt injection fixture_id must be non-empty")
        if not self.surface.strip():
            raise ValueError("prompt injection surface must be non-empty")
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
        # INV-4 — category adequacy diagnostic, not proof of GT saturation.
        "category_saturation": assess_category_saturation(state).model_dump(),
        # INV-7 — prompt-injection fixture results when an external evaluator provides them.
        "prompt_injection_inv7": prompt_injection_scorecard(state),
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
        "cost_note": "D10 cost/latency is populated by the bench CLI from llm_client observability rows; never estimate it from ProjectState.",
    }
    return card


def d10_cost_latency_scorecard(
    state: ProjectState,
    db_path: Path | str = DEFAULT_OBSERVABILITY_DB_PATH,
    *,
    project: str = "qualitative_coding",
    trace_id: str | None = None,
) -> Dict[str, Any]:
    """Score D10 LLM cost/latency from real llm_client observability rows."""
    db_path = Path(db_path)
    trace_match = _trace_match_for_state(state, trace_id)
    if not db_path.exists():
        return {
            "status": "not_available",
            "reason": f"Observability DB not found: {db_path}",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "D10 cost/latency requires real llm_client observability rows; do not estimate from ProjectState.",
        }

    try:
        rows = _fetch_d10_llm_rows(db_path, project=project, trace_match=trace_match)
    except sqlite3.Error as exc:
        return {
            "status": "not_available",
            "reason": f"Could not read llm_calls observability rows: {exc}",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "D10 cost/latency requires real llm_client observability rows; do not estimate from ProjectState.",
        }

    if not rows:
        return {
            "status": "not_available",
            "reason": "No llm_calls rows matched the project and trace selector.",
            "source": str(db_path),
            "project": project,
            "trace_match": trace_match,
            "note": "No D10 score is reported without matching real observability rows; do not estimate from ProjectState.",
        }

    call_count = len(rows)
    total_cost = sum(_float_or_zero(row["cost"]) for row in rows)
    marginal_cost = sum(_float_or_zero(row["marginal_cost"]) for row in rows)
    prompt_tokens = sum(_int_or_zero(row["prompt_tokens"]) for row in rows)
    completion_tokens = sum(_int_or_zero(row["completion_tokens"]) for row in rows)
    total_tokens = sum(_int_or_zero(row["total_tokens"]) for row in rows)
    latencies = [_float_or_zero(row["latency_s"]) for row in rows]
    summed_latency = sum(latencies)
    document_count = state.corpus.num_documents
    errored_calls = sum(1 for row in rows if _row_has_error(row))

    return {
        "status": "scored",
        "source": str(db_path),
        "project": project,
        "trace_match": trace_match,
        "call_count": call_count,
        "successful_calls": call_count - errored_calls,
        "errored_calls": errored_calls,
        "total_cost_usd": total_cost,
        "total_marginal_cost_usd": marginal_cost,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "summed_latency_s": summed_latency,
        "mean_latency_s": _safe_div(summed_latency, call_count),
        "max_latency_s": max(latencies) if latencies else 0.0,
        "document_count": document_count,
        "cost_per_document_usd": _safe_div_or_none(total_cost, document_count),
        "latency_per_document_s": _safe_div_or_none(summed_latency, document_count),
        "first_timestamp": min(str(row["timestamp"]) for row in rows),
        "last_timestamp": max(str(row["timestamp"]) for row in rows),
        "models": dict(sorted(Counter(str(row["model"] or "") for row in rows).items())),
        "tasks": dict(sorted(Counter(str(row["task"] or "") for row in rows).items())),
        "note": (
            "D10 uses summed observed LLM-call latency and real logged cost from "
            "llm_client; it is not full pipeline wall-clock time and is not a "
            "baseline comparison."
        ),
    }


def _trace_match_for_state(state: ProjectState, trace_id: str | None) -> Dict[str, str]:
    """Return the D10 trace selector."""
    if trace_id:
        return {"mode": "exact", "value": trace_id}
    return {"mode": "prefix", "value": f"qualitative_coding/project/{state.id}"}


def _fetch_d10_llm_rows(
    db_path: Path,
    *,
    project: str,
    trace_match: Dict[str, str],
) -> list[sqlite3.Row]:
    """Fetch D10 rows from the observability database."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        required = {
            "timestamp",
            "project",
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cost",
            "latency_s",
            "error",
            "task",
            "trace_id",
            "marginal_cost",
        }
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(llm_calls)").fetchall()}
        missing = sorted(required - columns)
        if missing:
            raise sqlite3.OperationalError(
                "llm_calls table missing required D10 column(s): " + ", ".join(missing)
            )

        error_select = "error"
        if "error_type" in columns:
            error_select += ", error_type"
        if "validation_errors" in columns:
            error_select += ", validation_errors"
        trace_clause = "trace_id = ?" if trace_match["mode"] == "exact" else "trace_id LIKE ?"
        trace_value = trace_match["value"] if trace_match["mode"] == "exact" else f"{trace_match['value']}%"
        query = f"""
            SELECT timestamp, model, prompt_tokens, completion_tokens, total_tokens,
                   cost, latency_s, task, trace_id, marginal_cost, {error_select}
            FROM llm_calls
            WHERE project = ?
              AND {trace_clause}
            ORDER BY timestamp ASC
        """
        return list(conn.execute(query, (project, trace_value)).fetchall())
    finally:
        conn.close()


def _row_has_error(row: sqlite3.Row) -> bool:
    """Return true when an observability row records an error-like field."""
    return any(
        key in row.keys() and row[key]
        for key in ("error", "error_type", "validation_errors")
    )


def _int_or_zero(value: Any) -> int:
    """Convert nullable token counts to integers."""
    return int(value or 0)


def _float_or_zero(value: Any) -> float:
    """Convert nullable numeric DB values to floats."""
    return float(value or 0.0)


def _safe_div_or_none(numerator: float, denominator: float) -> float | None:
    """Return None for undefined reporting denominators."""
    if denominator == 0:
        return None
    return numerator / denominator


def prompt_injection_scorecard(state: ProjectState) -> Dict[str, Any]:
    """Score externally supplied INV-7 prompt-injection fixture outcomes."""
    evaluations = _prompt_injection_evaluations(state)
    if not evaluations:
        return {
            "status": "not_available",
            "reason": (
                "No prompt-injection fixture results found at "
                f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}']; scoring "
                "requires externally supplied adversarial evaluation outcomes."
            ),
            "note": (
                "Absence of INV-7 fixture data is not evidence of prompt-injection "
                "robustness; deterministic prompt-boundary tests are separate from "
                "live adversarial evaluation."
            ),
        }

    total = len(evaluations)
    failed = sorted(ev.fixture_id for ev in evaluations if ev.attack_succeeded)
    passed = total - len(failed)
    return {
        "status": "scored",
        "source": f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}']",
        "total_fixtures": total,
        "passed": passed,
        "failed": len(failed),
        "pass_rate": _safe_div(passed, total),
        "attack_success_rate": _safe_div(len(failed), total),
        "failed_fixture_ids": failed,
        "by_surface": _prompt_injection_by_surface(evaluations),
        "note": (
            "Scores externally supplied prompt-injection fixture outcomes. This is "
            "a measurement substrate, not a proof of prompt-injection robustness."
        ),
    }


def _prompt_injection_evaluations(state: ProjectState) -> list[PromptInjectionEvaluation]:
    """Load INV-7 fixture outcomes from project config metadata."""
    raw = state.config.extra.get(_PROMPT_INJECTION_EXTRA_KEY)
    if raw is None:
        return []
    if isinstance(raw, dict) and _PROMPT_INJECTION_EXTRA_KEY in raw:
        raw = raw[_PROMPT_INJECTION_EXTRA_KEY]
    if not isinstance(raw, list):
        raise ValueError(
            f"ProjectState.config.extra['{_PROMPT_INJECTION_EXTRA_KEY}'] must be a list "
            "of prompt-injection fixture outcomes"
        )
    try:
        return [PromptInjectionEvaluation.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid prompt_injection_evaluations metadata: {exc}") from exc


def _prompt_injection_by_surface(
    evaluations: list[PromptInjectionEvaluation],
) -> Dict[str, Dict[str, Any]]:
    """Summarize INV-7 fixture outcomes by prompt surface."""
    summary: Dict[str, Dict[str, Any]] = {}
    for ev in evaluations:
        bucket = summary.setdefault(
            ev.surface,
            {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "attack_success_rate": 0.0,
                "failed_fixture_ids": [],
            },
        )
        bucket["total"] += 1
        if ev.attack_succeeded:
            bucket["failed"] += 1
            bucket["failed_fixture_ids"].append(ev.fixture_id)
        else:
            bucket["passed"] += 1
    for bucket in summary.values():
        bucket["failed_fixture_ids"] = sorted(bucket["failed_fixture_ids"])
        bucket["attack_success_rate"] = _safe_div(bucket["failed"], bucket["total"])
        bucket["pass_rate"] = _safe_div(bucket["passed"], bucket["total"])
    return dict(sorted(summary.items()))


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
    recall_denominator = true_positives + false_negatives
    precision_denominator = true_positives + false_positives

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
        "recall_ci": _wilson_interval(true_positives, recall_denominator),
        "precision_ci": _wilson_interval(true_positives, precision_denominator),
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


def _wilson_interval(
    successes: int,
    denominator: int,
    *,
    confidence_level: float = 0.95,
) -> Dict[str, Any]:
    """Return a Wilson score interval for a binomial proportion."""
    if confidence_level != 0.95:
        raise ValueError("Only 95% Wilson intervals are supported in Phase 0")
    if successes < 0 or denominator < 0:
        raise ValueError("Wilson interval counts must be non-negative")
    if successes > denominator:
        raise ValueError("Wilson interval successes cannot exceed denominator")
    if denominator == 0:
        return {
            "method": "wilson",
            "confidence_level": confidence_level,
            "successes": successes,
            "denominator": denominator,
            "lower": None,
            "upper": None,
            "note": "undefined denominator",
        }

    z = _WILSON_Z_95
    p_hat = successes / denominator
    z2 = z * z
    denom = 1 + (z2 / denominator)
    center = (p_hat + (z2 / (2 * denominator))) / denom
    margin = (
        z * sqrt((p_hat * (1 - p_hat) / denominator) + (z2 / (4 * denominator * denominator)))
    ) / denom
    return {
        "method": "wilson",
        "confidence_level": confidence_level,
        "successes": successes,
        "denominator": denominator,
        "lower": max(0.0, center - margin),
        "upper": min(1.0, center + margin),
    }
