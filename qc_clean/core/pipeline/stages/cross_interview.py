"""
Cross-interview analysis stage.

Only runs when the corpus contains more than one document.
Identifies patterns across documents using the codebook and code applications.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Dict, List

from qc_clean.core.claims import (
    claim_anchor_from_application,
    claim_relationships_for_cross_interview,
    claims_for_cross_interview,
    replace_claim_relationships_for_stage,
    replace_claims_for_stage,
)
from qc_clean.schemas.domain import (
    AnalysisMemo,
    CausalInterpretationStatus,
    CrossInterviewResult,
    ObservedPattern,
    ObservedPatternKind,
    ProjectState,
    Provenance,
)
from ..pipeline_engine import PipelineContext, PipelineStage

logger = logging.getLogger(__name__)


class CrossInterviewStage(PipelineStage):

    def name(self) -> str:
        return "cross_interview"

    def can_execute(self, state: ProjectState) -> bool:
        return state.corpus.num_documents > 1

    async def execute(self, state: ProjectState, ctx: PipelineContext) -> ProjectState:
        """Run cross-interview analysis using in-memory ProjectState data."""
        logger.info(
            "Starting cross_interview: docs=%d, codes=%d, applications=%d",
            state.corpus.num_documents, len(state.codebook.codes),
            len(state.code_applications),
        )
        results = analyze_cross_interview_patterns(state)

        # Store results as an analytical memo
        memo = AnalysisMemo(
            memo_type="cross_case",
            title="Cross-Interview Pattern Analysis",
            content=_format_cross_results(results),
            code_refs=list(results.shared_codes.keys()),
            doc_refs=[d.id for d in state.corpus.documents],
            created_by=Provenance.SYSTEM,
        )
        state.memos.append(memo)
        state.observed_patterns = [
            pattern for pattern in state.observed_patterns
            if pattern.source_stage != self.name()
        ] + observed_patterns_for_cross_interview(state, results, self.name())
        replace_claims_for_stage(
            state,
            self.name(),
            claims_for_cross_interview(state, results, self.name()),
            no_claims_reason="cross-interview analysis produced no consensus, divergence, or co-occurrence claims",
        )
        replace_claim_relationships_for_stage(
            state,
            self.name(),
            claim_relationships_for_cross_interview(state, self.name()),
        )

        logger.info(
            "Cross-interview analysis: %d shared codes, %d consensus, %d divergent",
            len(results.shared_codes),
            len(results.consensus_themes),
            len(results.divergent_themes),
        )
        return state


# ---------------------------------------------------------------------------
# Pure-function cross-interview analysis (no Neo4j)
# ---------------------------------------------------------------------------

def analyze_cross_interview_patterns(state: ProjectState) -> CrossInterviewResult:
    """
    Analyze patterns across documents using codebook and applications.

    Returns a CrossInterviewResult with shared/unique codes, consensus/divergent
    themes, co-occurrences, and code-doc matrices.
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
    code_pair_docs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for doc_id, codes in doc_codes.items():
        sorted_codes = sorted(codes)
        for i, c1 in enumerate(sorted_codes):
            for c2 in sorted_codes[i + 1:]:
                code_pairs[(c1, c2)] += 1
                code_pair_docs[(c1, c2)].add(doc_id)

    top_co_occurrences = [
        {
            "code_1_id": pair[0],
            "code_2_id": pair[1],
            "code_1": _code_name(state, pair[0]),
            "code_2": _code_name(state, pair[1]),
            "co_occurrence_count": count,
            "doc_ids": sorted(code_pair_docs[pair]),
        }
        for pair, count in code_pairs.most_common(15)
        if count > 1
    ]

    participant_names = []
    perspective_consensus = []
    perspective_divergence = []
    if state.perspective_analysis is not None:
        participant_names = [
            participant.name
            for participant in state.perspective_analysis.participants
            if participant.name
        ]
        perspective_consensus = [
            {
                "summary": theme,
                "participant_names": participant_names,
                "participant_count": len(participant_names),
            }
            for theme in state.perspective_analysis.consensus_themes
            if theme
        ]
        perspective_divergence = [
            {
                "summary": viewpoint,
                "participant_names": participant_names,
                "participant_count": len(participant_names),
            }
            for viewpoint in state.perspective_analysis.divergent_viewpoints
            if viewpoint
        ]

    return CrossInterviewResult(
        shared_codes=shared_codes,
        unique_codes=unique_codes,
        consensus_themes=consensus_themes,
        divergent_themes=divergent_themes,
        co_occurrences=top_co_occurrences,
        perspective_consensus=perspective_consensus,
        perspective_divergence=perspective_divergence,
        code_doc_matrix={cid: list(dids) for cid, dids in code_docs.items()},
        doc_code_matrix={did: list(cids) for did, cids in doc_codes.items()},
    )


