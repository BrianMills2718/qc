"""Versioned QC-to-process-tracing handoff package contracts."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from qc_clean.schemas.domain import ClaimAnchor, ProjectState


HANDOFF_PACKAGE_TYPE = "qualitative_coding.process_tracing_handoff"
HANDOFF_CAVEATS = [
    "This package contains qualitative evidence objects for process-tracing review; it is not causal proof.",
    "Abductive candidates are provisional hypotheses unless reviewed and later tested by a process-tracing engine.",
    "No likelihood vectors, Bayesian updates, comparative support, methodological-validity evidence, or SOTA evidence are included.",
]
FORBIDDEN_PT_INFERENCE_FIELDS = frozenset({
    "likelihood_vector",
    "likelihood_vectors",
    "evidence_likelihoods",
    "bayesian_update",
    "bayesian_updates",
    "posterior",
    "final_posterior",
    "comparative_support",
    "hypothesis_posterior",
    "hypothesis_posteriors",
})


class ProcessTracingHandoffDocument(BaseModel):
    """Document metadata exported without full source text."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(description="QC document identifier")
    name: str = Field(description="Document display name")
    content_sha256: str = Field(description="SHA-256 hash of the document content")
    char_count: int = Field(description="Document character count")


class ProcessTracingHandoffAnchor(BaseModel):
    """One source-span anchor referenced by package objects."""

    model_config = ConfigDict(extra="forbid")

    anchor_id: str = Field(description="Package-local stable anchor identifier")
    source_object_type: str = Field(description="Object type that supplied this anchor")
    source_object_id: str = Field(description="Object ID that supplied this anchor")
    doc_id: str = Field(description="Document containing the anchored span")
    start_char: int | None = Field(default=None, description="Start offset in source document")
    end_char: int | None = Field(default=None, description="End offset in source document")
    quote_text: str = Field(default="", description="Evidence text for human inspection")
    quote_hash: str | None = Field(default=None, description="Hash of the anchored source span")
    segment_id: str | None = Field(default=None, description="Segment ID when available")
    code_application_id: str | None = Field(
        default=None,
        description="CodeApplication ID when anchor originates from a code application",
    )


class ProcessTracingHandoffObservedPattern(BaseModel):
    """Observed descriptive pattern row exported for later causal review."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="ObservedPattern ID")
    source_stage: str = Field(description="Pipeline stage that produced the pattern")
    pattern_kind: str = Field(description="Pattern kind")
    summary: str = Field(description="Pattern summary")
    code_ids: list[str] = Field(description="Related code IDs")
    doc_ids: list[str] = Field(description="Related document IDs")
    application_ids: list[str] = Field(description="Related code application IDs")
    count: int | None = Field(default=None, description="Pattern numerator when available")
    total: int | None = Field(default=None, description="Pattern denominator when available")
    causal_interpretation_status: str = Field(description="QC-side causal interpretation status")
    support_anchor_ids: list[str] = Field(description="Anchor IDs supporting this pattern")


class ProcessTracingHandoffAbductiveCandidate(BaseModel):
    """Provisional abductive candidate exported for process-tracing review."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="AbductiveCandidateExplanation ID")
    source_stage: str = Field(description="Pipeline stage that produced the candidate")
    source_pattern_ids: list[str] = Field(description="ObservedPattern IDs this candidate explains")
    explanation_text: str = Field(description="Plain-language provisional explanation")
    mechanism_summary: str = Field(description="Candidate mechanism summary")
    rival_explanations: list[str] = Field(description="Rival explanations")
    observable_implications: list[str] = Field(description="Observable implications")
    evidence_gaps: list[str] = Field(description="Evidence still needed before promotion")
    confidence: float | None = Field(default=None, description="Provisional QC confidence, not calibration evidence")
    status: str = Field(description="QC candidate review status")
    created_by: str = Field(description="Actor that produced the candidate")


class ProcessTracingHandoffClaim(BaseModel):
    """Analytic claim row exported as qualitative context."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="AnalyticClaim ID")
    claim_kind: str = Field(description="Claim kind")
    source_stage: str = Field(description="Pipeline stage that produced the claim")
    claim_text: str = Field(description="Claim text")
    support_status: str = Field(description="QC support/anchoring status")
    adjudication_status: str = Field(description="Human/agent adjudication status")
    origin_object_type: str = Field(description="Originating QC object type")
    origin_object_id: str = Field(description="Originating QC object ID")
    scope: dict[str, Any] = Field(description="Serialized claim scope")
    supporting_anchor_ids: list[str] = Field(description="Supporting anchor IDs")
    contrary_anchor_ids: list[str] = Field(description="Contrary anchor IDs")


class ProcessTracingHandoffProvenance(BaseModel):
    """Package provenance and source-state hashes."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(description="UTC ISO timestamp for package generation")
    project_state_sha256: str = Field(description="SHA-256 hash of the serialized ProjectState")
    producer: str = Field(description="Producer component name")


