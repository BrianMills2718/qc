"""Helpers for the first-class analytic claim ledger (INV-9)."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping

from qc_clean.core.grounding import MatchStatus, resolve_against_docs
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAdjudicationStatus,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    ClaimSupportStatus,
    CodeApplication,
    CodeRelationship,
    CoreCategoryResult,
    DomainEntityRelationship,
    ProjectState,
    Provenance,
)

MAX_RELATIONSHIP_EVIDENCE_CHARS_FOR_ANCHORING = 280
MAX_RELATIONSHIP_EVIDENCE_TOKENS_FOR_ANCHORING = 48

NEGATIVE_CASE_TARGET_KINDS = {
    ClaimKind.CODE,
    ClaimKind.CROSS_CASE,
    ClaimKind.SYNTHESIS_FINDING,
    ClaimKind.GT_CATEGORY,
    ClaimKind.GT_PROPOSITION,
}

DISCONFIRMATION_EXCLUDED_KINDS = {
    ClaimKind.NEGATIVE_CASE,
    ClaimKind.NO_CLAIMS_EVENT,
}

DISCONFIRMATION_EXCLUDED_ADJUDICATIONS = {
    ClaimAdjudicationStatus.WITHDRAWN,
}


def claim_anchor_from_application(app: CodeApplication) -> ClaimAnchor | None:
    """Build a claim anchor from an anchored code application, if possible."""
    if app.start_char is None or app.end_char is None or app.quote_hash is None:
        return None
    return ClaimAnchor(
        doc_id=app.doc_id,
        start_char=app.start_char,
        end_char=app.end_char,
        quote_text=app.quote_text,
        quote_hash=app.quote_hash,
        code_application_id=app.id,
    )


def claims_for_codes(
    state: ProjectState,
    source_stage: str = "thematic_coding",
) -> list[AnalyticClaim]:
    """Create one claim for each code in the active codebook."""
    claims: list[AnalyticClaim] = []
    for code in state.codebook.codes:
        anchors = _anchors_for_code(state, code.id)
        description = code.description or code.definition or "analytic category"
        claims.append(AnalyticClaim(
            claim_kind=ClaimKind.CODE,
            source_stage=source_stage,
            claim_text=f"Code '{code.name}' represents {description}",
            scope=ClaimScope(code_ids=[code.id]),
            origin_object_type="code",
            origin_object_id=code.id,
            supporting_anchors=anchors,
            support_status=_support_status(anchors),
            created_by=code.provenance,
        ))
    return claims


def claims_for_code_applications(
    state: ProjectState,
    source_stage: str = "thematic_coding",
) -> list[AnalyticClaim]:
    """Create one claim for each code application."""
    code_names = {code.id: code.name for code in state.codebook.codes}
    claims: list[AnalyticClaim] = []
    for app in state.code_applications:
        anchor = claim_anchor_from_application(app)
        anchors = [anchor] if anchor else []
        code_name = code_names.get(app.code_id, app.code_id)
        claims.append(AnalyticClaim(
            claim_kind=ClaimKind.CODE_APPLICATION,
            source_stage=source_stage,
            claim_text=f"Passage '{app.quote_text}' is coded as '{code_name}'.",
            scope=ClaimScope(
                doc_ids=[app.doc_id],
                code_ids=[app.code_id],
                application_ids=[app.id],
            ),
            origin_object_type="code_application",
            origin_object_id=app.id,
            supporting_anchors=anchors,
            support_status=_support_status(anchors),
            created_by=app.applied_by,
        ))
    return claims


def claims_for_perspectives(
    state: ProjectState,
    source_stage: str = "perspective",
) -> list[AnalyticClaim]:
    """Create claims from participant perspective analysis."""
    if state.perspective_analysis is None:
        return []

    claims: list[AnalyticClaim] = []
    for participant in state.perspective_analysis.participants:
        text = participant.perspective_summary or f"Perspective identified for {participant.name}."
        scope = ClaimScope(
            participant_names=[participant.name],
            code_ids=list(participant.codes_emphasized),
            doc_ids=[participant.doc_id] if participant.doc_id else [],
        )
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.PERSPECTIVE,
            source_stage=source_stage,
            text=text,
            scope=scope,
            origin_type="participant_perspective",
            origin_id=participant.name,
            supporting_anchors=_anchors_for_scope(state, scope),
        ))
        for idx, statement in enumerate(participant.position_statements):
            claims.append(_needs_anchor_claim(
                kind=ClaimKind.PERSPECTIVE,
                source_stage=source_stage,
                text=f"{participant.name} position: {statement}",
                scope=scope,
                origin_type="participant_position",
                origin_id=f"{participant.name}:position:{idx}",
                supporting_anchors=_anchors_for_scope(state, scope),
            ))

    for i, theme in enumerate(state.perspective_analysis.consensus_themes):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.PERSPECTIVE,
            source_stage=source_stage,
            text=f"Perspective consensus theme: {theme}",
            scope=ClaimScope(corpus_level=True),
            origin_type="perspective_consensus",
            origin_id=f"consensus:{i}",
        ))

    for i, viewpoint in enumerate(state.perspective_analysis.divergent_viewpoints):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.PERSPECTIVE,
            source_stage=source_stage,
            text=f"Divergent perspective: {viewpoint}",
            scope=ClaimScope(corpus_level=True),
            origin_type="perspective_divergence",
            origin_id=f"divergent:{i}",
        ))

    return claims


def claims_for_relationships(
    state: ProjectState,
    source_stage: str = "relationship",
) -> list[AnalyticClaim]:
    """Create claims from entity and code relationships."""
    entity_names = {entity.id: entity.name for entity in state.entities}
    code_names = {code.id: code.name for code in state.codebook.codes}
    claims: list[AnalyticClaim] = []

    for rel in state.entity_relationships:
        scope = ClaimScope(
            entity_ids=[rel.entity_1_id, rel.entity_2_id],
            relationship_ids=[rel.id],
        )
        claims.append(_relationship_claim(
            rel,
            source_stage,
            entity_names.get(rel.entity_1_id, rel.entity_1_id),
            entity_names.get(rel.entity_2_id, rel.entity_2_id),
            scope,
            "domain_entity_relationship",
            supporting_anchors=_anchors_for_evidence(
                state,
                rel.supporting_evidence,
                allow_fuzzy=False,
            ),
        ))

    for rel in state.code_relationships:
        scope = ClaimScope(
            code_ids=[rel.source_code_id, rel.target_code_id],
            relationship_ids=[rel.id],
        )
        scoped_anchors = _anchors_for_scope(state, scope)
        evidence_anchors = _anchors_for_evidence(state, rel.evidence, allow_fuzzy=False)
        claims.append(_relationship_claim(
            rel,
            source_stage,
            code_names.get(rel.source_code_id, rel.source_code_id),
            code_names.get(rel.target_code_id, rel.target_code_id),
            scope,
            "code_relationship",
            supporting_anchors=_merge_scoped_and_evidence_anchors(
                scoped_anchors,
                evidence_anchors,
            ),
        ))

    return claims


def claims_for_synthesis(
    state: ProjectState,
    source_stage: str = "synthesis",
) -> list[AnalyticClaim]:
    """Create claims from synthesis findings, patterns, recommendations, confidence."""
    if state.synthesis is None:
        return []

    claims: list[AnalyticClaim] = []
    for i, finding in enumerate(state.synthesis.key_findings):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage=source_stage,
            text=finding,
            scope=ClaimScope(corpus_level=True),
            origin_type="synthesis_key_finding",
            origin_id=f"finding:{i}",
        ))

    for i, pattern in enumerate(state.synthesis.cross_cutting_patterns):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage=source_stage,
            text=f"Cross-cutting pattern: {pattern}",
            scope=ClaimScope(corpus_level=True),
            origin_type="synthesis_pattern",
            origin_id=f"pattern:{i}",
        ))

    for i, rec in enumerate(state.synthesis.recommendations):
        scope = ClaimScope(corpus_level=True, code_ids=list(rec.supporting_themes))
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage=source_stage,
            text=f"Recommendation: {rec.title}. {rec.description}".strip(),
            scope=scope,
            origin_type="synthesis_recommendation",
            origin_id=f"recommendation:{i}",
            supporting_anchors=_anchors_for_scope(state, scope),
        ))

    for theme, confidence in sorted(state.synthesis.confidence_assessment.items()):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.SYNTHESIS_FINDING,
            source_stage=source_stage,
            text=f"Confidence assessment for {theme}: {confidence}",
            scope=ClaimScope(corpus_level=True),
            origin_type="synthesis_confidence",
            origin_id=f"confidence:{theme}",
        ))

    return claims


def claims_for_cross_interview(
    state: ProjectState,
    results: Any,
    source_stage: str = "cross_interview",
) -> list[AnalyticClaim]:
    """Create claims from a CrossInterviewResult."""
    claims: list[AnalyticClaim] = []

    for item in results.consensus_themes:
        code_id = item["code_id"]
        doc_ids = list(results.code_doc_matrix.get(code_id, []))
        anchors = _anchors_for_code(state, code_id)
        claims.append(AnalyticClaim(
            claim_kind=ClaimKind.CROSS_CASE,
            source_stage=source_stage,
            claim_text=(
                f"Code '{item['code_name']}' is present in "
                f"{item['doc_count']}/{item['total_docs']} documents."
            ),
            scope=ClaimScope(doc_ids=doc_ids, code_ids=[code_id], corpus_level=True),
            origin_object_type="cross_interview_consensus",
            origin_object_id=f"consensus:{code_id}",
            supporting_anchors=anchors,
            support_status=_support_status(anchors),
            created_by=Provenance.SYSTEM,
        ))

    for item in results.divergent_themes:
        code_id = item["code_id"]
        doc_ids = list(results.code_doc_matrix.get(code_id, []))
        anchors = _anchors_for_code(state, code_id)
        claims.append(AnalyticClaim(
            claim_kind=ClaimKind.CROSS_CASE,
            source_stage=source_stage,
            claim_text=(
                f"Code '{item['code_name']}' is divergent: present in "
                f"{item['doc_count']}/{item['total_docs']} documents."
            ),
            scope=ClaimScope(doc_ids=doc_ids, code_ids=[code_id], corpus_level=True),
            origin_object_type="cross_interview_divergent",
            origin_object_id=f"divergent:{code_id}",
            supporting_anchors=anchors,
            support_status=_support_status(anchors),
            created_by=Provenance.SYSTEM,
        ))

    for i, item in enumerate(results.co_occurrences):
        claims.append(_needs_anchor_claim(
            kind=ClaimKind.CROSS_CASE,
            source_stage=source_stage,
            text=(
                f"Codes '{item['code_1']}' and '{item['code_2']}' co-occur in "
                f"{item['co_occurrence_count']} documents."
            ),
            scope=ClaimScope(corpus_level=True),
            origin_type="cross_interview_co_occurrence",
            origin_id=f"co_occurrence:{i}",
            created_by=Provenance.SYSTEM,
        ))

    return claims


def claims_for_gt_categories(
    state: ProjectState,
    source_stage: str = "gt_selective_coding",
) -> list[AnalyticClaim]:
    """Create claims from grounded-theory core categories."""
    claims: list[AnalyticClaim] = []
    for category in state.core_categories:
        claims.append(_gt_category_claim(
            category,
            source_stage,
            supporting_anchors=_anchors_for_scope(
                state,
                ClaimScope(code_ids=list(category.related_categories)),
            ),
        ))
    return claims


def claims_for_gt_theory(
    state: ProjectState,
    source_stage: str = "gt_theory_integration",
) -> list[AnalyticClaim]:
    """Create claims from a grounded-theory theoretical model."""
    if state.theoretical_model is None:
        return []

    claims: list[AnalyticClaim] = []
    tm = state.theoretical_model
    for i, proposition in enumerate(tm.propositions):
        claims.append(_gt_proposition_claim(
            text=proposition,
            source_stage=source_stage,
            origin_id=f"proposition:{i}",
        ))
    for i, condition in enumerate(tm.scope_conditions):
        claims.append(_gt_proposition_claim(
            text=f"Scope condition: {condition}",
            source_stage=source_stage,
            origin_id=f"scope_condition:{i}",
        ))
    for i, implication in enumerate(tm.implications):
        claims.append(_gt_proposition_claim(
            text=f"Implication: {implication}",
            source_stage=source_stage,
            origin_id=f"implication:{i}",
        ))
    return claims


def claims_for_negative_cases(
    state: ProjectState,
    negative_cases: Iterable[Any],
    source_stage: str = "negative_case_analysis",
    *,
    candidate_anchors: Mapping[str, ClaimAnchor] | None = None,
) -> list[AnalyticClaim]:
    """Create claims from negative-case objects and resolve contrary anchors."""
    claims: list[AnalyticClaim] = []
    for i, negative_case in enumerate(negative_cases):
        code_id = _code_id_by_name(state, negative_case.code_name)
        anchor = _anchor_for_negative_case(state, negative_case, candidate_anchors)
        contrary_anchors = [anchor] if anchor else []
        target_claim_ids = _claim_ids_for_negative_case_target(
            state,
            negative_case,
            code_id,
            source_stage,
        )
        claims.append(AnalyticClaim(
            claim_kind=ClaimKind.NEGATIVE_CASE,
            source_stage=source_stage,
            claim_text=(
                f"Negative case for {negative_case.code_name}: "
                f"{negative_case.explanation} Implication: {negative_case.implication}"
            ),
            scope=ClaimScope(
                doc_ids=[anchor.doc_id] if anchor else [],
                code_ids=[code_id] if code_id else [],
                claim_ids=target_claim_ids,
            ),
            origin_object_type="negative_case",
            origin_object_id=f"negative_case:{i}:{negative_case.code_name}",
            contrary_anchors=contrary_anchors,
            support_status=_support_status(contrary_anchors),
        ))
    return claims


def no_claims_event(source_stage: str, reason: str) -> AnalyticClaim:
    """Create a system claim recording that a stage emitted no substantive claims."""
    return AnalyticClaim(
        claim_kind=ClaimKind.NO_CLAIMS_EVENT,
        source_stage=source_stage,
        claim_text=f"No analytic claims emitted: {reason}",
        scope=ClaimScope(corpus_level=True),
        origin_object_type="stage",
        origin_object_id=source_stage,
        support_status=ClaimSupportStatus.SUPPORTED,
        created_by=Provenance.SYSTEM,
    )


def replace_claims_for_stage(
    state: ProjectState,
    source_stage: str,
    claims: Iterable[AnalyticClaim],
    *,
    no_claims_reason: str = "",
) -> None:
    """Replace a stage's prior ledger entries with freshly-derived claims."""
    fresh_claims = list(claims)
    if not fresh_claims and no_claims_reason:
        fresh_claims = [no_claims_event(source_stage, no_claims_reason)]
    state.claims = [
        claim for claim in state.claims
        if claim.source_stage != source_stage
    ]
    state.claims.extend(fresh_claims)


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


