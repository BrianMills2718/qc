"""Build unlabeled adjudication sample packages for human/expert review."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAnchor,
    ClaimKind,
    CodeApplication,
    CodeRelationship,
    DomainEntityRelationship,
    ProjectState,
)


TargetType = Literal[
    "code_application",
    "claim",
    "negative_case",
    "code_relationship",
    "entity_relationship",
]

TARGET_TYPE_ORDER: tuple[TargetType, ...] = (
    "code_application",
    "claim",
    "negative_case",
    "code_relationship",
    "entity_relationship",
)


class AdjudicationSourceContext(BaseModel):
    """Source-text context included for one adjudication sample item."""

    doc_id: str = Field(description="Document ID containing the source span")
    doc_name: str = Field(description="Human-readable document name")
    start_char: int | None = Field(default=None, description="Start offset of the source span")
    end_char: int | None = Field(default=None, description="End offset of the source span")
    quote_text: str = Field(default="", description="Quoted source text for human inspection")
    quote_hash: str | None = Field(default=None, description="Hash of the anchored source span")
    segment_id: str | None = Field(default=None, description="Segment ID when available")
    code_application_id: str | None = Field(
        default=None,
        description="CodeApplication ID when the context originates from an application",
    )
    context_before: str = Field(default="", description="Source text before the quote")
    context_after: str = Field(default="", description="Source text after the quote")


class AdjudicationSampleItem(BaseModel):
    """One unlabeled target for human/expert adjudication."""

    item_id: str = Field(description="Stable sample item ID, namespaced by target type")
    target_type: TargetType = Field(description="Review target type represented by this sample")
    target_id: str = Field(description="Underlying project object ID")
    title: str = Field(description="Compact human-readable item title")
    prompt: str = Field(description="Question the adjudicator should answer")
    payload: dict[str, Any] = Field(description="Target-specific context and provenance")
    source_context: AdjudicationSourceContext | None = Field(
        default=None,
        description="Primary source context when a single span is available",
    )
    response_template: dict[str, Any] = Field(
        default_factory=lambda: {
            "validity": "",
            "rationale": "",
            "corrected_value": None,
            "adjudicator_id": "",
        },
        description="Empty response fields for the human/expert adjudicator",
    )


class AdjudicationSamplePackage(BaseModel):
    """Versioned unlabeled adjudication package."""

    schema_version: Literal[1] = Field(description="Adjudication sample package schema version")
    package_type: Literal["adjudication_sample"] = Field(
        description="Package kind; sample packages are unlabeled inputs"
    )
    created_at: str = Field(description="UTC package creation timestamp")
    project_id: str = Field(description="Project ID the package was exported from")
    project_name: str = Field(description="Project name the package was exported from")
    hash_algorithm: Literal["sha256"] = Field(description="Hash algorithm used for provenance")
    project_state_sha256: str = Field(description="SHA-256 of the exported ProjectState JSON")
    corpus_sha256: str = Field(description="SHA-256 of the corpus payload")
    corpus_scope: dict[str, Any] | None = Field(
        default=None,
        description="Optional ProjectState.corpus_scope serialized for boundary context",
    )
    sample_policy: dict[str, Any] = Field(description="Deterministic sample selection policy")
    item_counts: dict[str, dict[str, int]] = Field(
        description="Available and returned item counts by target type"
    )
    caution: str = Field(
        description="Caveat that this unlabeled package is not validity evidence"
    )
    items: list[AdjudicationSampleItem] = Field(description="Unlabeled sample items")


def build_adjudication_sample_package(
    state: ProjectState,
    *,
    limit_per_type: int = 20,
    context_chars: int = 120,
) -> AdjudicationSamplePackage:
    """Build a deterministic unlabeled adjudication package from project state."""
    safe_limit = max(0, limit_per_type)
    safe_context_chars = max(0, context_chars)
    docs_by_id = {doc.id: doc for doc in state.corpus.documents}
    codes_by_id = {code.id: code for code in state.codebook.codes}
    entities_by_id = {entity.id: entity for entity in state.entities}

    candidates: dict[TargetType, list[AdjudicationSampleItem]] = {
        "code_application": [
            _item_for_application(app, docs_by_id, codes_by_id, safe_context_chars)
            for app in sorted(state.code_applications, key=lambda item: item.id)
        ],
        "claim": [
            _item_for_claim(claim, docs_by_id, safe_context_chars, target_type="claim")
            for claim in sorted(
                (claim for claim in state.claims if claim.claim_kind != ClaimKind.NEGATIVE_CASE),
                key=lambda item: item.id,
            )
        ],
        "negative_case": [
            _item_for_claim(claim, docs_by_id, safe_context_chars, target_type="negative_case")
            for claim in sorted(
                (claim for claim in state.claims if claim.claim_kind == ClaimKind.NEGATIVE_CASE),
                key=lambda item: item.id,
            )
        ],
        "code_relationship": [
            _item_for_code_relationship(rel, codes_by_id)
            for rel in sorted(state.code_relationships, key=lambda item: item.id)
        ],
        "entity_relationship": [
            _item_for_entity_relationship(rel, entities_by_id)
            for rel in sorted(state.entity_relationships, key=lambda item: item.id)
        ],
    }

    items: list[AdjudicationSampleItem] = []
    available_counts: dict[str, int] = {}
    returned_counts: dict[str, int] = {}
    for target_type in TARGET_TYPE_ORDER:
        available = candidates[target_type]
        returned = available[:safe_limit]
        available_counts[target_type] = len(available)
        returned_counts[target_type] = len(returned)
        items.extend(returned)
    available_counts["total"] = sum(available_counts.values())
    returned_counts["total"] = len(items)

    return AdjudicationSamplePackage(
        schema_version=1,
        package_type="adjudication_sample",
        created_at=datetime.now(timezone.utc).isoformat(),
        project_id=state.id,
        project_name=state.name,
        hash_algorithm="sha256",
        project_state_sha256=_sha256_jsonable(state.model_dump(mode="json")),
        corpus_sha256=_sha256_jsonable(state.corpus.model_dump(mode="json")),
        corpus_scope=(
            state.corpus_scope.model_dump(mode="json") if state.corpus_scope is not None else None
        ),
        sample_policy={
            "type_order": list(TARGET_TYPE_ORDER),
            "ordering": "stable target_type order, then target_id ascending",
            "limit_per_type": safe_limit,
            "context_chars": safe_context_chars,
            "sampling": "deterministic_first_n_per_type",
        },
        item_counts={"available": available_counts, "returned": returned_counts},
        caution=(
            "This package is an unlabeled adjudication input. It is not expert "
            "evidence, validity evidence, or a benchmark result until labels are "
            "collected under a documented protocol and scored separately."
        ),
        items=items,
    )


def write_adjudication_sample_package(
    package: AdjudicationSamplePackage,
    output_file: str | Path,
) -> str:
    """Write an adjudication sample package to JSON and return the output path."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(package.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return str(path)