def _code_name(state: ProjectState, code_id: str) -> str:
    code = state.codebook.get_code(code_id)
    return code.name if code else code_id


def observed_patterns_for_cross_interview(
    state: ProjectState,
    results: CrossInterviewResult,
    source_stage: str = "cross_interview",
) -> list[ObservedPattern]:
    """Build first-class descriptive pattern records from cross-interview output."""
    patterns: list[ObservedPattern] = []
    apps_by_code: dict[str, list] = defaultdict(list)
    for app in state.code_applications:
        apps_by_code[app.code_id].append(app)

    for consensus in results.consensus_themes:
        code_id = consensus["code_id"]
        doc_ids = sorted(results.code_doc_matrix.get(code_id, []))
        apps = [
            app for app in apps_by_code.get(code_id, [])
            if app.doc_id in set(doc_ids)
        ]
        patterns.append(ObservedPattern(
            id=f"pattern:{source_stage}:consensus_code:{code_id}",
            source_stage=source_stage,
            pattern_kind=ObservedPatternKind.CONSENSUS_CODE,
            summary=(
                f"Code '{consensus['code_name']}' appears in "
                f"{consensus['doc_count']}/{consensus['total_docs']} documents."
            ),
            code_ids=[code_id],
            doc_ids=doc_ids,
            application_ids=[app.id for app in apps],
            support_anchors=[
                anchor for app in apps
                if (anchor := claim_anchor_from_application(app)) is not None
            ],
            strength=consensus.get("strength"),
            count=consensus["doc_count"],
            total=consensus["total_docs"],
            metadata={"denominator": "documents_with_code_applications"},
            causal_interpretation_status=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
            created_by=Provenance.SYSTEM,
        ))

    for divergent in results.divergent_themes:
        code_id = divergent["code_id"]
        doc_ids = sorted(results.code_doc_matrix.get(code_id, []))
        apps = [
            app for app in apps_by_code.get(code_id, [])
            if app.doc_id in set(doc_ids)
        ]
        patterns.append(ObservedPattern(
            id=f"pattern:{source_stage}:divergent_code:{code_id}",
            source_stage=source_stage,
            pattern_kind=ObservedPatternKind.DIVERGENT_CODE,
            summary=(
                f"Code '{divergent['code_name']}' appears in "
                f"{divergent['doc_count']}/{divergent['total_docs']} documents."
            ),
            code_ids=[code_id],
            doc_ids=doc_ids,
            application_ids=[app.id for app in apps],
            support_anchors=[
                anchor for app in apps
                if (anchor := claim_anchor_from_application(app)) is not None
            ],
            count=divergent["doc_count"],
            total=divergent["total_docs"],
            metadata={"denominator": "documents_with_code_applications"},
            causal_interpretation_status=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
            created_by=Provenance.SYSTEM,
        ))

    for co in results.co_occurrences:
        code_ids = [co["code_1_id"], co["code_2_id"]]
        doc_ids = sorted(co.get("doc_ids", []))
        apps = [
            app
            for code_id in code_ids
            for app in apps_by_code.get(code_id, [])
            if app.doc_id in set(doc_ids)
        ]
        patterns.append(ObservedPattern(
            id=f"pattern:{source_stage}:code_co_occurrence:{code_ids[0]}:{code_ids[1]}",
            source_stage=source_stage,
            pattern_kind=ObservedPatternKind.CODE_CO_OCCURRENCE,
            summary=(
                f"Codes '{co['code_1']}' and '{co['code_2']}' co-occur in "
                f"{co['co_occurrence_count']} documents."
            ),
            code_ids=code_ids,
            doc_ids=doc_ids,
            application_ids=[app.id for app in apps],
            support_anchors=[
                anchor for app in apps
                if (anchor := claim_anchor_from_application(app)) is not None
            ],
            count=co["co_occurrence_count"],
            total=state.corpus.num_documents,
            metadata={"denominator": "documents_with_both_codes"},
            causal_interpretation_status=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
            created_by=Provenance.SYSTEM,
        ))

    all_doc_ids = [doc.id for doc in state.corpus.documents]
    for idx, item in enumerate(results.perspective_consensus):
        patterns.append(ObservedPattern(
            id=f"pattern:{source_stage}:perspective_consensus:{idx}",
            source_stage=source_stage,
            pattern_kind=ObservedPatternKind.PERSPECTIVE_CONSENSUS,
            summary=f"Participants converge on the position: {item['summary']}",
            doc_ids=all_doc_ids,
            count=item.get("participant_count", 0),
            total=state.corpus.num_documents,
            metadata={
                "denominator": "participants_in_perspective_analysis",
                "participant_names": item.get("participant_names", []),
            },
            causal_interpretation_status=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
            created_by=Provenance.SYSTEM,
        ))

    for idx, item in enumerate(results.perspective_divergence):
        patterns.append(ObservedPattern(
            id=f"pattern:{source_stage}:perspective_divergence:{idx}",
            source_stage=source_stage,
            pattern_kind=ObservedPatternKind.PERSPECTIVE_DIVERGENCE,
            summary=f"Participants diverge on the position: {item['summary']}",
            doc_ids=all_doc_ids,
            count=item.get("participant_count", 0),
            total=state.corpus.num_documents,
            metadata={
                "denominator": "participants_in_perspective_analysis",
                "participant_names": item.get("participant_names", []),
            },
            causal_interpretation_status=CausalInterpretationStatus.DESCRIPTIVE_ONLY,
            created_by=Provenance.SYSTEM,
        ))

    return patterns


