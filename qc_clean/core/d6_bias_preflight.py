"""Preflight D6 bias result files against registered protocols."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.bench import BiasCounterfactualEvaluation, BiasStratifiedEvaluation
from qc_clean.core.d6_bias_protocol import (
    D6BiasProtocolPackage,
    validate_d6_bias_protocol_payload,
)


D6_BIAS_PREFLIGHT_CAUTION = (
    "D6 bias preflight is process/provenance metadata only; it is not a "
    "populated bias audit, not causal proof, not bias-free evidence, not "
    "methodological-validity evidence, and not a benchmark result."
)


class D6BiasPreflightError(BaseModel):
    """One D6 bias protocol/result preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D6BiasPreflightReport(BaseModel):
    """Machine-readable report for D6 bias protocol/result preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d6_bias_protocol_result_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    split: str | None = Field(default=None, description="Protocol split when available")
    dimensions: list[str] = Field(description="Protocol D6 dimensions when available")
    stratified_row_count: int = Field(description="Number of validated stratified rows")
    counterfactual_row_count: int = Field(description="Number of validated counterfactual rows")
    errors: list[D6BiasPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d6_bias_payloads(
    protocol_payload: Any,
    stratified_payload: Any | None = None,
    counterfactual_payload: Any | None = None,
    *,
    stratified_file_sha256: str | None = None,
    counterfactual_file_sha256: str | None = None,
) -> D6BiasPreflightReport:
    """Cross-check D6 result files against a registered bias-audit protocol."""
    errors: list[D6BiasPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    stratified_rows = _validate_stratified_payload(stratified_payload, errors)
    counterfactual_rows = _validate_counterfactual_payload(counterfactual_payload, errors)

    if protocol is not None:
        _check_result_presence(
            protocol,
            stratified_payload=stratified_payload,
            counterfactual_payload=counterfactual_payload,
            errors=errors,
        )
        if stratified_rows:
            _check_stratified_matches_protocol(
                protocol,
                stratified_rows,
                stratified_file_sha256,
                errors,
            )
        if counterfactual_rows:
            _check_counterfactual_matches_protocol(
                protocol,
                counterfactual_rows,
                counterfactual_file_sha256,
                errors,
            )

    return _build_report(
        protocol=protocol,
        stratified_rows=stratified_rows,
        counterfactual_rows=counterfactual_rows,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[D6BiasPreflightError],
) -> D6BiasProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d6_bias_protocol_payload(payload)
    except ValueError as exc:
        errors.append(D6BiasPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_stratified_payload(
    payload: Any | None,
    errors: list[D6BiasPreflightError],
) -> list[BiasStratifiedEvaluation]:
    """Validate supplied stratified rows and append a preflight error on failure."""
    if payload is None:
        return []
    try:
        raw_rows = _extract_rows(
            payload,
            key="bias_stratified_evaluations",
            label="stratified",
        )
        return [BiasStratifiedEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(D6BiasPreflightError(field="stratified_file", message=str(exc)))
        return []


def _validate_counterfactual_payload(
    payload: Any | None,
    errors: list[D6BiasPreflightError],
) -> list[BiasCounterfactualEvaluation]:
    """Validate supplied counterfactual rows and append a preflight error on failure."""
    if payload is None:
        return []
    try:
        raw_rows = _extract_rows(
            payload,
            key="bias_counterfactual_evaluations",
            label="counterfactual",
        )
        return [BiasCounterfactualEvaluation.model_validate(row) for row in raw_rows]
    except (TypeError, ValueError, ValidationError) as exc:
        errors.append(D6BiasPreflightError(field="counterfactual_file", message=str(exc)))
        return []


def _extract_rows(payload: Any, *, key: str, label: str) -> list[Any]:
    """Extract raw result rows from either a raw list or keyed object."""
    if isinstance(payload, list):
        raw_rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get(key), list):
        raw_rows = payload[key]
    else:
        raise ValueError(f"D6 bias {label} payload must be a JSON list or object with '{key}'")
    if not raw_rows:
        raise ValueError(f"D6 bias {label} payload must contain at least one row")
    return raw_rows


def _check_result_presence(
    protocol: D6BiasProtocolPackage,
    *,
    stratified_payload: Any | None,
    counterfactual_payload: Any | None,
    errors: list[D6BiasPreflightError],
) -> None:
    """Append errors for missing or unexpected result files."""
    dimensions = set(protocol.dimensions)
    if "bias_stratified_d6" in dimensions:
        if stratified_payload is None:
            errors.append(
                D6BiasPreflightError(
                    field="stratified_file",
                    message="D6 protocol requires a stratified result file",
                )
            )
    elif stratified_payload is not None:
        errors.append(
            D6BiasPreflightError(
                field="stratified_file",
                message=(
                    "Stratified result file was supplied but bias_stratified_d6 "
                    "is not configured"
                ),
            )
        )

    if "bias_counterfactual_d6" in dimensions:
        if counterfactual_payload is None:
            errors.append(
                D6BiasPreflightError(
                    field="counterfactual_file",
                    message="D6 protocol requires a counterfactual result file",
                )
            )
    elif counterfactual_payload is not None:
        errors.append(
            D6BiasPreflightError(
                field="counterfactual_file",
                message=(
                    "Counterfactual result file was supplied but "
                    "bias_counterfactual_d6 is not configured"
                ),
            )
        )


def _check_stratified_matches_protocol(
    protocol: D6BiasProtocolPackage,
    rows: list[BiasStratifiedEvaluation],
    file_sha256: str | None,
    errors: list[D6BiasPreflightError],
) -> None:
    """Append errors for stratified result drift from protocol metadata."""
    strategy = protocol.stratified_strategy
    if strategy is None:
        return
    _check_hash_lock(
        "stratified_file_sha256",
        strategy.outcome_file_sha256,
        file_sha256,
        errors,
    )
    expected_attributes = set(strategy.attributes)
    actual_attributes = {row.attribute for row in rows}
    _check_set_equal(
        "stratified_attributes",
        expected_attributes,
        actual_attributes,
        errors,
    )
    expected_surfaces = set(strategy.surfaces)
    actual_surfaces = {row.surface for row in rows}
    _check_set_equal("stratified_surfaces", expected_surfaces, actual_surfaces, errors)


def _check_counterfactual_matches_protocol(
    protocol: D6BiasProtocolPackage,
    rows: list[BiasCounterfactualEvaluation],
    file_sha256: str | None,
    errors: list[D6BiasPreflightError],
) -> None:
    """Append errors for counterfactual result drift from protocol metadata."""
    strategy = protocol.counterfactual_strategy
    if strategy is None:
        return
    _check_hash_lock(
        "counterfactual_file_sha256",
        strategy.outcome_file_sha256,
        file_sha256,
        errors,
    )
    expected_attributes = set(protocol.attribute_policy.attributes)
    actual_attributes = {row.attribute for row in rows}
    unexpected_attributes = sorted(actual_attributes - expected_attributes)
    if unexpected_attributes:
        errors.append(
            D6BiasPreflightError(
                field="counterfactual_attributes",
                message=(
                    "Counterfactual rows contain unregistered attribute(s): "
                    + ", ".join(unexpected_attributes)
                ),
            )
        )


def _check_hash_lock(
    field: str,
    expected_hash: str | None,
    actual_hash: str | None,
    errors: list[D6BiasPreflightError],
) -> None:
    """Append hash-lock errors when protocol and actual file hashes diverge."""
    if expected_hash is None:
        return
    if actual_hash is None:
        errors.append(
            D6BiasPreflightError(
                field=field,
                message=f"Protocol {field} is set but actual file hash was not supplied",
            )
        )
        return
    if expected_hash.lower() != actual_hash.lower():
        errors.append(
            D6BiasPreflightError(
                field=field,
                message=(
                    f"Protocol {field} {expected_hash!r} does not match actual "
                    f"file hash {actual_hash!r}"
                ),
            )
        )


def _check_set_equal(
    field: str,
    expected: set[str],
    actual: set[str],
    errors: list[D6BiasPreflightError],
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
    errors.append(D6BiasPreflightError(field=field, message="; ".join(parts)))


def _build_report(
    *,
    protocol: D6BiasProtocolPackage | None,
    stratified_rows: list[BiasStratifiedEvaluation],
    counterfactual_rows: list[BiasCounterfactualEvaluation],
    errors: list[D6BiasPreflightError],
) -> D6BiasPreflightReport:
    """Build the final preflight report."""
    return D6BiasPreflightReport(
        schema_version=1,
        package_type="d6_bias_protocol_result_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        split=protocol.split if protocol is not None else None,
        dimensions=list(protocol.dimensions) if protocol is not None else [],
        stratified_row_count=len(stratified_rows),
        counterfactual_row_count=len(counterfactual_rows),
        errors=errors,
        caution=D6_BIAS_PREFLIGHT_CAUTION,
    )