def _item_for_application(
    app: CodeApplication,
    docs_by_id: dict[str, Any],
    codes_by_id: dict[str, Any],
    context_chars: int,
) -> AdjudicationSampleItem:
    code = codes_by_id.get(app.code_id)
    code_name = code.name if code is not None else app.code_id
    source_context = _source_context_for_application(app, docs_by_id, context_chars)
    return AdjudicationSampleItem(
        item_id=f"code_application:{app.id}",
        target_type="code_application",
        target_id=app.id,
        title=f"Code application: {code_name}",
        prompt="Is this code application valid for the quoted source span?",
        source_context=source_context,
        payload={
            "application_id": app.id,
            "code_id": app.code_id,
            "code_name": code_name,
            "doc_id": app.doc_id,
            "speaker": app.speaker,
            "confidence": app.confidence,
            "applied_by": app.applied_by.value,
            "codebook_version": app.codebook_version,
        },
    )


def _item_for_claim(
    claim: AnalyticClaim,
    docs_by_id: dict[str, Any],
    context_chars: int,
    *,
    target_type: Literal["claim", "negative_case"],
) -> AdjudicationSampleItem:
    supporting_anchors = [
        _source_context_for_anchor(anchor, docs_by_id, context_chars)
        for anchor in claim.supporting_anchors
    ]
    contrary_anchors = [
        _source_context_for_anchor(anchor, docs_by_id, context_chars)
        for anchor in claim.contrary_anchors
    ]
    primary_context = (
        contrary_anchors[0]
        if target_type == "negative_case" and contrary_anchors
        else supporting_anchors[0] if supporting_anchors else None
    )
    prompt = (
        "Does this negative case validly challenge the scoped target claim?"
        if target_type == "negative_case"
        else "Is this analytic claim valid within its stated evidence and scope?"
    )
    return AdjudicationSampleItem(
        item_id=f"{target_type}:{claim.id}",
        target_type=target_type,
        target_id=claim.id,
        title=f"{target_type.replace('_', ' ').title()}: {claim.id}",
        prompt=prompt,
        source_context=primary_context,
        payload={
            "claim_id": claim.id,
            "claim_kind": claim.claim_kind.value,
            "source_stage": claim.source_stage,
            "claim_text": claim.claim_text,
            "scope": claim.scope.model_dump(mode="json"),
            "origin_object_type": claim.origin_object_type,
            "origin_object_id": claim.origin_object_id,
            "support_status": claim.support_status.value,
            "adjudication_status": claim.adjudication_status.value,
            "supporting_anchors": [
                context.model_dump(mode="json") for context in supporting_anchors
            ],
            "contrary_anchors": [
                context.model_dump(mode="json") for context in contrary_anchors
            ],
        },
    )