def format_claim_scope_summary(scope: ClaimScope) -> str:
    """Return a compact, deterministic claim scope summary."""
    parts: list[str] = []
    if scope.corpus_level:
        parts.append("corpus")
    for label, values in (
        ("claims", scope.claim_ids),
        ("docs", scope.doc_ids),
        ("codes", scope.code_ids),
        ("segments", scope.segment_ids),
        ("apps", scope.application_ids),
        ("entities", scope.entity_ids),
        ("relationships", scope.relationship_ids),
        ("participants", scope.participant_names),
    ):
        if values:
            parts.append(f"{label}={','.join(values)}")
    return ";".join(parts) if parts else "unspecified"


def format_claim_anchor_details(
    anchors: Iterable[ClaimAnchor],
    *,
    limit: int = 5,
    quote_max_chars: int = 240,
) -> list[dict[str, Any]]:
    """Return bounded source-anchor details for review payloads."""
    safe_limit = max(0, limit)
    safe_quote_max = max(0, quote_max_chars)
    details: list[dict[str, Any]] = []
    for anchor in list(anchors)[:safe_limit]:
        quote_text = anchor.quote_text or ""
        if len(quote_text) > safe_quote_max:
            quote_text = quote_text[:safe_quote_max] + "..."
        details.append({
            "doc_id": anchor.doc_id,
            "start_char": anchor.start_char,
            "end_char": anchor.end_char,
            "quote_hash": anchor.quote_hash,
            "quote_text": quote_text,
            "segment_id": anchor.segment_id,
            "code_application_id": anchor.code_application_id,
        })
    return details


