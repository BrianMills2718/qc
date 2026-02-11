"""
Theoretical sampling: suggest which documents to code next
based on code coverage gaps.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List

from qc_clean.schemas.domain import ProjectState

logger = logging.getLogger(__name__)


def suggest_next_documents(
    state: ProjectState,
    candidate_names: List[str] | None = None,
    max_suggestions: int = 3,
) -> List[Dict]:
    """
    Suggest which documents should be analyzed next to maximize
    code coverage and address gaps.

    If *candidate_names* is provided, only those document names are
    considered.  Otherwise all un-coded documents in the corpus are
    candidates.

    Returns a list of dicts sorted by priority:
    - doc_id / doc_name
    - reason: why this document is suggested
    - gap_codes: codes not yet represented
    """
    coded_doc_ids = {a.doc_id for a in state.code_applications}
    uncoded = [
        d for d in state.corpus.documents
        if d.id not in coded_doc_ids
        and (candidate_names is None or d.name in candidate_names)
    ]

    if not uncoded:
        return []

    # Which codes have low coverage?
    code_doc_counts: Dict[str, int] = defaultdict(int)
    for app in state.code_applications:
        code_doc_counts[app.code_id] += 1

    all_code_ids = {c.id for c in state.codebook.codes}
    low_coverage_codes = {
        cid for cid in all_code_ids
        if code_doc_counts.get(cid, 0) <= 1
    }

    suggestions = []
    for doc in uncoded:
        # Simple heuristic: prioritize docs whose speakers or content
        # might cover gap codes.  Since we haven't coded them yet, we
        # use a naive score based on speaker diversity.
        score = len(doc.detected_speakers) + 1  # more speakers = richer data
        suggestions.append({
            "doc_id": doc.id,
            "doc_name": doc.name,
            "reason": "Uncoded document with potential to cover under-represented codes",
            "gap_codes": sorted(low_coverage_codes),
            "priority_score": score,
        })

    suggestions.sort(key=lambda s: s["priority_score"], reverse=True)
    return suggestions[:max_suggestions]
