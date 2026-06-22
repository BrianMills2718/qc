"""Preflight D8 GT-fidelity result files against registered protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.bench import GTFidelityEvaluation
from qc_clean.core.d8_gt_fidelity_protocol import (
    D8GTFidelityProtocolPackage,
    validate_d8_gt_fidelity_protocol_payload,
)


D8_GT_FIDELITY_PREFLIGHT_CAUTION = (
    "D8 GT-fidelity preflight is process/provenance metadata only; it is not "
    "expert-rubric acceptance, not methodological-saturation evidence, not "
    "full grounded-theory evidence, and not SOTA evidence."
)


class D8GTFidelityPreflightError(BaseModel):
    """One D8 GT-fidelity protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D8GTFidelityPreflightReport(BaseModel):
    """Machine-readable report for D8 GT-fidelity protocol/result preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d8_gt_fidelity_protocol_result_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    rubric_metrics: list[str] = Field(description="Protocol D8 rubric metrics")
    target_scopes: list[str] = Field(description="Protocol D8 target scopes")
    result_row_count: int = Field(description="Number of validated D8 result rows")
    evaluator_count: int = Field(description="Number of unique evaluators in result rows")
    evaluator_types: list[str] = Field(description="Evaluator types found in result rows")
    artifact_count: int = Field(description="Number of unique targeted artifact IDs")
    errors: list[D8GTFidelityPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d8_gt_fidelity_payloads(
    protocol_payload: Any,
    gt_fidelity_payload: Any | None = None,
    *,
    gt_fidelity_file_sha256: str | None = None,
) -> D8GTFidelityPreflightReport:
    """Cross-check D8 GT-fidelity result rows against a registered protocol."""
    errors: list[D8GTFidelityPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    gt_fidelity_rows = _validate_gt_fidelity_payload(gt_fidelity_payload, errors)

    if protocol is not None and gt_fidelity_rows:
        _check_hash_lock(
            "gt_fidelity_file_sha256",
            protocol.outcome_file_sha256,
            gt_fidelity_file_sha256,
            errors,
        )
        _check_evaluators_match_protocol(protocol, gt_fidelity_rows, errors)
        _check_scopes_match_protocol(protocol, gt_fidelity_rows, errors)

    return _build_report(
        protocol=protocol,
        gt_fidelity_rows=gt_fidelity_rows,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[D8GTFidelityPreflightError],
) -> D8GTFidelityProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d8_gt_fidelity_protocol_payload(payload)
    except ValueError as exc:
        errors.append(D8GTFidelityPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_gt_fidelity_payload(
    payload: Any | None,
    errors: list[D8GTFidelityPreflightError],
) -> list[GTFidelityEvaluation]:
    """Validate supplied D8 GT-fidelity rows and append errors on failure."""
    if payload is None:
        errors.append(
            D8GTFidelityPreflightError(
                field="gt_fidelity_file",
                message="D8 preflight requires a GT-fidelity result file",
            )
        )
        return []
    try:
        raw_rows = _extract_rows(payload)
        return [GTFidelityEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(D8GTFidelityPreflightError(field="gt_fidelity_file", message=str(exc)))
        return []


def _extract_rows(payload: Any) -> list[Any]:
    """Extract raw D8 result rows from either a raw list or keyed object."""
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(
        payload.get("gt_fidelity_evaluations"),
        list,
    ):
        raw_rows = payload["gt_fidelity_evaluations"]
    else:
        raise ValueError(
            "D8 GT-fidelity payload must be a JSON list or object with "
            "'gt_fidelity_evaluations'"
        )
    if not raw_rows:
        raise ValueError("D8 GT-fidelity payload must contain at least one row")
    return raw_rows


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[D8GTFidelityPreflightError],
) -> None:
    """Append a hash-lock error when protocol and actual file hash diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            D8GTFidelityPreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            D8GTFidelityPreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_evaluators_match_protocol(
    protocol: D8GTFidelityProtocolPackage,
    rows: list[GTFidelityEvaluation],
    errors: list[D8GTFidelityPreflightError],
) -> None:
    """Append errors for evaluator drift from protocol metadata."""
    expected_types = set(protocol.evaluator_plan.evaluator_types)
    actual_types = {row.evaluator_type for row in rows}
    _check_set_equal("evaluator_types", expected_types, actual_types, errors)

    actual_evaluators = {row.evaluator for row in rows}
    if len(actual_evaluators) < protocol.evaluator_plan.planned_evaluator_count:
        errors.append(
            D8GTFidelityPreflightError(
                field="evaluator_count",
                message=(
                    "D8 result rows include "
                    f"{len(actual_evaluators)} unique evaluator(s), below planned "
                    f"count {protocol.evaluator_plan.planned_evaluator_count}"
                ),
            )
        )


def _check_scopes_match_protocol(
    protocol: D8GTFidelityProtocolPackage,
    rows: list[GTFidelityEvaluation],
    errors: list[D8GTFidelityPreflightError],
) -> None:
    """Append errors for target-scope drift and missing artifact IDs."""
    expected_scopes = set(protocol.target_scopes)
    actual_scopes = {row.scope for row in rows}
    _check_set_equal("target_scopes", expected_scopes, actual_scopes, errors)

    missing_artifact_ids = [
        f"{row.evaluator}:{row.scope}"
        for row in rows
        if row.scope != "grounded_theory_pipeline" and row.artifact_id is None
    ]
    if missing_artifact_ids:
        errors.append(
            D8GTFidelityPreflightError(
                field="targeted_scope_artifact_id",
                message=(
                    "D8 targeted-scope result rows require artifact_id; missing for "
                    + ", ".join(sorted(missing_artifact_ids))
                ),
            )
        )


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[D8GTFidelityPreflightError],
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
    errors.append(D8GTFidelityPreflightError(field=field, message="; ".join(parts)))


def _build_report(
    *,
    protocol: D8GTFidelityProtocolPackage | None,
    gt_fidelity_rows: list[GTFidelityEvaluation],
    errors: list[D8GTFidelityPreflightError],
) -> D8GTFidelityPreflightReport:
    """Build the final preflight report."""
    return D8GTFidelityPreflightReport(
        schema_version=1,
        package_type="d8_gt_fidelity_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        rubric_metrics=list(protocol.rubric_metrics) if protocol is not None else [],
        target_scopes=list(protocol.target_scopes) if protocol is not None else [],
        result_row_count=len(gt_fidelity_rows),
        evaluator_count=len({row.evaluator for row in gt_fidelity_rows}),
        evaluator_types=sorted({row.evaluator_type for row in gt_fidelity_rows}),
        artifact_count=len(
            {row.artifact_id for row in gt_fidelity_rows if row.artifact_id is not None}
        ),
        errors=errors,
        caution=D8_GT_FIDELITY_PREFLIGHT_CAUTION,
    )