def disconfirmation_targets(
    state: ProjectState,
    limit: int | None = None,
) -> list[AnalyticClaim]:
    """Return live substantive claims that should face disconfirmation."""
    targets = [
        claim for claim in state.claims
        if claim.claim_kind not in DISCONFIRMATION_EXCLUDED_KINDS
        and claim.adjudication_status not in DISCONFIRMATION_EXCLUDED_ADJUDICATIONS
    ]
    if limit is None:
        return targets
    return targets[:max(0, limit)]


def summarize_disconfirmation_coverage(state: ProjectState) -> dict[str, Any]:
    """Return claim-ledger disconfirmation coverage from exact target IDs."""
    targets = disconfirmation_targets(state)
    target_ids = [claim.id for claim in targets]
    target_id_set = set(target_ids)

    challenged_set: set[str] = set()
    negative_case_claims = 0
    for claim in state.claims:
        if claim.claim_kind != ClaimKind.NEGATIVE_CASE:
            continue
        negative_case_claims += 1
        challenged_set.update(
            claim_id for claim_id in claim.scope.claim_ids
            if claim_id in target_id_set
        )

    challenged_ids = [claim_id for claim_id in target_ids if claim_id in challenged_set]
    unchallenged_ids = [claim_id for claim_id in target_ids if claim_id not in challenged_set]
    total = len(target_ids)
    challenged = len(challenged_ids)

    return {
        "total_targets": total,
        "challenged_targets": challenged,
        "unchallenged_targets": len(unchallenged_ids),
        "challenged_rate": challenged / total if total else 0.0,
        "challenged_claim_ids": challenged_ids,
        "unchallenged_claim_ids": unchallenged_ids,
        "negative_case_claims": negative_case_claims,
    }


