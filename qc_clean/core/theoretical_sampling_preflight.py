"""Preflight theoretical-sampling candidates/results against protocols."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from qc_clean.core.theoretical_sampling_protocol import (
    TheoreticalSamplingGapType,
    TheoreticalSamplingProtocolPackage,
    validate_theoretical_sampling_protocol_payload,
)


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

THEORETICAL_SAMPLING_PREFLIGHT_CAUTION = (
    "Theoretical sampling preflight is process/provenance metadata only; it is "
    "not sampling adequacy evidence, not methodological saturation evidence, "
    "not full grounded-theory evidence, and not a SOTA claim."
)

CandidateSource = Literal["loaded_uncoded_documents", "external_recruitment_pool", "mixed"]
CollectionMode = Literal["select_existing_documents", "collect_new_data", "mixed"]
CandidateSourceKind = Literal["loaded_document", "external_case"]


class TheoreticalSamplingCandidate(BaseModel):
    """One candidate case/document for a theoretical-sampling protocol."""

    candidate_id: str = Field(description="Stable candidate identifier")
    source_kind: CandidateSourceKind = Field(description="Candidate source kind")
    doc_id: str | None = Field(
        default=None,
        description="Loaded document ID when source_kind is loaded_document",
    )
    doc_name: str | None = Field(
        default=None,
        description="Loaded document or external case display name",
    )
    gap_codes: list[str] = Field(description="Protocol target gap codes this candidate addresses")
    gap_types: list[TheoreticalSamplingGapType] = Field(
        description="Protocol target gap types this candidate addresses"
    )
    priority_score: float = Field(default=0.0, description="Candidate priority score")
    rationale: str = Field(default="", description="Why this candidate addresses the gaps")

    @model_validator(mode="after")
    def require_candidate_invariants(self) -> "TheoreticalSamplingCandidate":
        """Reject underspecified candidate records."""
        self.candidate_id = self.candidate_id.strip()
        if not self.candidate_id:
            raise ValueError("Theoretical sampling candidate_id must be non-empty")
        self.doc_id = self.doc_id.strip() if self.doc_id is not None else None
        self.doc_name = self.doc_name.strip() if self.doc_name is not None else None
        if self.source_kind == "loaded_document":
            if not self.doc_id:
                raise ValueError("loaded_document candidates require doc_id")
            if not self.doc_name:
                raise ValueError("loaded_document candidates require doc_name")
        if self.source_kind == "external_case" and not self.doc_name:
            raise ValueError("external_case candidates require doc_name")
        self.gap_codes = _normalize_unique_nonempty(
            self.gap_codes,
            label="candidate gap_code",
        )
        if not self.gap_codes:
            raise ValueError("Theoretical sampling candidate gap_codes are required")
        self.gap_types = _normalize_unique_nonempty(
            list(self.gap_types),
            label="candidate gap_type",
        )
        if not self.gap_types:
            raise ValueError("Theoretical sampling candidate gap_types are required")
        return self


class TheoreticalSamplingCandidatePackage(BaseModel):
    """Concrete candidate pool for a theoretical-sampling protocol."""

    schema_version: Literal[1] = Field(description="Candidate package schema version")
    package_type: Literal["qualitative_coding.theoretical_sampling_candidates"] = Field(
        description="Stable candidate package type"
    )
    protocol_id: str = Field(description="Protocol ID this candidate pool claims to follow")
    project_id: str = Field(description="Project ID this candidate pool applies to")
    corpus_sha256: str = Field(description="SHA-256 hash of the protocol corpus payload")
    project_state_sha256: str | None = Field(
        default=None,
        description="Optional ProjectState SHA-256 hash",
    )
    candidate_source: CandidateSource = Field(description="Candidate source policy")
    collection_mode: CollectionMode = Field(description="Candidate collection/selection mode")
    candidates: list[TheoreticalSamplingCandidate] = Field(
        description="Candidate cases/documents for this protocol"
    )
    caution: str = Field(description="Claim-discipline caveat for candidate consumers")

    @model_validator(mode="after")
    def require_candidate_package_invariants(self) -> "TheoreticalSamplingCandidatePackage":
        """Reject malformed candidate packages before cross-checking."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        if not self.protocol_id:
            raise ValueError("Theoretical sampling candidate protocol_id must be non-empty")
        if not self.project_id:
            raise ValueError("Theoretical sampling candidate project_id must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("Theoretical sampling candidate corpus_sha256 must be a SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError(
                "Theoretical sampling candidate project_state_sha256 must be a SHA-256"
            )
        if not self.candidates:
            raise ValueError("Theoretical sampling candidate package requires candidates")
        duplicate_ids = sorted(
            candidate_id
            for candidate_id in {candidate.candidate_id for candidate in self.candidates}
            if [candidate.candidate_id for candidate in self.candidates].count(candidate_id) > 1
        )
        if duplicate_ids:
            raise ValueError(
                "Duplicate theoretical sampling candidate_id(s): " + ", ".join(duplicate_ids)
            )
        if not self.caution.strip():
            raise ValueError("Theoretical sampling candidate caution must be non-empty")
        return self


class TheoreticalSamplingResultPackage(BaseModel):
    """Selected candidate/result record for a theoretical-sampling protocol."""

    schema_version: Literal[1] = Field(description="Result package schema version")
    package_type: Literal["qualitative_coding.theoretical_sampling_results"] = Field(
        description="Stable result package type"
    )
    protocol_id: str = Field(description="Protocol ID this result package claims to follow")
    project_id: str = Field(description="Project ID this result package applies to")
    corpus_sha256: str = Field(description="SHA-256 hash of the protocol corpus payload")
    project_state_sha256: str | None = Field(
        default=None,
        description="Optional ProjectState SHA-256 hash",
    )
    selected_candidate_ids: list[str] = Field(
        description="Candidate IDs selected or collected under this protocol"
    )
    addressed_gap_codes: list[str] = Field(
        description="Protocol target gap codes addressed by the selections"
    )
    addressed_gap_types: list[TheoreticalSamplingGapType] = Field(
        description="Protocol target gap types addressed by the selections"
    )
    stopped_by_rule: bool = Field(description="Whether the protocol stopping rule was met")
    success_criteria_met: list[str] = Field(
        description="Pre-registered success criteria marked as met"
    )
    caution: str = Field(description="Claim-discipline caveat for result consumers")

    @model_validator(mode="after")
    def require_result_package_invariants(self) -> "TheoreticalSamplingResultPackage":
        """Reject malformed result packages before cross-checking."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        if not self.protocol_id:
            raise ValueError("Theoretical sampling result protocol_id must be non-empty")
        if not self.project_id:
            raise ValueError("Theoretical sampling result project_id must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("Theoretical sampling result corpus_sha256 must be a SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError(
                "Theoretical sampling result project_state_sha256 must be a SHA-256"
            )
        self.selected_candidate_ids = _normalize_unique_nonempty(
            self.selected_candidate_ids,
            label="selected_candidate_id",
        )
        if not self.selected_candidate_ids:
            raise ValueError("Theoretical sampling result selected_candidate_ids are required")
        self.addressed_gap_codes = _normalize_unique_nonempty(
            self.addressed_gap_codes,
            label="addressed_gap_code",
        )
        if not self.addressed_gap_codes:
            raise ValueError("Theoretical sampling result addressed_gap_codes are required")
        self.addressed_gap_types = _normalize_unique_nonempty(
            list(self.addressed_gap_types),
            label="addressed_gap_type",
        )
        if not self.addressed_gap_types:
            raise ValueError("Theoretical sampling result addressed_gap_types are required")
        self.success_criteria_met = _normalize_unique_nonempty(
            self.success_criteria_met,
            label="success_criterion_met",
            unique=False,
        )
        if not self.success_criteria_met:
            raise ValueError("Theoretical sampling result success_criteria_met is required")
        if not self.caution.strip():
            raise ValueError("Theoretical sampling result caution must be non-empty")
        return self


class TheoreticalSamplingPreflightError(BaseModel):
    """One theoretical-sampling protocol preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class TheoreticalSamplingPreflightReport(BaseModel):
    """Machine-readable theoretical-sampling preflight report."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["theoretical_sampling_protocol_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    target_gap_codes: list[str] = Field(description="Protocol target gap codes")
    covered_gap_codes: list[str] = Field(description="Candidate-covered target gap codes")
    target_gap_types: list[str] = Field(description="Protocol target gap types")
    covered_gap_types: list[str] = Field(description="Candidate-covered target gap types")
    candidate_source: str | None = Field(
        default=None,
        description="Protocol candidate source when available",
    )
    collection_mode: str | None = Field(
        default=None,
        description="Protocol collection mode when available",
    )
    candidate_count: int = Field(description="Number of validated candidates")
    result_selected_count: int = Field(description="Number of selected result candidates")
    source_kinds: list[str] = Field(description="Candidate source kinds found")
    errors: list[TheoreticalSamplingPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_theoretical_sampling_payloads(
    protocol_payload: Any,
    candidates_payload: Any | None = None,
    results_payload: Any | None = None,
) -> TheoreticalSamplingPreflightReport:
    """Cross-check candidate/result packages against a registered protocol."""
    errors: list[TheoreticalSamplingPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    candidate_package = _validate_candidates(candidates_payload, errors)
    result_package = _validate_results(results_payload, errors)

    if protocol is not None and candidate_package is not None:
        _check_package_matches_protocol(protocol, candidate_package, errors)
        _check_candidate_policy_matches_protocol(protocol, candidate_package, errors)
        _check_candidates_cover_protocol(protocol, candidate_package, errors)
    if protocol is not None and result_package is not None:
        _check_package_matches_protocol(protocol, result_package, errors)
        _check_results_match_protocol(protocol, result_package, errors)
    if candidate_package is not None and result_package is not None:
        _check_results_match_candidates(candidate_package, result_package, errors)

    return _build_report(
        protocol=protocol,
        candidate_package=candidate_package,
        result_package=result_package,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[TheoreticalSamplingPreflightError],
) -> TheoreticalSamplingProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_theoretical_sampling_protocol_payload(payload)
    except ValueError as exc:
        errors.append(TheoreticalSamplingPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_candidates(
    payload: Any | None,
    errors: list[TheoreticalSamplingPreflightError],
) -> TheoreticalSamplingCandidatePackage | None:
    """Validate candidate payload and append a preflight error on failure."""
    if payload is None:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidates_file",
                message="Theoretical sampling preflight requires a candidate package",
            )
        )
        return None
    if not isinstance(payload, dict):
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidates_file",
                message="Theoretical sampling candidate package must be a JSON object",
            )
        )
        return None
    if payload.get("schema_version") != 1:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidates_file",
                message="Theoretical sampling candidate package must include schema_version=1",
            )
        )
        return None
    try:
        return TheoreticalSamplingCandidatePackage.model_validate(payload)
    except ValidationError as exc:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidates_file",
                message=f"Invalid theoretical sampling candidate package: {exc}",
            )
        )
        return None


def _validate_results(
    payload: Any | None,
    errors: list[TheoreticalSamplingPreflightError],
) -> TheoreticalSamplingResultPackage | None:
    """Validate optional result payload and append a preflight error on failure."""
    if payload is None:
        return None
    if not isinstance(payload, dict):
        errors.append(
            TheoreticalSamplingPreflightError(
                field="results_file",
                message="Theoretical sampling result package must be a JSON object",
            )
        )
        return None
    if payload.get("schema_version") != 1:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="results_file",
                message="Theoretical sampling result package must include schema_version=1",
            )
        )
        return None
    try:
        return TheoreticalSamplingResultPackage.model_validate(payload)
    except ValidationError as exc:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="results_file",
                message=f"Invalid theoretical sampling result package: {exc}",
            )
        )
        return None


def _check_package_matches_protocol(
    protocol: TheoreticalSamplingProtocolPackage,
    package: TheoreticalSamplingCandidatePackage | TheoreticalSamplingResultPackage,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append errors for common protocol/package identity drift."""
    _check_equal("protocol_id", protocol.protocol_id, package.protocol_id, errors)
    _check_equal("project_id", protocol.project_id, package.project_id, errors)
    _check_equal(
        "corpus_sha256",
        protocol.corpus_sha256.lower(),
        package.corpus_sha256.lower(),
        errors,
    )
    if protocol.project_state_sha256 is not None:
        if package.project_state_sha256 is None:
            errors.append(
                TheoreticalSamplingPreflightError(
                    field="project_state_sha256",
                    message="Protocol locks project_state_sha256 but package does not supply one",
                )
            )
        else:
            _check_equal(
                "project_state_sha256",
                protocol.project_state_sha256.lower(),
                package.project_state_sha256.lower(),
                errors,
            )


def _check_candidate_policy_matches_protocol(
    protocol: TheoreticalSamplingProtocolPackage,
    candidate_package: TheoreticalSamplingCandidatePackage,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append errors for source-policy or collection-mode drift."""
    _check_equal(
        "candidate_source",
        protocol.candidate_source,
        candidate_package.candidate_source,
        errors,
    )
    _check_equal(
        "collection_mode",
        protocol.collection_mode,
        candidate_package.collection_mode,
        errors,
    )
    if len(candidate_package.candidates) > protocol.max_suggestions:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidate_count",
                message=(
                    f"Candidate package contains {len(candidate_package.candidates)} "
                    f"candidate(s), above protocol max_suggestions {protocol.max_suggestions}"
                ),
            )
        )

    source_kinds = {candidate.source_kind for candidate in candidate_package.candidates}
    if protocol.candidate_source == "loaded_uncoded_documents" and "external_case" in source_kinds:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidate_source",
                message="loaded_uncoded_documents protocols cannot include external_case candidates",
            )
        )
    if protocol.candidate_source == "external_recruitment_pool" and "loaded_document" in source_kinds:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="candidate_source",
                message="external_recruitment_pool protocols cannot include loaded_document candidates",
            )
        )
    if protocol.collection_mode == "select_existing_documents" and "external_case" in source_kinds:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="collection_mode",
                message="select_existing_documents protocols cannot include external_case candidates",
            )
        )
    if protocol.collection_mode == "collect_new_data" and "loaded_document" in source_kinds:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="collection_mode",
                message="collect_new_data protocols cannot include loaded_document candidates",
            )
        )


def _check_candidates_cover_protocol(
    protocol: TheoreticalSamplingProtocolPackage,
    candidate_package: TheoreticalSamplingCandidatePackage,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append errors for candidate target-gap coverage drift."""
    candidate_gap_codes = {
        gap_code
        for candidate in candidate_package.candidates
        for gap_code in candidate.gap_codes
    }
    candidate_gap_types = {
        gap_type
        for candidate in candidate_package.candidates
        for gap_type in candidate.gap_types
    }
    _check_expected_set(
        "target_gap_codes",
        set(protocol.target_gap_codes),
        candidate_gap_codes,
        errors,
    )
    _check_expected_set(
        "target_gap_types",
        set(protocol.target_gap_types),
        candidate_gap_types,
        errors,
    )


def _check_results_match_protocol(
    protocol: TheoreticalSamplingProtocolPackage,
    result_package: TheoreticalSamplingResultPackage,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append errors for result drift from protocol target gaps."""
    unexpected_gap_codes = sorted(set(result_package.addressed_gap_codes) - set(protocol.target_gap_codes))
    if unexpected_gap_codes:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="addressed_gap_codes",
                message="Result package addresses unregistered gap code(s): "
                + ", ".join(unexpected_gap_codes),
            )
        )
    unexpected_gap_types = sorted(set(result_package.addressed_gap_types) - set(protocol.target_gap_types))
    if unexpected_gap_types:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="addressed_gap_types",
                message="Result package addresses unregistered gap type(s): "
                + ", ".join(unexpected_gap_types),
            )
        )
    unexpected_criteria = sorted(
        set(result_package.success_criteria_met) - set(protocol.success_criteria)
    )
    if unexpected_criteria:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="success_criteria_met",
                message="Result package marks unregistered success criteria as met: "
                + " | ".join(unexpected_criteria),
            )
        )


def _check_results_match_candidates(
    candidate_package: TheoreticalSamplingCandidatePackage,
    result_package: TheoreticalSamplingResultPackage,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append errors for selected result candidates absent from the pool."""
    candidate_ids = {candidate.candidate_id for candidate in candidate_package.candidates}
    unknown_ids = sorted(set(result_package.selected_candidate_ids) - candidate_ids)
    if unknown_ids:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="selected_candidate_ids",
                message="Result package selected unknown candidate ID(s): "
                + ", ".join(unknown_ids),
            )
        )
    selected_candidates = [
        candidate
        for candidate in candidate_package.candidates
        if candidate.candidate_id in set(result_package.selected_candidate_ids)
    ]
    selected_gap_codes = {
        gap_code
        for candidate in selected_candidates
        for gap_code in candidate.gap_codes
    }
    missing_addressed_gap_codes = sorted(
        set(result_package.addressed_gap_codes) - selected_gap_codes
    )
    if missing_addressed_gap_codes:
        errors.append(
            TheoreticalSamplingPreflightError(
                field="addressed_gap_codes",
                message="Result addressed gap code(s) not covered by selected candidates: "
                + ", ".join(missing_addressed_gap_codes),
            )
        )


def _build_report(
    *,
    protocol: TheoreticalSamplingProtocolPackage | None,
    candidate_package: TheoreticalSamplingCandidatePackage | None,
    result_package: TheoreticalSamplingResultPackage | None,
    errors: list[TheoreticalSamplingPreflightError],
) -> TheoreticalSamplingPreflightReport:
    """Build the final preflight report."""
    covered_gap_codes: list[str] = []
    covered_gap_types: list[str] = []
    source_kinds: list[str] = []
    candidate_count = 0
    if candidate_package is not None:
        covered_gap_codes = sorted(
            {
                gap_code
                for candidate in candidate_package.candidates
                for gap_code in candidate.gap_codes
            }
        )
        covered_gap_types = sorted(
            {
                gap_type
                for candidate in candidate_package.candidates
                for gap_type in candidate.gap_types
            }
        )
        source_kinds = sorted({candidate.source_kind for candidate in candidate_package.candidates})
        candidate_count = len(candidate_package.candidates)

    return TheoreticalSamplingPreflightReport(
        schema_version=1,
        package_type="theoretical_sampling_protocol_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        target_gap_codes=list(protocol.target_gap_codes) if protocol is not None else [],
        covered_gap_codes=covered_gap_codes,
        target_gap_types=list(protocol.target_gap_types) if protocol is not None else [],
        covered_gap_types=covered_gap_types,
        candidate_source=protocol.candidate_source if protocol is not None else None,
        collection_mode=protocol.collection_mode if protocol is not None else None,
        candidate_count=candidate_count,
        result_selected_count=(
            len(result_package.selected_candidate_ids) if result_package is not None else 0
        ),
        source_kinds=source_kinds,
        errors=errors,
        caution=THEORETICAL_SAMPLING_PREFLIGHT_CAUTION,
    )


def _check_equal(
    field: str,
    expected: str,
    actual: str,
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append an equality error when expected and actual values diverge."""
    if expected == actual:
        return
    errors.append(
        TheoreticalSamplingPreflightError(
            field=field,
            message=f"Expected {field} {expected!r}, got {actual!r}",
        )
    )


def _check_expected_set(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[TheoreticalSamplingPreflightError],
) -> None:
    """Append a set mismatch error when candidate gaps drift from protocol."""
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if not missing and not unexpected:
        return
    parts = []
    if missing:
        parts.append("missing: " + ", ".join(missing))
    if unexpected:
        parts.append("unexpected: " + ", ".join(unexpected))
    errors.append(TheoreticalSamplingPreflightError(field=field, message="; ".join(parts)))


def _normalize_unique_nonempty(
    values: list[str],
    *,
    label: str,
    unique: bool = True,
) -> list[str]:
    """Normalize strings and reject duplicates when requested."""
    normalized = [value.strip() for value in values if value.strip()]
    if unique:
        duplicates = sorted(value for value in set(normalized) if normalized.count(value) > 1)
        if duplicates:
            raise ValueError(
                f"Duplicate theoretical sampling {label}(s): " + ", ".join(duplicates)
            )
    return normalized


def _is_sha256(value: str) -> bool:
    """Return whether *value* is a 64-character SHA-256 hex digest."""
    return bool(_SHA256_RE.fullmatch(value))