def _format_cross_results(results: CrossInterviewResult) -> str:
    """Format cross-interview results as readable text for a memo."""
    lines = ["## Cross-Interview Pattern Analysis\n"]

    if results.consensus_themes:
        lines.append("### Consensus Themes (shared across majority of interviews)")
        for ct in results.consensus_themes:
            lines.append(
                f"- **{ct['code_name']}**: present in {ct['doc_count']}/{ct['total_docs']} "
                f"documents (strength={ct['strength']:.2f})"
            )
        lines.append("")

    if results.divergent_themes:
        lines.append("### Divergent Themes (present in only some interviews)")
        for dt in results.divergent_themes:
            lines.append(
                f"- **{dt['code_name']}**: present in {dt['doc_count']}/{dt['total_docs']} documents"
            )
        lines.append("")

    if results.co_occurrences:
        lines.append("### Top Code Co-occurrences")
        for co in results.co_occurrences:
            lines.append(
                f"- {co['code_1']} + {co['code_2']}: co-occur in {co['co_occurrence_count']} documents"
            )
        lines.append("")

    if results.perspective_consensus:
        lines.append("### Perspective Consensus")
        for item in results.perspective_consensus:
            lines.append(f"- {item['summary']}")
        lines.append("")

    if results.perspective_divergence:
        lines.append("### Perspective Divergence")
        for item in results.perspective_divergence:
            lines.append(f"- {item['summary']}")
        lines.append("")

    return "\n".join(lines)