def format_disconfirmation_targets(
    state: ProjectState,
    limit: int = 50,
) -> str:
    """Format bounded claim targets for a negative-case prompt."""
    bounded_limit = max(0, limit)
    targets = disconfirmation_targets(state)
    shown = targets[:bounded_limit]
    if not shown:
        return ""

    lines = [
        "CLAIM LEDGER TARGETS TO CHALLENGE "
        f"(showing {len(shown)}/{len(targets)} live substantive claims):"
    ]
    for claim in shown:
        text = claim.claim_text.replace("\n", " ").strip()
        if len(text) > 220:
            text = text[:217] + "..."
        lines.append(
            f"- claim_id={claim.id} kind={claim.claim_kind.value} "
            f"stage={claim.source_stage} support={claim.support_status.value} "
            f"adjudication={claim.adjudication_status.value} "
            f"scope={_format_scope_summary(claim.scope)} text={text}"
        )
    if len(targets) > bounded_limit:
        lines.append(f"... {len(targets) - bounded_limit} additional claims omitted by limit.")
    return "\n".join(lines)


def _anchors_for_code(state: ProjectState, code_id: str) -> list[ClaimAnchor]:
    """Return all anchored application spans for a code."""
    anchors: list[ClaimAnchor] = []
    for app in state.code_applications:
        if app.code_id != code_id:
            continue
        anchor = claim_anchor_from_application(app)
        if anchor is not None:
            anchors.append(anchor)
    return anchors


