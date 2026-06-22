"""Preflight D9 interpretive-preference result files against protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.bench import InterpretivePreferenceEvaluation
from qc_clean.core.d9_interpretive_preference_protocol import (
    D9InterpretivePreferenceProtocolPackage,
    validate_d9_interpretive_preference_protocol_payload,
)


D9_INTERPRETIVE_PREFERENCE_PREFLIGHT_CAUTION = (
    "D9 interpretive-preference preflight is process/provenance metadata only; "
    "it is not blind expert-parity evidence, not interpretive-depth evidence, "
    "not methodological-validity evidence, and not SOTA evidence."
)


class D9InterpretivePreferencePreflightError(BaseModel):
    """One D9 interpretive-preference protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D9InterpretivePreferencePreflightReport(BaseModel):
    """Machine-readable report for D9 protocol/result preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d9_interpretive_preference_protocol_result_preflight"] = (
        Field(description="Report package kind")
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    target_criteria: list[str] = Field(description="Protocol D9 target criteria")
    target_surfaces: list[str] = Field(description="Protocol D9 target surfaces")
    non_inferiority_margin: float | None = Field(
        default=None,
        description="Protocol non-inferiority margin when available",
    )
    result_row_count: int = Field(description="Number of validated D9 result rows")
    case_count: int = Field(description="Number of unique D9 comparison cases")
    evaluator_count: int = Field(description="Number of unique evaluators in rows")
    evaluator_types: list[str] = Field(description="Evaluator types found in rows")
    errors: list[D9InterpretivePreferencePreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d9_interpretive_preference_payloads(
    protocol_payload: Any,
    preference_payload: Any | None = None,
    *,
    preference_file_sha256: str | None = None,
) -> D9InterpretivePreferencePreflightReport:
    """Cross-check D9 preference result rows against a registered protocol."""
    errors: list[D9InterpretivePreferencePreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    preference_rows = _validate_preference_payload(preference_payload, errors)

    if protocol is not None and preference_rows:
        _check_hash_lock(
            "preference_file_sha256",
            protocol.outcome_file_sha256,
            preference_file_sha256,
            errors,
        )
        _check_evaluators_match_protocol(protocol, preference_rows, errors)
        _check_targets_match_protocol(protocol, preference_rows, errors)
        _check_case_count_matches_protocol(protocol, preference_rows, errors)

    return _build_report(
        protocol=protocol,
        preference_rows=preference_rows,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[D9InterpretivePreferencePreflightError],
) -> D9InterpretivePreferenceProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d9_interpretive_preference_protocol_payload(payload)
    except ValueError as exc:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field="protocol",
                message=str(exc),
            )
        )
        return None


def _validate_preference_payload(
    payload: Any | None,
    errors: list[D9InterpretivePreferencePreflightError],
) -> list[InterpretivePreferenceEvaluation]:
    """Validate supplied D9 preference rows and append errors on failure."""
    if payload is None:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field="preference_file",
                message="D9 preflight requires a preference result file",
            )
        )
        return []
    try:
        raw_rows = _extract_rows(payload)
        return [InterpretivePreferenceEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field="preference_file",
                message=str(exc),
            )
        )
        return []


def _extract_rows(payload: Any) -> list[Any]:
    """Extract raw D9 result rows from either a raw list or keyed object."""
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(
        payload.get("interpretive_preference_evaluations"),
        list,
    ):
        raw_rows = payload["interpretive_preference_evaluations"]
    else:
        raise ValueError(
            "D9 interpretive-preference payload must be a JSON list or object "
            "with 'interpretive_preference_evaluations'"
        )
    if not raw_rows:
        raise ValueError("D9 interpretive-preference payload must contain at least one row")
    return raw_rows


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[D9InterpretivePreferencePreflightError],
) -> None:
    """Append a hash-lock error when protocol and actual file hash diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            D9InterpretivePreferencePreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_evaluators_match_protocol(
    protocol: D9InterpretivePreferenceProtocolPackage,
    rows: list[InterpretivePreferenceEvaluation],
    errors: list[D9InterpretivePreferencePreflightError],
) -> None:
    """Append errors for evaluator drift from protocol metadata."""
    expected_types = set(protocol.evaluator_plan.evaluator_types)
    actual_types = {row.evaluator_type for row in rows}
    _check_set_equal("evaluator_types", expected_types, actual_types, errors)

    actual_evaluators = {row.evaluator for row in rows}
    if len(actual_evaluators) < protocol.evaluator_plan.planned_evaluator_count:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field="evaluator_count",
                message=(
                    "D9 result rows include "
                    f"{len(actual_evaluators)} unique evaluator(s), below planned "
                    f"count {protocol.evaluator_plan.planned_evaluator_count}"
                ),
            )
        )


def _check_targets_match_protocol(
    protocol: D9InterpretivePreferenceProtocolPackage,
    rows: list[InterpretivePreferenceEvaluation],
    errors: list[D9InterpretivePreferencePreflightError],
) -> None:
    """Append errors for target criterion or surface drift."""
    _check_set_equal(
        "target_criteria",
        set(protocol.target_criteria),
        {row.criterion for row in rows},
        errors,
    )
    _check_set_equal(
        "target_surfaces",
        set(protocol.target_surfaces),
        {row.surface for row in rows},
        errors,
    )


def _check_case_count_matches_protocol(
    protocol: D9InterpretivePreferenceProtocolPackage,
    rows: list[InterpretivePreferenceEvaluation],
    errors: list[D9InterpretivePreferencePreflightError],
) -> None:
    """Append an error when result rows undershoot planned case count."""
    case_count = len({row.case_id for row in rows})
    if case_count < protocol.planned_case_count:
        errors.append(
            D9InterpretivePreferencePreflightError(
                field="planned_case_count",
                message=(
                    "D9 result rows include "
                    f"{case_count} unique case(s), below planned count "
                    f"{protocol.planned_case_count}"
                ),
            )
        )


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[D9InterpretivePreferencePreflightError],
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
        D9InterpretivePreferencePreflightError(
            field=field,
            message="; ".join(parts),
        )
    )


def _build_report(
    *,
    protocol: D9InterpretivePreferenceProtocolPackage | None,
    preference_rows: list[InterpretivePreferenceEvaluation],
    errors: list[D9InterpretivePreferencePreflightError],
) -> D9InterpretivePreferencePreflightReport:
    """Build the final preflight report."""
    return D9InterpretivePreferencePreflightReport(
        schema_version=1,
        package_type="d9_interpretive_preference_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        target_criteria=list(protocol.target_criteria) if protocol is not None else [],
        target_surfaces=list(protocol.target_surfaces) if protocol is not None else [],
        non_inferiority_margin=(
            protocol.non_inferiority_margin if protocol is not None else None
        ),
        result_row_count=len(preference_rows),
        case_count=len({row.case_id for row in preference_rows}),
        evaluator_count=len({row.evaluator for row in preference_rows}),
        evaluator_types=sorted({row.evaluator_type for row in preference_rows}),
        errors=errors,
        caution=D9_INTERPRETIVE_PREFERENCE_PREFLIGHT_CAUTION,
    )
