"""Read-surface helpers for first-class observed patterns."""

from __future__ import annotations

from collections import Counter
from typing import Any

from qc_clean.core.claims import format_claim_anchor_details
from qc_clean.schemas.domain import ObservedPattern, ProjectState


def observed_pattern_row(
    pattern: ObservedPattern,
    *,
    include_anchor_details: bool = True,
) -> dict[str, Any]:
    """Return a compact machine-readable row for an observed pattern."""
    row: dict[str, Any] = {
        "id": pattern.id,
        "source_stage": pattern.source_stage,
        "pattern_kind": pattern.pattern_kind.value,
        "summary": pattern.summary,
        "code_ids": list(pattern.code_ids),
        "doc_ids": list(pattern.doc_ids),
        "application_ids": list(pattern.application_ids),
        "support_anchor_count": len(pattern.support_anchors),
        "strength": pattern.strength,
        "count": pattern.count,
        "total": pattern.total,
        "metadata": dict(pattern.metadata),
        "causal_interpretation_status": pattern.causal_interpretation_status.value,
        "created_by": pattern.created_by.value,
        "created_at": pattern.created_at,
    }
    if include_anchor_details:
        row["support_anchor_details"] = format_claim_anchor_details(
            pattern.support_anchors
        )
    return row


def summarize_observed_patterns(state: ProjectState) -> dict[str, Any]:
    """Summarize observed-pattern counts without adding interpretation."""
    return {
        "total_patterns": len(state.observed_patterns),
        "by_kind": dict(Counter(p.pattern_kind.value for p in state.observed_patterns)),
        "by_stage": dict(Counter(p.source_stage for p in state.observed_patterns)),
        "by_causal_interpretation_status": dict(
            Counter(
                p.causal_interpretation_status.value
                for p in state.observed_patterns
            )
        ),
    }