def _anchors_for_scope(state: ProjectState, scope: ClaimScope) -> list[ClaimAnchor]:
    """Return unique application anchors for code/application IDs in a claim scope."""
    anchors: list[ClaimAnchor] = []
    seen: set[tuple[str, int | None, int | None, str | None, str | None]] = set()

    def add(anchor: ClaimAnchor | None) -> None:
        if anchor is None:
            return
        key = (
            anchor.doc_id,
            anchor.start_char,
            anchor.end_char,
            anchor.quote_hash,
            anchor.code_application_id,
        )
        if key in seen:
            return
        seen.add(key)
        anchors.append(anchor)

    for code_id in scope.code_ids:
        for anchor in _anchors_for_code(state, code_id):
            add(anchor)

    application_ids = set(scope.application_ids)
    if application_ids:
        for app in state.code_applications:
            if app.id in application_ids:
                add(claim_anchor_from_application(app))

    return anchors


def _anchors_for_evidence(
    state: ProjectState,
    evidence_items: Iterable[str],
    *,
    allow_fuzzy: bool = True,
) -> list[ClaimAnchor]:
    """Resolve unique evidence strings into exact source anchors."""
    anchors: list[ClaimAnchor] = []
    seen: set[tuple[str, int | None, int | None]] = set()
    for evidence in evidence_items:
        if not _should_attempt_evidence_anchor(evidence):
            continue
        anchor = _anchor_from_quote(state, evidence, allow_fuzzy=allow_fuzzy)
        if anchor is None:
            continue
        key = _anchor_span_key(anchor)
        if key in seen:
            continue
        seen.add(key)
        anchors.append(anchor)
    return anchors