class ProcessTracingHandoffPackage(BaseModel):
    """Strict schema_version=1 QC handoff package for process-tracing consumers."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(1, description="Package schema version")
    package_type: Literal[HANDOFF_PACKAGE_TYPE] = Field(
        HANDOFF_PACKAGE_TYPE,
        description="Package type discriminator",
    )
    project_id: str = Field(description="QC project ID")
    project_name: str = Field(description="QC project name")
    corpus_scope: dict[str, Any] | None = Field(description="Serialized CorpusScope or null")
    documents: list[ProcessTracingHandoffDocument] = Field(description="Document metadata and hashes")
    observed_patterns: list[ProcessTracingHandoffObservedPattern] = Field(description="Observed descriptive patterns")
    abductive_candidates: list[ProcessTracingHandoffAbductiveCandidate] = Field(description="Provisional candidates")
    analytic_claims: list[ProcessTracingHandoffClaim] = Field(description="Analytic claims for context")
    anchors: list[ProcessTracingHandoffAnchor] = Field(description="Package-local source anchors")
    caveats: list[str] = Field(description="Claim-discipline caveats")
    provenance: ProcessTracingHandoffProvenance = Field(description="Package provenance")

    @model_validator(mode="after")
    def _validate_references(self) -> "ProcessTracingHandoffPackage":
        pattern_ids = {pattern.id for pattern in self.observed_patterns}
        doc_ids = {doc.doc_id for doc in self.documents}
        anchor_ids = {anchor.anchor_id for anchor in self.anchors}

        missing_pattern_refs = sorted({
            pattern_id
            for candidate in self.abductive_candidates
            for pattern_id in candidate.source_pattern_ids
            if pattern_id not in pattern_ids
        })
        if missing_pattern_refs:
            raise ValueError(
                "Abductive candidate source_pattern_ids not found in observed_patterns: "
                f"{missing_pattern_refs}"
            )

        missing_anchor_docs = sorted({
            anchor.doc_id for anchor in self.anchors if anchor.doc_id not in doc_ids
        })
        if missing_anchor_docs:
            raise ValueError(
                "Anchor doc_id values not found in documents: "
                f"{missing_anchor_docs}"
            )

        missing_pattern_anchors = sorted({
            anchor_id
            for pattern in self.observed_patterns
            for anchor_id in pattern.support_anchor_ids
            if anchor_id not in anchor_ids
        })
        missing_claim_anchors = sorted({
            anchor_id
            for claim in self.analytic_claims
            for anchor_id in [*claim.supporting_anchor_ids, *claim.contrary_anchor_ids]
            if anchor_id not in anchor_ids
        })
        missing_anchor_refs = sorted(set(missing_pattern_anchors + missing_claim_anchors))
        if missing_anchor_refs:
            raise ValueError(
                "Anchor IDs referenced by patterns/claims are missing from anchors: "
                f"{missing_anchor_refs}"
            )

        return self


def build_process_tracing_handoff_package(
    state: ProjectState,
) -> ProcessTracingHandoffPackage:
    """Build a strict handoff package from a QC project state."""
    anchors: list[ProcessTracingHandoffAnchor] = []
    pattern_anchor_ids: dict[str, list[str]] = {}
    claim_support_anchor_ids: dict[str, list[str]] = {}
    claim_contrary_anchor_ids: dict[str, list[str]] = {}

    for pattern in state.observed_patterns:
        pattern_anchor_ids[pattern.id] = _append_anchors(
            anchors,
            pattern.support_anchors,
            source_object_type="observed_pattern",
            source_object_id=pattern.id,
        )

    for claim in state.claims:
        claim_support_anchor_ids[claim.id] = _append_anchors(
            anchors,
            claim.supporting_anchors,
            source_object_type="analytic_claim:supporting",
            source_object_id=claim.id,
        )
        claim_contrary_anchor_ids[claim.id] = _append_anchors(
            anchors,
            claim.contrary_anchors,
            source_object_type="analytic_claim:contrary",
            source_object_id=claim.id,
        )

    package = ProcessTracingHandoffPackage(
        project_id=state.id,
        project_name=state.name,
        corpus_scope=(
            state.corpus_scope.model_dump(mode="json")
            if state.corpus_scope is not None
            else None
        ),
        documents=[
            ProcessTracingHandoffDocument(
                doc_id=document.id,
                name=document.name,
                content_sha256=_sha256_text(document.content),
                char_count=len(document.content),
            )
            for document in state.corpus.documents
        ],
        observed_patterns=[
            ProcessTracingHandoffObservedPattern(
                id=pattern.id,
                source_stage=pattern.source_stage,
                pattern_kind=pattern.pattern_kind.value,
                summary=pattern.summary,
                code_ids=list(pattern.code_ids),
                doc_ids=list(pattern.doc_ids),
                application_ids=list(pattern.application_ids),
                count=pattern.count,
                total=pattern.total,
                causal_interpretation_status=pattern.causal_interpretation_status.value,
                support_anchor_ids=pattern_anchor_ids.get(pattern.id, []),
            )
            for pattern in state.observed_patterns
        ],
        abductive_candidates=[
            ProcessTracingHandoffAbductiveCandidate(
                id=candidate.id,
                source_stage=candidate.source_stage,
                source_pattern_ids=list(candidate.source_pattern_ids),
                explanation_text=candidate.explanation_text,
                mechanism_summary=candidate.mechanism_summary,
                rival_explanations=list(candidate.rival_explanations),
                observable_implications=list(candidate.observable_implications),
                evidence_gaps=list(candidate.evidence_gaps),
                confidence=candidate.confidence,
                status=candidate.status.value,
                created_by=candidate.created_by.value,
            )
            for candidate in state.abductive_explanations
        ],
        analytic_claims=[
            ProcessTracingHandoffClaim(
                id=claim.id,
                claim_kind=claim.claim_kind.value,
                source_stage=claim.source_stage,
                claim_text=claim.claim_text,
                support_status=claim.support_status.value,
                adjudication_status=claim.adjudication_status.value,
                origin_object_type=claim.origin_object_type,
                origin_object_id=claim.origin_object_id,
                scope=claim.scope.model_dump(mode="json"),
                supporting_anchor_ids=claim_support_anchor_ids.get(claim.id, []),
                contrary_anchor_ids=claim_contrary_anchor_ids.get(claim.id, []),
            )
            for claim in state.claims
        ],
        anchors=anchors,
        caveats=list(HANDOFF_CAVEATS),
        provenance=ProcessTracingHandoffProvenance(
            generated_at=datetime.now(timezone.utc).isoformat(),
            project_state_sha256=_project_state_hash(state),
            producer="qualitative_coding.process_tracing_handoff",
        ),
    )
    return package


def write_process_tracing_handoff_package(
    state: ProjectState,
    output_path: Path | str,
) -> ProcessTracingHandoffPackage:
    """Write a handoff package JSON file and return the validated package."""
    package = build_process_tracing_handoff_package(state)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(package.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return package


def load_process_tracing_handoff_package(
    path: Path | str,
) -> ProcessTracingHandoffPackage:
    """Load and validate a handoff package JSON file."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_process_tracing_handoff_payload(payload)


