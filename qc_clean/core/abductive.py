"""Read-surface helpers for abductive candidate explanations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from qc_clean.schemas.domain import AbductiveCandidateExplanation, ProjectState


def abductive_candidate_row(
    candidate: AbductiveCandidateExplanation,
) -> dict[str, Any]:
    """Return a compact machine-readable row for an abductive candidate."""
    return {
        "id": candidate.id,
        "source_stage": candidate.source_stage,
        "source_pattern_ids": list(candidate.source_pattern_ids),
        "explanation_text": candidate.explanation_text,
        "mechanism_summary": candidate.mechanism_summary,
        "rival_explanations": list(candidate.rival_explanations),
        "observable_implications": list(candidate.observable_implications),
        "evidence_gaps": list(candidate.evidence_gaps),
        "confidence": candidate.confidence,
        "status": candidate.status.value,
        "created_by": candidate.created_by.value,
        "created_at": candidate.created_at,
    }


def summarize_abductive_candidates(state: ProjectState) -> dict[str, Any]:
    """Summarize candidate explanation counts without validating them."""
    return {
        "total_candidates": len(state.abductive_explanations),
        "by_stage": dict(
            Counter(candidate.source_stage for candidate in state.abductive_explanations)
        ),
        "by_status": dict(
            Counter(candidate.status.value for candidate in state.abductive_explanations)
        ),
    }