def _should_attempt_evidence_anchor(evidence: str) -> bool:
    """Return whether an evidence string is short enough for quote anchoring.

    Relationship evidence often contains paraphrases or multi-sentence summaries
    rather than direct quotes. Long fuzzy grounding attempts on those strings are
    expensive and not reliable enough to justify the cost.
    """
    normalized = evidence.strip()
    if not normalized:
        return False
    if len(normalized) > MAX_RELATIONSHIP_EVIDENCE_CHARS_FOR_ANCHORING:
        return False
    if len(normalized.split()) > MAX_RELATIONSHIP_EVIDENCE_TOKENS_FOR_ANCHORING:
        return False
    return True


def _merge_scoped_and_evidence_anchors(
    scoped_anchors: Iterable[ClaimAnchor],
    evidence_anchors: Iterable[ClaimAnchor],
) -> list[ClaimAnchor]:
    """Append evidence anchors unless they duplicate an existing scoped span."""
    anchors = list(scoped_anchors)
    seen_evidence_spans = {_anchor_span_key(anchor) for anchor in anchors}
    for anchor in evidence_anchors:
        key = _anchor_span_key(anchor)
        if key in seen_evidence_spans:
            continue
        seen_evidence_spans.add(key)
        anchors.append(anchor)
    return anchors


def _anchor_span_key(anchor: ClaimAnchor) -> tuple[str, int | None, int | None]:
    """Return the source-span identity for duplicate relationship evidence."""
    return (anchor.doc_id, anchor.start_char, anchor.end_char)


def _support_status(anchors: list[ClaimAnchor]) -> ClaimSupportStatus:
    """Return supported when at least one source anchor exists."""
    return ClaimSupportStatus.SUPPORTED if anchors else ClaimSupportStatus.NEEDS_ANCHOR


def _format_scope_summary(scope: ClaimScope) -> str:
    """Return a compact, deterministic claim scope summary."""
    return format_claim_scope_summary(scope)


def _needs_anchor_claim(
    *,
    kind: ClaimKind,
    source_stage: str,
    text: str,
    scope: ClaimScope,
    origin_type: str,
    origin_id: str,
    created_by: Provenance = Provenance.LLM,
    supporting_anchors: Iterable[ClaimAnchor] = (),
) -> AnalyticClaim:
    """Create a claim with explicit anchors or a visible anchor gap."""
    anchors = list(supporting_anchors)
    return AnalyticClaim(
        claim_kind=kind,
        source_stage=source_stage,
        claim_text=text,
        scope=scope,
        origin_object_type=origin_type,
        origin_object_id=origin_id,
        supporting_anchors=anchors,
        support_status=_support_status(anchors),
        created_by=created_by,
    )


def _relationship_claim(
    rel: DomainEntityRelationship | CodeRelationship,
    source_stage: str,
    source_name: str,
    target_name: str,
    scope: ClaimScope,
    origin_type: str,
    supporting_anchors: Iterable[ClaimAnchor] = (),
) -> AnalyticClaim:
    """Create one relationship claim with any available scoped anchors."""
    return _needs_anchor_claim(
        kind=ClaimKind.RELATIONSHIP,
        source_stage=source_stage,
        text=f"{source_name} {rel.relationship_type} {target_name}.",
        scope=scope,
        origin_type=origin_type,
        origin_id=rel.id,
        supporting_anchors=supporting_anchors,
    )


