"""Preflight adjudication protocol packages against sample packages."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.adjudication_protocol import (
    AdjudicationProtocolPackage,
    validate_adjudication_protocol_payload,
)
from qc_clean.core.adjudication_sample import (
    AdjudicationSamplePackage,
    TARGET_TYPE_ORDER,
    TargetType,
)


PREFLIGHT_CAUTION = (
    "Adjudication protocol/sample preflight is process metadata only; it is not "
    "expert evidence, labels, correctness estimates, validity evidence, or a "
    "benchmark result."
)


class AdjudicationPreflightError(BaseModel):
    """One protocol-to-sample preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class AdjudicationProtocolSamplePreflightReport(BaseModel):
    """Machine-readable report for protocol-to-sample preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["adjudication_protocol_sample_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Protocol project ID when available")
    sample_project_id: str | None = Field(
        default=None,
        description="Sample package project ID when available",
    )
    corpus_sha256: str | None = Field(
        default=None,
        description="Protocol corpus SHA-256 when available",
    )
    sample_corpus_sha256: str | None = Field(
        default=None,
        description="Sample package corpus SHA-256 when available",
    )
    project_state_sha256: str | None = Field(
        default=None,
        description="Protocol project-state SHA-256 when available",
    )
    sample_project_state_sha256: str | None = Field(
        default=None,
        description="Sample package project-state SHA-256 when available",
    )
    sample_package_sha256: str | None = Field(
        default=None,
        description="Concrete sample package file SHA-256 when available",
    )
    required_target_item_types: list[TargetType] = Field(
        default_factory=list,
        description="Target item types required by the protocol",
    )
    returned_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Actual returned sample item counts by target type",
    )
    total_returned_count: int = Field(description="Actual total returned sample items")
    planned_sample_size: int | None = Field(
        default=None,
        description="Protocol planned sample size when available",
    )
    errors: list[AdjudicationPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_adjudication_protocol_sample_payloads(
    protocol_payload: Any,
    sample_payload: Any,
    *,
    sample_file_sha256: str | None = None,
) -> AdjudicationProtocolSamplePreflightReport:
    """Cross-check a protocol package against a concrete sample package."""
    errors: list[AdjudicationPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    sample = _validate_sample(sample_payload, errors)
    if protocol is None or sample is None:
        return _build_report(
            protocol=protocol,
            sample=sample,
            sample_file_sha256=sample_file_sha256,
            returned_counts={target_type: 0 for target_type in TARGET_TYPE_ORDER} | {"total": 0},
            errors=errors,
        )

    returned_counts = _returned_counts(sample)
    _check_project_and_hashes(protocol, sample, sample_file_sha256, errors)
    _check_target_type_coverage(protocol, returned_counts, errors)
    _check_planned_sample_size(protocol, returned_counts["total"], errors)
    return _build_report(
        protocol=protocol,
        sample=sample,
        sample_file_sha256=sample_file_sha256,
        returned_counts=returned_counts,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[AdjudicationPreflightError],
) -> AdjudicationProtocolPackage | None:
    """Validate protocol payload and append a report error on failure."""
    try:
        return validate_adjudication_protocol_payload(payload)
    except ValueError as exc:
        errors.append(AdjudicationPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_sample(
    payload: Any,
    errors: list[AdjudicationPreflightError],
) -> AdjudicationSamplePackage | None:
    """Validate sample payload and append a report error on failure."""
    try:
        return AdjudicationSamplePackage.model_validate(payload)
    except ValidationError as exc:
        errors.append(
            AdjudicationPreflightError(
                field="sample",
                message=f"Invalid adjudication sample package: {exc}",
            )
        )
        return None


def _check_project_and_hashes(
    protocol: AdjudicationProtocolPackage,
    sample: AdjudicationSamplePackage,
    sample_file_sha256: str | None,
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append project and hash mismatch errors."""
    if protocol.project_id != sample.project_id:
        errors.append(
            AdjudicationPreflightError(
                field="project_id",
                message=(
                    f"Protocol project_id {protocol.project_id!r} does not match "
                    f"sample project_id {sample.project_id!r}"
                ),
            )
        )
    if protocol.corpus_sha256 != sample.corpus_sha256:
        errors.append(
            AdjudicationPreflightError(
                field="corpus_sha256",
                message="Protocol corpus_sha256 does not match sample corpus_sha256",
            )
        )
    if (
        protocol.project_state_sha256 is not None
        and protocol.project_state_sha256 != sample.project_state_sha256
    ):
        errors.append(
            AdjudicationPreflightError(
                field="project_state_sha256",
                message="Protocol project_state_sha256 does not match sample package",
            )
        )

    expected_sample_hash = protocol.sampling_plan.sample_package_sha256
    if expected_sample_hash is not None and sample_file_sha256 is None:
        errors.append(
            AdjudicationPreflightError(
                field="sample_package_sha256",
                message="Protocol records sample_package_sha256 but no sample file hash was provided",
            )
        )
    elif expected_sample_hash is not None and expected_sample_hash != sample_file_sha256:
        errors.append(
            AdjudicationPreflightError(
                field="sample_package_sha256",
                message="Protocol sample_package_sha256 does not match the sample file",
            )
        )


