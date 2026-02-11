"""
Cross-interview analysis stage.

Only runs when the corpus contains more than one document.
Identifies patterns across documents using the codebook and code applications.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Dict, List

from qc_clean.schemas.domain import (
    AnalysisMemo,
    ProjectState,
    Provenance,
)
from ..pipeline_engine import PipelineStage

logger = logging.getLogger(__name__)


class CrossInterviewStage(PipelineStage):

    def name(self) -> str:
        return "cross_interview"

    def can_execute(self, state: ProjectState) -> bool:
        return state.corpus.num_documents > 1

    async def execute(self, state: ProjectState, config: dict) -> ProjectState:
        """Run cross-interview analysis using in-memory ProjectState data."""
        results = analyze_cross_interview_patterns(state)

        # Store results as an analytical memo
        memo = AnalysisMemo(
            memo_type="cross_case",
            title="Cross-Interview Pattern Analysis",
            content=_format_cross_results(results),
            code_refs=list(results.get("shared_codes", {}).keys()),
            doc_refs=[d.id for d in state.corpus.documents],
            created_by=Provenance.SYSTEM,
        )
        state.memos.append(memo)

        logger.info(
            "Cross-interview analysis: %d shared codes, %d consensus, %d divergent",
            len(results.get("shared_codes", {})),
            len(results.get("consensus_themes", [])),
            len(results.get("divergent_themes", [])),
        )
        return state


# ---------------------------------------------------------------------------
# Pure-function cross-interview analysis (no Neo4j)
# ---------------------------------------------------------------------------

def analyze_cross_interview_patterns(state: ProjectState) -> Dict:
    """
    Analyze patterns across documents using codebook and applications.

    Returns a dict with:
    - shared_codes: codes appearing in >1 document
    - unique_codes: codes appearing in only 1 document
    - consensus_themes: codes with high overlap
    - divergent_themes: codes appearing in some docs but not others
    - code_doc_matrix: {code_id: [doc_ids]}
    - doc_code_matrix: {doc_id: [code_ids]}
    """
    # Build doc -> codes and code -> docs mappings
    doc_codes: Dict[str, set] = defaultdict(set)
    code_docs: Dict[str, set] = defaultdict(set)
    code_quotes: Dict[str, List[str]] = defaultdict(list)

    for app in state.code_applications:
        doc_codes[app.doc_id].add(app.code_id)
        code_docs[app.code_id].add(app.doc_id)
        code_quotes[app.code_id].append(app.quote_text)

    num_docs = state.corpus.num_documents
    doc_ids = [d.id for d in state.corpus.documents]

    # Shared vs unique codes
    shared_codes = {
        cid: list(dids) for cid, dids in code_docs.items() if len(dids) > 1
    }
    unique_codes = {
        cid: list(dids) for cid, dids in code_docs.items() if len(dids) == 1
    }

    # Consensus: codes in >60% of documents
    consensus_threshold = max(2, int(num_docs * 0.6))
    consensus_themes = [
        {
            "code_id": cid,
            "code_name": _code_name(state, cid),
            "doc_count": len(dids),
            "total_docs": num_docs,
            "strength": len(dids) / num_docs,
        }
        for cid, dids in code_docs.items()
        if len(dids) >= consensus_threshold
    ]

    # Divergent: codes in <40% of docs (but at least 1)
    divergent_themes = [
        {
            "code_id": cid,
            "code_name": _code_name(state, cid),
            "doc_count": len(dids),
            "total_docs": num_docs,
        }
        for cid, dids in code_docs.items()
        if 0 < len(dids) < max(2, int(num_docs * 0.4))
    ]

    # Co-occurrence: codes that appear together in the same documents
    code_pairs: Counter = Counter()
    for doc_id, codes in doc_codes.items():
        sorted_codes = sorted(codes)
        for i, c1 in enumerate(sorted_codes):
            for c2 in sorted_codes[i + 1:]:
                code_pairs[(c1, c2)] += 1

    top_co_occurrences = [
        {
            "code_1": _code_name(state, pair[0]),
            "code_2": _code_name(state, pair[1]),
            "co_occurrence_count": count,
        }
        for pair, count in code_pairs.most_common(15)
        if count > 1
    ]

    return {
        "shared_codes": shared_codes,
        "unique_codes": unique_codes,
        "consensus_themes": consensus_themes,
        "divergent_themes": divergent_themes,
        "co_occurrences": top_co_occurrences,
        "code_doc_matrix": {cid: list(dids) for cid, dids in code_docs.items()},
        "doc_code_matrix": {did: list(cids) for did, cids in doc_codes.items()},
    }


def _code_name(state: ProjectState, code_id: str) -> str:
    code = state.codebook.get_code(code_id)
    return code.name if code else code_id


def _format_cross_results(results: Dict) -> str:
    """Format cross-interview results as readable text for a memo."""
    lines = ["## Cross-Interview Pattern Analysis\n"]

    if results["consensus_themes"]:
        lines.append("### Consensus Themes (shared across majority of interviews)")
        for ct in results["consensus_themes"]:
            lines.append(
                f"- **{ct['code_name']}**: present in {ct['doc_count']}/{ct['total_docs']} "
                f"documents (strength={ct['strength']:.2f})"
            )
        lines.append("")

    if results["divergent_themes"]:
        lines.append("### Divergent Themes (present in only some interviews)")
        for dt in results["divergent_themes"]:
            lines.append(
                f"- **{dt['code_name']}**: present in {dt['doc_count']}/{dt['total_docs']} documents"
            )
        lines.append("")

    if results["co_occurrences"]:
        lines.append("### Top Code Co-occurrences")
        for co in results["co_occurrences"]:
            lines.append(
                f"- {co['code_1']} + {co['code_2']}: co-occur in {co['co_occurrence_count']} documents"
            )
        lines.append("")

    return "\n".join(lines)