def _gt_category_claim(
    category: CoreCategoryResult,
    source_stage: str,
    supporting_anchors: Iterable[ClaimAnchor] = (),
) -> AnalyticClaim:
    """Create one grounded-theory category claim with any scoped anchors."""
    text = category.definition or category.central_phenomenon or category.category_name
    return _needs_anchor_claim(
        kind=ClaimKind.GT_CATEGORY,
        source_stage=source_stage,
        text=f"Core category '{category.category_name}': {text}",
        scope=ClaimScope(code_ids=list(category.related_categories)),
        origin_type="gt_core_category",
        origin_id=category.category_name,
        supporting_anchors=supporting_anchors,
    )


def _gt_proposition_claim(
    *,
    text: str,
    source_stage: str,
    origin_id: str,
) -> AnalyticClaim:
    """Create one unanchored grounded-theory proposition-like claim."""
    return _needs_anchor_claim(
        kind=ClaimKind.GT_PROPOSITION,
        source_stage=source_stage,
        text=text,
        scope=ClaimScope(corpus_level=True),
        origin_type="gt_theoretical_model",
        origin_id=origin_id,
    )


def _code_id_by_name(state: ProjectState, name: str) -> str | None:
    """Resolve a code name to its ID."""
    for code in state.codebook.codes:
        if code.name == name:
            return code.id
    return None


def _claim_ids_for_code_target(
    state: ProjectState,
    code_id: str | None,
    source_stage: str,
) -> list[str]:
    """Return existing high-level claim IDs challenged by a negative case."""
    if not code_id:
        return []

    target_ids: list[str] = []
    for claim in state.claims:
        if claim.source_stage == source_stage or claim.claim_kind == ClaimKind.NEGATIVE_CASE:
            continue
        if claim.claim_kind not in NEGATIVE_CASE_TARGET_KINDS:
            continue
        if code_id in claim.scope.code_ids:
            target_ids.append(claim.id)
    return target_ids


def _claim_ids_for_negative_case_target(
    state: ProjectState,
    negative_case: Any,
    code_id: str | None,
    source_stage: str,
) -> list[str]:
    """Resolve exact or fallback challenged claim IDs for a negative case."""
    explicit_target = getattr(negative_case, "target_claim_id", None)
    if explicit_target:
        target_ids = {claim.id for claim in disconfirmation_targets(state)}
        if explicit_target not in target_ids:
            raise ValueError(
                f"Negative case target_claim_id '{explicit_target}' is not a live disconfirmation target"
            )
        return [explicit_target]
    return _claim_ids_for_code_target(state, code_id, source_stage)


def _anchor_for_negative_case(
    state: ProjectState,
    negative_case: Any,
    candidate_anchors: Mapping[str, ClaimAnchor] | None,
) -> ClaimAnchor | None:
    """Resolve a negative-case anchor from candidate ID or evidence quote."""
    candidate_id = getattr(negative_case, "candidate_id", None)
    if candidate_id:
        if candidate_anchors is None or candidate_id not in candidate_anchors:
            raise ValueError(
                f"Negative case candidate_id '{candidate_id}' is not a retrieved candidate"
            )
        return candidate_anchors[candidate_id]
    return _anchor_from_quote(state, negative_case.disconfirming_evidence)


def _anchor_from_quote(
    state: ProjectState,
    quote: str,
    *,
    allow_fuzzy: bool = True,
) -> ClaimAnchor | None:
    """Resolve a quote across project documents into an exact claim anchor."""
    match = resolve_against_docs(quote, state.corpus.documents, allow_fuzzy=allow_fuzzy)
    if match.status is not MatchStatus.UNIQUE or match.doc_id is None:
        return None
    return ClaimAnchor(
        doc_id=match.doc_id,
        start_char=match.start_char,
        end_char=match.end_char,
        quote_text=quote,
        quote_hash=match.quote_hash,
    )
