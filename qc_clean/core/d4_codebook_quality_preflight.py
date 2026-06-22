"""Preflight D4 codebook-quality result files against registered protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.bench import CodebookQualityEvaluation
from qc_clean.core.d4_codebook_quality_protocol import (
    D4CodebookQualityProtocolPackage,
    validate_d4_codebook_quality_protocol_payload,
)


D4_CODEBOOK_QUALITY_PREFLIGHT_CAUTION = (
    "D4 codebook-quality preflight is process/provenance metadata only; it is "
    "not blind expert-panel evidence, not LLM-judge evidence, not "
    "codebook-quality evidence, not methodological-validity evidence, and not "
    "SOTA evidence."
)


class D4CodebookQualityPreflightError(BaseModel):
    """One D4 codebook-quality protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D4CodebookQualityPreflightReport(BaseModel):
    """Machine-readable report for D4 codebook-quality preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d4_codebook_quality_protocol_result_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    rubric_metrics: list[str] = Field(description="Protocol D4 rubric metrics")
    target_scopes: list[str] = Field(description="Protocol D4 target scopes")
    result_row_count: int = Field(description="Number of validated D4 result rows")
    evaluator_count: int = Field(description="Number of unique evaluators in result rows")
    evaluator_types: list[str] = Field(description="Evaluator types found in result rows")
    errors: list[D4CodebookQualityPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d4_codebook_quality_payloads(
    protocol_payload: Any,
    quality_payload: Any | None = None,
    *,
    quality_file_sha256: str | None = None,
) -> D4CodebookQualityPreflightReport:
    """Cross-check D4 quality result rows against a registered protocol."""
    errors: list[D4CodebookQualityPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    quality_rows = _validate_quality_payload(quality_payload, errors)

    if protocol is not None and quality_rows:
        _check_hash_lock(
            "quality_file_sha256",
            protocol.outcome_file_sha256,
            quality_file_sha256,
            errors,
        )
        _check_evaluators_match_protocol(protocol, quality_rows, errors)
        _check_scopes_match_protocol(protocol, quality_rows, errors)

    return _build_report(
        protocol=protocol,
        quality_rows=quality_rows,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[D4CodebookQualityPreflightError],
) -> D4CodebookQualityProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d4_codebook_quality_protocol_payload(payload)
    except ValueError as exc:
        errors.append(D4CodebookQualityPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_quality_payload(
    payload: Any | None,
    errors: list[D4CodebookQualityPreflightError],
) -> list[CodebookQualityEvaluation]:
    """Validate supplied D4 quality rows and append a preflight error on failure."""
    if payload is None:
        errors.append(
            D4CodebookQualityPreflightError(
                field="quality_file",
                message="D4 protocol/result preflight requires a quality result file",
            )
        )
        return []
    try:
        raw_rows = _extract_rows(payload)
        return [CodebookQualityEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(D4CodebookQualityPreflightError(field="quality_file", message=str(exc)))
        return []


def _extract_rows(payload: Any) -> list[Any]:
    """Extract raw D4 result rows from either a raw list or keyed object."""
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(
        payload.get("codebook_quality_evaluations"),
        list,
    ):
        raw_rows = payload["codebook_quality_evaluations"]
    else:
        raise ValueError(
            "D4 codebook-quality payload must be a JSON list or object with "
            "'codebook_quality_evaluations'"
        )
    if not raw_rows:
        raise ValueError("D4 codebook-quality payload must contain at least one row")
    return raw_rows


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[D4CodebookQualityPreflightError],
) -> None:
    """Append a hash-lock error when protocol and actual file hash diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            D4CodebookQualityPreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            D4CodebookQualityPreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_evaluators_match_protocol(
    protocol: D4CodebookQualityProtocolPackage,
    rows: list[CodebookQualityEvaluation],
    errors: list[D4CodebookQualityPreflightError],
) -> None:
    """Append errors for evaluator drift from protocol metadata."""
    expected_types = set(protocol.evaluator_plan.evaluator_types)
    actual_types = {row.evaluator_type for row in rows}
    _check_set_equal("evaluator_types", expected_types, actual_types, errors)

    actual_evaluators = {row.evaluator for row in rows}
    if len(actual_evaluators) < protocol.evaluator_plan.planned_evaluator_count:
        errors.append(
            D4CodebookQualityPreflightError(
                field="evaluator_count",
                message=(
                    "D4 result rows include "
                    f"{len(actual_evaluators)} unique evaluator(s), below planned "
                    f"count {protocol.evaluator_plan.planned_evaluator_count}"
                ),
            )
        )


def _check_scopes_match_protocol(
    protocol: D4CodebookQualityProtocolPackage,
    rows: list[CodebookQualityEvaluation],
    errors: list[D4CodebookQualityPreflightError],
) -> None:
    """Append errors for target-scope drift and missing code IDs."""
    expected_scopes = set(protocol.target_scopes)
    actual_scopes = {row.scope for row in rows}
    _check_set_equal("target_scopes", expected_scopes, actual_scopes, errors)

    missing_code_ids = [
        row.evaluator
        for row in rows
        if row.scope == "individual_code" and row.code_id is None
    ]
    if missing_code_ids:
        errors.append(
            D4CodebookQualityPreflightError(
                field="individual_code_code_id",
                message=(
                    "D4 individual_code result rows require code_id; missing for "
                    + ", ".join(sorted(missing_code_ids))
                ),
            )
        )


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[D4CodebookQualityPreflightError],
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
    errors.append(D4CodebookQualityPreflightError(field=field, message="; ".join(parts)))


def _build_report(
    *,
    protocol: D4CodebookQualityProtocolPackage | None,
    quality_rows: list[CodebookQualityEvaluation],
    errors: list[D4CodebookQualityPreflightError],
) -> D4CodebookQualityPreflightReport:
    """Build the final preflight report."""
    return D4CodebookQualityPreflightReport(
        schema_version=1,
        package_type="d4_codebook_quality_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        rubric_metrics=list(protocol.rubric_metrics) if protocol is not None else [],
        target_scopes=list(protocol.target_scopes) if protocol is not None else [],
        result_row_count=len(quality_rows),
        evaluator_count=len({row.evaluator for row in quality_rows}),
        evaluator_types=sorted({row.evaluator_type for row in quality_rows}),
        errors=errors,
        caution=D4_CODEBOOK_QUALITY_PREFLIGHT_CAUTION,
    )