def validate_process_tracing_handoff_payload(
    payload: Any,
) -> ProcessTracingHandoffPackage:
    """Validate a handoff package payload and reject PT inference fields."""
    _reject_forbidden_pt_fields(payload)
    try:
        return ProcessTracingHandoffPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid process-tracing handoff package: {exc}") from exc


def _append_anchors(
    output: list[ProcessTracingHandoffAnchor],
    anchors: Iterable[ClaimAnchor],
    *,
    source_object_type: str,
    source_object_id: str,
) -> list[str]:
    ids: list[str] = []
    for index, anchor in enumerate(anchors):
        anchor_id = f"anchor:{source_object_type}:{source_object_id}:{index}"
        output.append(
            ProcessTracingHandoffAnchor(
                anchor_id=anchor_id,
                source_object_type=source_object_type,
                source_object_id=source_object_id,
                doc_id=anchor.doc_id,
                start_char=anchor.start_char,
                end_char=anchor.end_char,
                quote_text=anchor.quote_text,
                quote_hash=anchor.quote_hash,
                segment_id=anchor.segment_id,
                code_application_id=anchor.code_application_id,
            )
        )
        ids.append(anchor_id)
    return ids


def _reject_forbidden_pt_fields(payload: Any, *, path: str = "$") -> None:
    """Reject process-tracing inference fields anywhere in the payload."""
    if isinstance(payload, dict):
        forbidden = sorted(set(payload) & FORBIDDEN_PT_INFERENCE_FIELDS)
        if forbidden:
            raise ValueError(
                f"Forbidden process-tracing inference fields at {path}: {forbidden}"
            )
        for key, value in payload.items():
            _reject_forbidden_pt_fields(value, path=f"{path}.{key}")
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            _reject_forbidden_pt_fields(value, path=f"{path}[{index}]")


def _project_state_hash(state: ProjectState) -> str:
    """Hash the serialized project state deterministically."""
    payload = json.dumps(state.model_dump(mode="json"), sort_keys=True)
    return _sha256_text(payload)


def _sha256_text(value: str) -> str:
    """Return the SHA-256 hex digest for text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
