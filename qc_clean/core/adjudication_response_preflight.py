"""Preflight completed adjudication responses against protocol and sample packages."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.adjudication_preflight import (
    AdjudicationPreflightError,
    preflight_adjudication_protocol_sample_payloads,
)
from qc_clean.core.adjudication_protocol import (
    AdjudicationProtocolPackage,
    validate_adjudication_protocol_payload,
)
from qc_clean.core.adjudication_sample import (
    AdjudicationResponseValidationReport,
    AdjudicationSamplePackage,
    TARGET_TYPE_ORDER,
    TargetType,
    validate_adjudication_response_payload,
)


RESPONSE_PREFLIGHT_CAUTION = (
    "Adjudication response preflight is process metadata only; it is not expert "
    "evidence, labels, correctness estimates, validity evidence, or a benchmark result."
)


class AdjudicationResponsePreflightReport(BaseModel):
    """Machine-readable report for completed adjudication response preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["adjudication_response_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Protocol project ID when available")
    sample_project_id: str | None = Field(
        default=None,
        description="Sample package project ID when available",
    )
    response_project_id: str | None = Field(
        default=None,
        description="Response package project ID when available",
    )
    sample_package_sha256: str | None = Field(
        default=None,
        description="Concrete sample package file SHA-256 when available",
    )
    required_target_item_types: list[TargetType] = Field(
        default_factory=list,
        description="Target item types required by the protocol",
    )
    sample_item_count: int = Field(description="Number of sample items expected")
    response_item_count: int = Field(description="Number of response package items returned")
    completed_response_count: int = Field(description="Number of items with complete responses")
    completed_counts_by_target_type: dict[str, int] = Field(
        default_factory=dict,
        description="Complete response counts by target type",
    )
    errors: list[AdjudicationPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_adjudication_responses_payloads(
    protocol_payload: Any,
    sample_payload: Any,
    response_payload: Any,
    *,
    sample_file_sha256: str | None = None,
) -> AdjudicationResponsePreflightReport:
    """Cross-check completed responses against protocol, sample, and provenance."""
    errors: list[AdjudicationPreflightError] = []
    protocol_sample_report = preflight_adjudication_protocol_sample_payloads(
        protocol_payload,
        sample_payload,
        sample_file_sha256=sample_file_sha256,
    )
    errors.extend(
        AdjudicationPreflightError(
            field=f"protocol_sample_preflight.{error.field}",
            message=error.message,
        )
        for error in protocol_sample_report.errors
    )

    protocol = _validate_protocol(protocol_payload, errors)
    sample = _validate_package(sample_payload, field="sample", errors=errors)
    response_package = _validate_package(response_payload, field="responses", errors=errors)
    response_validation = validate_adjudication_response_payload(response_payload)
    _append_response_validation_errors(response_validation, errors)

    if sample is not None and response_package is not None:
        _check_response_provenance(sample, response_package, errors)
        _check_item_id_set(sample, response_package, errors)

    completed_counts = _completed_counts_by_target_type(response_payload, sample, response_validation)
    if protocol is not None:
        _check_required_response_types(protocol, completed_counts, errors)

    return _build_report(
        protocol=protocol,
        sample=sample,
        response_package=response_package,
        sample_file_sha256=sample_file_sha256,
        response_validation=response_validation,
        completed_counts=completed_counts,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[AdjudicationPreflightError],
) -> AdjudicationProtocolPackage | None:
    """Validate protocol payload for report metadata and required type checks."""
    try:
        return validate_adjudication_protocol_payload(payload)
    except ValueError as exc:
        if not _has_error(errors, "protocol_sample_preflight.protocol"):
            errors.append(AdjudicationPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_package(
    payload: Any,
    *,
    field: str,
    errors: list[AdjudicationPreflightError],
) -> AdjudicationSamplePackage | None:
    """Validate a sample-shaped package and append a report error on failure."""
    try:
        return AdjudicationSamplePackage.model_validate(payload)
    except ValidationError as exc:
        errors.append(
            AdjudicationPreflightError(
                field=field,
                message=f"Invalid adjudication sample package: {exc}",
            )
        )
        return None


def _append_response_validation_errors(
    response_validation: AdjudicationResponseValidationReport,
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append completed-response validation failures."""
    if response_validation.status == "complete":
        return
    for error in response_validation.errors:
        errors.append(
            AdjudicationPreflightError(
                field=f"response_validation.{error.field}",
                message=f"{error.item_id}: {error.message}",
            )
        )


def _check_response_provenance(
    sample: AdjudicationSamplePackage,
    response_package: AdjudicationSamplePackage,
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append errors for response package provenance drift from the sample."""
    if response_package.project_id != sample.project_id:
        errors.append(
            AdjudicationPreflightError(
                field="project_id",
                message=(
                    f"Response project_id {response_package.project_id!r} does not match "
                    f"sample project_id {sample.project_id!r}"
                ),
            )
        )
    if response_package.corpus_sha256 != sample.corpus_sha256:
        errors.append(
            AdjudicationPreflightError(
                field="corpus_sha256",
                message="Response corpus_sha256 does not match sample corpus_sha256",
            )
        )
    if response_package.project_state_sha256 != sample.project_state_sha256:
        errors.append(
            AdjudicationPreflightError(
                field="project_state_sha256",
                message="Response project_state_sha256 does not match sample package",
            )
        )


def _check_item_id_set(
    sample: AdjudicationSamplePackage,
    response_package: AdjudicationSamplePackage,
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append an error unless response item IDs exactly match sample item IDs."""
    sample_ids = {item.item_id for item in sample.items}
    response_ids = {item.item_id for item in response_package.items}
    if sample_ids == response_ids:
        return

    missing = sorted(sample_ids - response_ids)
    extra = sorted(response_ids - sample_ids)
    errors.append(
        AdjudicationPreflightError(
            field="item_ids",
            message=(
                "Response item IDs must exactly match the sample item IDs; "
                f"missing={missing}, extra={extra}"
            ),
        )
    )


def _completed_counts_by_target_type(
    response_payload: Any,
    sample: AdjudicationSamplePackage | None,
    response_validation: AdjudicationResponseValidationReport,
) -> dict[str, int]:
    """Count complete responses by target type from raw response items."""
    counts = {target_type: 0 for target_type in TARGET_TYPE_ORDER}
    if response_validation.status != "complete" or sample is None or not isinstance(response_payload, dict):
        return counts

    sample_types_by_item_id = {item.item_id: item.target_type for item in sample.items}
    raw_items = response_payload.get("items", [])
    if not isinstance(raw_items, list):
        return counts

    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue
        target_type = sample_types_by_item_id.get(str(raw_item.get("item_id") or ""))
        if target_type is not None:
            counts[target_type] += 1
    return counts


def _check_required_response_types(
    protocol: AdjudicationProtocolPackage,
    completed_counts: dict[str, int],
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append errors for protocol-required types with no complete response."""
    for target_type in protocol.sampling_plan.target_item_types:
        if completed_counts.get(target_type, 0) < 1:
            errors.append(
                AdjudicationPreflightError(
                    field=f"target_item_types.{target_type}",
                    message=f"Required target type {target_type!r} has no complete response",
                )
            )


def _build_report(
    *,
    protocol: AdjudicationProtocolPackage | None,
    sample: AdjudicationSamplePackage | None,
    response_package: AdjudicationSamplePackage | None,
    sample_file_sha256: str | None,
    response_validation: AdjudicationResponseValidationReport,
    completed_counts: dict[str, int],
    errors: list[AdjudicationPreflightError],
) -> AdjudicationResponsePreflightReport:
    """Build the final response preflight report."""
    return AdjudicationResponsePreflightReport(
        schema_version=1,
        package_type="adjudication_response_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        sample_project_id=sample.project_id if sample is not None else None,
        response_project_id=(
            response_package.project_id if response_package is not None else None
        ),
        sample_package_sha256=sample_file_sha256,
        required_target_item_types=(
            list(protocol.sampling_plan.target_item_types) if protocol is not None else []
        ),
        sample_item_count=len(sample.items) if sample is not None else 0,
        response_item_count=(
            len(response_package.items) if response_package is not None else 0
        ),
        completed_response_count=response_validation.valid_response_count,
        completed_counts_by_target_type=completed_counts,
        errors=errors,
        caution=RESPONSE_PREFLIGHT_CAUTION,
    )


def _has_error(errors: list[AdjudicationPreflightError], field: str) -> bool:
    """Return whether a field already has a reported error."""
    return any(error.field == field for error in errors)