def _check_target_type_coverage(
    protocol: AdjudicationProtocolPackage,
    returned_counts: dict[str, int],
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append errors for required target types with no returned sample items."""
    for target_type in protocol.sampling_plan.target_item_types:
        if returned_counts.get(target_type, 0) < 1:
            errors.append(
                AdjudicationPreflightError(
                    field=f"target_item_types.{target_type}",
                    message=f"Required target type {target_type!r} has no returned sample items",
                )
            )


def _check_planned_sample_size(
    protocol: AdjudicationProtocolPackage,
    total_returned_count: int,
    errors: list[AdjudicationPreflightError],
) -> None:
    """Append an error when sample size is below the protocol plan."""
    planned = protocol.sampling_plan.planned_sample_size
    if total_returned_count < planned:
        errors.append(
            AdjudicationPreflightError(
                field="planned_sample_size",
                message=(
                    f"Sample returned {total_returned_count} item(s), below planned "
                    f"sample size {planned}"
                ),
            )
        )


def _returned_counts(sample: AdjudicationSamplePackage) -> dict[str, int]:
    """Count actual returned sample items by target type."""
    counts = {target_type: 0 for target_type in TARGET_TYPE_ORDER}
    for item in sample.items:
        counts[item.target_type] += 1
    counts["total"] = len(sample.items)
    return counts


def _build_report(
    *,
    protocol: AdjudicationProtocolPackage | None,
    sample: AdjudicationSamplePackage | None,
    sample_file_sha256: str | None,
    returned_counts: dict[str, int],
    errors: list[AdjudicationPreflightError],
) -> AdjudicationProtocolSamplePreflightReport:
    """Build the final preflight report."""
    return AdjudicationProtocolSamplePreflightReport(
        schema_version=1,
        package_type="adjudication_protocol_sample_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        sample_project_id=sample.project_id if sample is not None else None,
        corpus_sha256=protocol.corpus_sha256 if protocol is not None else None,
        sample_corpus_sha256=sample.corpus_sha256 if sample is not None else None,
        project_state_sha256=(
            protocol.project_state_sha256 if protocol is not None else None
        ),
        sample_project_state_sha256=(
            sample.project_state_sha256 if sample is not None else None
        ),
        sample_package_sha256=sample_file_sha256,
        required_target_item_types=(
            list(protocol.sampling_plan.target_item_types) if protocol is not None else []
        ),
        returned_counts=returned_counts,
        total_returned_count=returned_counts.get("total", 0),
        planned_sample_size=(
            protocol.sampling_plan.planned_sample_size if protocol is not None else None
        ),
        errors=errors,
        caution=PREFLIGHT_CAUTION,
    )
