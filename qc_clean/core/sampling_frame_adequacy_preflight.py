"""Preflight sampling-frame adequacy result packages against protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from qc_clean.core.sampling_frame_adequacy_protocol import (
    SAMPLING_FRAME_ADEQUACY_PROTOCOL_CAUTION,
    SamplingFrameAdequacyProtocolPackage,
    SamplingFrameAdequacyResultPackage,
    validate_sampling_frame_adequacy_protocol_payload,
    validate_sampling_frame_adequacy_result_payload,
)


SAMPLING_FRAME_ADEQUACY_PREFLIGHT_CAUTION = (
    "Sampling-frame adequacy preflight is process/provenance metadata only; "
    "it is not sampling-frame adequacy evidence, not permission for population "
    "generalization, not methodological-validity evidence, and not SOTA evidence."
)


class SamplingFrameAdequacyPreflightError(BaseModel):
    """One sampling-frame adequacy protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class SamplingFrameAdequacyPreflightReport(BaseModel):
    """Machine-readable sampling-frame adequacy preflight report."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["sampling_frame_adequacy_protocol_result_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    dimensions: list[str] = Field(description="Protocol dimensions")
    result_row_count: int = Field(description="Number of validated result rows")
    reviewer_count: int = Field(description="Number of unique reviewers in result rows")
    reviewer_types: list[str] = Field(description="Reviewer types found in result rows")
    ratings: list[str] = Field(description="Ratings found in result rows")
    errors: list[SamplingFrameAdequacyPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_sampling_frame_adequacy_payloads(
    protocol_payload: Any,
    adequacy_payload: Any | None = None,
    *,
    adequacy_file_sha256: str | None = None,
) -> SamplingFrameAdequacyPreflightReport:
    """Cross-check sampling-frame adequacy result rows against a protocol."""
    errors: list[SamplingFrameAdequacyPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    results = _validate_results(adequacy_payload, errors)

    if protocol is not None and results is not None:
        _check_package_matches_protocol(protocol, results, errors)
        _check_hash_lock(
            "adequacy_file_sha256",
            protocol.outcome_file_sha256,
            adequacy_file_sha256,
            errors,
        )
        _check_reviewers_match_protocol(protocol, results, errors)
        _check_dimensions_match_protocol(protocol, results, errors)

    return _build_report(protocol=protocol, results=results, errors=errors)


def _validate_protocol(
    payload: Any,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> SamplingFrameAdequacyProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_sampling_frame_adequacy_protocol_payload(payload)
    except ValueError as exc:
        errors.append(SamplingFrameAdequacyPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_results(
    payload: Any | None,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> SamplingFrameAdequacyResultPackage | None:
    """Validate result payload and append a preflight error on failure."""
    if payload is None:
        errors.append(
            SamplingFrameAdequacyPreflightError(
                field="adequacy_file",
                message="sampling-frame adequacy preflight requires a result package",
            )
        )
        return None
    try:
        return validate_sampling_frame_adequacy_result_payload(payload)
    except ValueError as exc:
        errors.append(
            SamplingFrameAdequacyPreflightError(field="adequacy_file", message=str(exc))
        )
        return None


def _check_package_matches_protocol(
    protocol: SamplingFrameAdequacyProtocolPackage,
    results: SamplingFrameAdequacyResultPackage,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> None:
    """Append errors for protocol/result package metadata drift."""
    comparisons = [
        ("protocol_id", protocol.protocol_id, results.protocol_id),
        ("project_id", protocol.project_id, results.project_id),
        ("corpus_sha256", protocol.corpus_sha256, results.corpus_sha256),
        ("project_state_sha256", protocol.project_state_sha256, results.project_state_sha256),
        ("corpus_scope_sha256", protocol.corpus_scope_sha256, results.corpus_scope_sha256),
    ]
    for field, expected, actual in comparisons:
        if expected is None:
            continue
        if actual is None or str(expected).lower() != str(actual).lower():
            errors.append(
                SamplingFrameAdequacyPreflightError(
                    field=field,
                    message=(
                        f"Protocol {field} {expected!r} does not match result "
                        f"{field} {actual!r}"
                    ),
                )
            )


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> None:
    """Append a hash-lock error when protocol and actual file hash diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            SamplingFrameAdequacyPreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            SamplingFrameAdequacyPreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_reviewers_match_protocol(
    protocol: SamplingFrameAdequacyProtocolPackage,
    results: SamplingFrameAdequacyResultPackage,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> None:
    """Append errors for reviewer drift from protocol metadata."""
    expected_types = set(protocol.reviewer_plan.reviewer_types)
    actual_types = {row.reviewer_type for row in results.evaluations}
    _check_set_equal("reviewer_types", expected_types, actual_types, errors)

    actual_reviewers = {row.reviewer for row in results.evaluations}
    if len(actual_reviewers) < protocol.reviewer_plan.planned_reviewer_count:
        errors.append(
            SamplingFrameAdequacyPreflightError(
                field="reviewer_count",
                message=(
                    "sampling-frame result rows include "
                    f"{len(actual_reviewers)} unique reviewer(s), below planned "
                    f"count {protocol.reviewer_plan.planned_reviewer_count}"
                ),
            )
        )


def _check_dimensions_match_protocol(
    protocol: SamplingFrameAdequacyProtocolPackage,
    results: SamplingFrameAdequacyResultPackage,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> None:
    """Append errors for dimension coverage drift."""
    expected_dimensions = set(protocol.dimensions)
    actual_dimensions = {row.dimension for row in results.evaluations}
    _check_set_equal("dimensions", expected_dimensions, actual_dimensions, errors)


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[SamplingFrameAdequacyPreflightError],
) -> None:
    """Append a set mismatch error when expected and actual values differ."""
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if not missing and not unexpected:
        return
    parts = []
    if missing:
        parts.append("missing: " + ", ".join(missing))
    if unexpected:
        parts.append("unexpected: " + ", ".join(unexpected))
    errors.append(SamplingFrameAdequacyPreflightError(field=field, message="; ".join(parts)))


def _build_report(
    *,
    protocol: SamplingFrameAdequacyProtocolPackage | None,
    results: SamplingFrameAdequacyResultPackage | None,
    errors: list[SamplingFrameAdequacyPreflightError],
) -> SamplingFrameAdequacyPreflightReport:
    """Build the final sampling-frame adequacy preflight report."""
    evaluations = results.evaluations if results is not None else []
    return SamplingFrameAdequacyPreflightReport(
        schema_version=1,
        package_type="sampling_frame_adequacy_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        dimensions=list(protocol.dimensions) if protocol is not None else [],
        result_row_count=len(evaluations),
        reviewer_count=len({row.reviewer for row in evaluations}),
        reviewer_types=sorted({row.reviewer_type for row in evaluations}),
        ratings=sorted({row.rating for row in evaluations}),
        errors=errors,
        caution=(
            protocol.caution
            if protocol is not None and protocol.caution
            else SAMPLING_FRAME_ADEQUACY_PROTOCOL_CAUTION
        ),
    )
