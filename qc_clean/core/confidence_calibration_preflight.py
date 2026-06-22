"""Preflight confidence-calibration result files against protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.bench import ConfidenceCalibrationEvaluation
from qc_clean.core.confidence_calibration_protocol import (
    ConfidenceCalibrationProtocolPackage,
    validate_confidence_calibration_protocol_payload,
)


CONFIDENCE_CALIBRATION_PREFLIGHT_CAUTION = (
    "Confidence-calibration protocol/result preflight is process/provenance "
    "metadata only; it is not calibration proof, not held-out correctness "
    "evidence, not methodological-validity evidence, and not SOTA evidence."
)


class ConfidenceCalibrationPreflightError(BaseModel):
    """One confidence-calibration protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class ConfidenceCalibrationPreflightReport(BaseModel):
    """Machine-readable report for confidence-calibration preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["confidence_calibration_protocol_result_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    target_surfaces: list[str] = Field(description="Protocol calibration target surfaces")
    outcome_metrics: list[str] = Field(description="Protocol calibration outcome metrics")
    confidence_source: str | None = Field(
        default=None,
        description="Protocol confidence source when available",
    )
    result_row_count: int = Field(description="Number of validated calibration rows")
    item_count: int = Field(description="Number of unique calibration item IDs")
    evaluator_count: int = Field(description="Number of unique evaluators in rows")
    evaluators: list[str] = Field(description="Evaluators or label sources found in rows")
    errors: list[ConfidenceCalibrationPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_confidence_calibration_payloads(
    protocol_payload: Any,
    calibration_payload: Any | None = None,
    *,
    calibration_file_sha256: str | None = None,
) -> ConfidenceCalibrationPreflightReport:
    """Cross-check confidence-calibration result rows against a registered protocol."""
    errors: list[ConfidenceCalibrationPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    calibration_rows = _validate_calibration_payload(calibration_payload, errors)

    if protocol is not None and calibration_rows:
        _check_hash_lock(
            "calibration_file_sha256",
            protocol.outcome_file_sha256,
            calibration_file_sha256,
            errors,
        )
        _check_label_sources_match_protocol(protocol, calibration_rows, errors)
        _check_targets_match_protocol(protocol, calibration_rows, errors)
        _check_item_count_matches_protocol(protocol, calibration_rows, errors)

    return _build_report(
        protocol=protocol,
        calibration_rows=calibration_rows,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[ConfidenceCalibrationPreflightError],
) -> ConfidenceCalibrationProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_confidence_calibration_protocol_payload(payload)
    except ValueError as exc:
        errors.append(
            ConfidenceCalibrationPreflightError(
                field="protocol",
                message=str(exc),
            )
        )
        return None


def _validate_calibration_payload(
    payload: Any | None,
    errors: list[ConfidenceCalibrationPreflightError],
) -> list[ConfidenceCalibrationEvaluation]:
    """Validate supplied calibration rows and append errors on failure."""
    if payload is None:
        errors.append(
            ConfidenceCalibrationPreflightError(
                field="calibration_file",
                message=(
                    "Confidence-calibration preflight requires a calibration result file"
                ),
            )
        )
        return []
    try:
        raw_rows = _extract_rows(payload)
        return [ConfidenceCalibrationEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(
            ConfidenceCalibrationPreflightError(
                field="calibration_file",
                message=str(exc),
            )
        )
        return []


def _extract_rows(payload: Any) -> list[Any]:
    """Extract raw calibration rows from either a raw list or keyed object."""
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(
        payload.get("confidence_calibration_evaluations"),
        list,
    ):
        raw_rows = payload["confidence_calibration_evaluations"]
    else:
        raise ValueError(
            "Confidence-calibration payload must be a JSON list or object with "
            "'confidence_calibration_evaluations'"
        )
    if not raw_rows:
        raise ValueError(
            "Confidence-calibration payload must contain at least one row"
        )
    return raw_rows


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[ConfidenceCalibrationPreflightError],
) -> None:
    """Append a hash-lock error when protocol and actual file hash diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            ConfidenceCalibrationPreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            ConfidenceCalibrationPreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_label_sources_match_protocol(
    protocol: ConfidenceCalibrationProtocolPackage,
    rows: list[ConfidenceCalibrationEvaluation],
    errors: list[ConfidenceCalibrationPreflightError],
) -> None:
    """Append errors for label-source drift from protocol metadata."""
    _check_set_equal(
        "label_sources",
        set(protocol.label_plan.label_sources),
        {row.evaluator for row in rows},
        errors,
    )


def _check_targets_match_protocol(
    protocol: ConfidenceCalibrationProtocolPackage,
    rows: list[ConfidenceCalibrationEvaluation],
    errors: list[ConfidenceCalibrationPreflightError],
) -> None:
    """Append errors for target surface drift from protocol metadata."""
    _check_set_equal(
        "target_surfaces",
        set(protocol.target_surfaces),
        {row.surface for row in rows},
        errors,
    )


def _check_item_count_matches_protocol(
    protocol: ConfidenceCalibrationProtocolPackage,
    rows: list[ConfidenceCalibrationEvaluation],
    errors: list[ConfidenceCalibrationPreflightError],
) -> None:
    """Append an error when result rows undershoot planned item count."""
    item_count = len({row.item_id for row in rows})
    if item_count < protocol.planned_item_count:
        errors.append(
            ConfidenceCalibrationPreflightError(
                field="planned_item_count",
                message=(
                    "Confidence-calibration result rows include "
                    f"{item_count} unique item(s), below planned count "
                    f"{protocol.planned_item_count}"
                ),
            )
        )


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[ConfidenceCalibrationPreflightError],
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
    errors.append(
        ConfidenceCalibrationPreflightError(
            field=field,
            message="; ".join(parts),
        )
    )


def _build_report(
    *,
    protocol: ConfidenceCalibrationProtocolPackage | None,
    calibration_rows: list[ConfidenceCalibrationEvaluation],
    errors: list[ConfidenceCalibrationPreflightError],
) -> ConfidenceCalibrationPreflightReport:
    """Build the final preflight report."""
    return ConfidenceCalibrationPreflightReport(
        schema_version=1,
        package_type="confidence_calibration_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        target_surfaces=list(protocol.target_surfaces) if protocol is not None else [],
        outcome_metrics=list(protocol.outcome_metrics) if protocol is not None else [],
        confidence_source=(
            protocol.confidence_source if protocol is not None else None
        ),
        result_row_count=len(calibration_rows),
        item_count=len({row.item_id for row in calibration_rows}),
        evaluator_count=len({row.evaluator for row in calibration_rows}),
        evaluators=sorted({row.evaluator for row in calibration_rows}),
        errors=errors,
        caution=CONFIDENCE_CALIBRATION_PREFLIGHT_CAUTION,
    )
