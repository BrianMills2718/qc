"""Helpers for the first-class analytic claim ledger (INV-9)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from qc_clean.schemas.domain import ProjectState


def summarize_claim_ledger(state: ProjectState) -> dict[str, Any]:
    """Return a compact deterministic summary of a project's claim ledger."""
    by_kind = Counter(claim.claim_kind.value for claim in state.claims)
    by_stage = Counter(claim.source_stage for claim in state.claims)
    by_adjudication = Counter(claim.adjudication_status.value for claim in state.claims)
    by_support = Counter(claim.support_status.value for claim in state.claims)

    return {
        "total_claims": len(state.claims),
        "by_kind": dict(sorted(by_kind.items())),
        "by_stage": dict(sorted(by_stage.items())),
        "by_adjudication_status": dict(sorted(by_adjudication.items())),
        "by_support_status": dict(sorted(by_support.items())),
        "unsupported_or_needing_anchor": (
            by_support.get("unsupported", 0) + by_support.get("needs_anchor", 0)
        ),
    }
