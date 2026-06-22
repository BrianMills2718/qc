"""Export theoretical-sampling candidate packages from project state."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from qc_clean.core.pipeline.theoretical_sampling import suggest_next_documents
from qc_clean.core.theoretical_sampling_preflight import (
    THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    TheoreticalSamplingCandidate,
    TheoreticalSamplingCandidatePackage,
)
from qc_clean.core.theoretical_sampling_protocol import (
    TheoreticalSamplingProtocolPackage,
    validate_theoretical_sampling_protocol_payload,
)
from qc_clean.schemas.domain import ProjectState


def export_theoretical_sampling_candidates(
    state: ProjectState,
    protocol_payload: TheoreticalSamplingProtocolPackage | dict[str, Any],
    *,
    candidate_names: list[str] | None = None,
    max_suggestions: int | None = None,
) -> dict[str, Any]:
    """Export loaded-document suggestions as a preflight-ready candidate package."""
    protocol = _coerce_protocol(protocol_payload)
    state_hash = _sha256_jsonable(state.model_dump(mode="json"))
    corpus_hash = _sha256_jsonable(state.corpus.model_dump(mode="json"))
    _require_protocol_matches_state(
        state,
        protocol,
        state_hash=state_hash,
        corpus_hash=corpus_hash,
    )
    _require_loaded_document_protocol(protocol)

    effective_max = max_suggestions if max_suggestions is not None else protocol.max_suggestions
    if effective_max < 1:
        raise ValueError("Theoretical sampling max_suggestions must be at least 1")
    if effective_max > protocol.max_suggestions:
        raise ValueError(
            "Theoretical sampling candidate export max_suggestions exceeds protocol "
            f"limit {protocol.max_suggestions}"
        )

    suggestions = suggest_next_documents(
        state,
        candidate_names=candidate_names,
        max_suggestions=effective_max,
    )
    if not suggestions:
        raise ValueError("Theoretical sampling candidate export found no loaded uncoded documents")

    target_gap_codes = set(protocol.target_gap_codes)
    candidates = [
        TheoreticalSamplingCandidate(
            candidate_id=f"loaded-{suggestion.doc_id}",
            source_kind="loaded_document",
            doc_id=suggestion.doc_id,
            doc_name=suggestion.doc_name,
            gap_codes=sorted(set(suggestion.gap_codes) & target_gap_codes),
            gap_types=list(protocol.target_gap_types),
            priority_score=suggestion.priority_score,
            rationale=suggestion.reason,
        )
        for suggestion in suggestions
    ]
    covered_gap_codes = {gap_code for candidate in candidates for gap_code in candidate.gap_codes}
    missing_gap_codes = sorted(target_gap_codes - covered_gap_codes)
    if missing_gap_codes:
        raise ValueError(
            "Theoretical sampling candidate export did not cover protocol target "
            "gap code(s): "
            + ", ".join(missing_gap_codes)
        )

    package = TheoreticalSamplingCandidatePackage(
        schema_version=1,
        package_type="qualitative_coding.theoretical_sampling_candidates",
        protocol_id=protocol.protocol_id,
        project_id=protocol.project_id,
        corpus_sha256=corpus_hash,
        project_state_sha256=state_hash,
        candidate_source=protocol.candidate_source,
        collection_mode=protocol.collection_mode,
        candidates=candidates,
        caution=THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    )
    return package.model_dump(mode="json")


def _coerce_protocol(
    payload: TheoreticalSamplingProtocolPackage | dict[str, Any],
) -> TheoreticalSamplingProtocolPackage:
    """Return a validated protocol package."""
    if isinstance(payload, TheoreticalSamplingProtocolPackage):
        return payload
    return validate_theoretical_sampling_protocol_payload(payload)


def _require_protocol_matches_state(
    state: ProjectState,
    protocol: TheoreticalSamplingProtocolPackage,
    *,
    state_hash: str,
    corpus_hash: str,
) -> None:
    """Fail loudly when a protocol was registered for a different state."""
    if protocol.project_id != state.id:
        raise ValueError(
            "Theoretical sampling protocol project_id "
            f"{protocol.project_id!r} does not match project {state.id!r}"
        )
    if protocol.corpus_sha256.lower() != corpus_hash.lower():
        raise ValueError(
            "Theoretical sampling protocol corpus_sha256 does not match current corpus hash"
        )
    if (
        protocol.project_state_sha256 is not None
        and protocol.project_state_sha256.lower() != state_hash.lower()
    ):
        raise ValueError(
            "Theoretical sampling protocol project_state_sha256 does not match "
            "current project state hash"
        )


def _require_loaded_document_protocol(protocol: TheoreticalSamplingProtocolPackage) -> None:
    """Fail for protocol modes this exporter cannot satisfy."""
    if protocol.candidate_source == "external_recruitment_pool":
        raise ValueError(
            "The loaded-document candidate exporter cannot satisfy "
            "external_recruitment_pool protocols"
        )
    if protocol.collection_mode == "collect_new_data":
        raise ValueError(
            "The loaded-document candidate exporter cannot satisfy collect_new_data protocols"
        )


def _sha256_jsonable(value: object) -> str:
    """Hash a JSON-serializable value using canonical compact JSON."""
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