def _item_for_code_relationship(
    relationship: CodeRelationship,
    codes_by_id: dict[str, Any],
) -> AdjudicationSampleItem:
    source_code = codes_by_id.get(relationship.source_code_id)
    target_code = codes_by_id.get(relationship.target_code_id)
    source_name = source_code.name if source_code is not None else relationship.source_code_id
    target_name = target_code.name if target_code is not None else relationship.target_code_id
    return AdjudicationSampleItem(
        item_id=f"code_relationship:{relationship.id}",
        target_type="code_relationship",
        target_id=relationship.id,
        title=f"Code relationship: {source_name} -> {target_name}",
        prompt="Is this relationship between codes valid and adequately evidenced?",
        payload={
            "relationship_id": relationship.id,
            "source_code_id": relationship.source_code_id,
            "source_code_name": source_name,
            "target_code_id": relationship.target_code_id,
            "target_code_name": target_name,
            "relationship_type": relationship.relationship_type,
            "strength": relationship.strength,
            "evidence": list(relationship.evidence),
            "conditions": list(relationship.conditions),
            "consequences": list(relationship.consequences),
        },
    )


def _item_for_entity_relationship(
    relationship: DomainEntityRelationship,
    entities_by_id: dict[str, Any],
) -> AdjudicationSampleItem:
    entity_1 = entities_by_id.get(relationship.entity_1_id)
    entity_2 = entities_by_id.get(relationship.entity_2_id)
    entity_1_name = entity_1.name if entity_1 is not None else relationship.entity_1_id
    entity_2_name = entity_2.name if entity_2 is not None else relationship.entity_2_id
    return AdjudicationSampleItem(
        item_id=f"entity_relationship:{relationship.id}",
        target_type="entity_relationship",
        target_id=relationship.id,
        title=f"Entity relationship: {entity_1_name} -> {entity_2_name}",
        prompt="Is this relationship between entities valid and adequately evidenced?",
        payload={
            "relationship_id": relationship.id,
            "entity_1_id": relationship.entity_1_id,
            "entity_1_name": entity_1_name,
            "entity_2_id": relationship.entity_2_id,
            "entity_2_name": entity_2_name,
            "relationship_type": relationship.relationship_type,
            "strength": relationship.strength,
            "supporting_evidence": list(relationship.supporting_evidence),
        },
    )


def _source_context_for_application(
    app: CodeApplication,
    docs_by_id: dict[str, Any],
    context_chars: int,
) -> AdjudicationSourceContext:
    return _source_context(
        docs_by_id,
        doc_id=app.doc_id,
        start_char=app.start_char,
        end_char=app.end_char,
        quote_text=app.quote_text,
        quote_hash=app.quote_hash,
        segment_id=None,
        code_application_id=app.id,
        context_chars=context_chars,
    )


def _source_context_for_anchor(
    anchor: ClaimAnchor,
    docs_by_id: dict[str, Any],
    context_chars: int,
) -> AdjudicationSourceContext:
    return _source_context(
        docs_by_id,
        doc_id=anchor.doc_id,
        start_char=anchor.start_char,
        end_char=anchor.end_char,
        quote_text=anchor.quote_text,
        quote_hash=anchor.quote_hash,
        segment_id=anchor.segment_id,
        code_application_id=anchor.code_application_id,
        context_chars=context_chars,
    )


def _source_context(
    docs_by_id: dict[str, Any],
    *,
    doc_id: str,
    start_char: int | None,
    end_char: int | None,
    quote_text: str,
    quote_hash: str | None,
    segment_id: str | None,
    code_application_id: str | None,
    context_chars: int,
) -> AdjudicationSourceContext:
    doc = docs_by_id.get(doc_id)
    doc_name = doc.name if doc is not None else doc_id
    content = doc.content if doc is not None else ""
    context_before = ""
    context_after = ""
    if (
        content
        and start_char is not None
        and end_char is not None
        and 0 <= start_char <= end_char <= len(content)
    ):
        context_before = content[max(0, start_char - context_chars):start_char]
        context_after = content[end_char:end_char + context_chars]
        if not quote_text:
            quote_text = content[start_char:end_char]
    return AdjudicationSourceContext(
        doc_id=doc_id,
        doc_name=doc_name,
        start_char=start_char,
        end_char=end_char,
        quote_text=quote_text,
        quote_hash=quote_hash,
        segment_id=segment_id,
        code_application_id=code_application_id,
        context_before=context_before,
        context_after=context_after,
    )


def _sha256_jsonable(value: Any) -> str:
    """Return a deterministic SHA-256 hash for a JSON-serializable value."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
