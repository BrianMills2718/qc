"""Preflight D3 baseline comparison packages against a registered protocol."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field

from qc_clean.core.d3_baseline_package import (
    D3BaselinePackage,
    validate_d3_baseline_package_payload,
)
from qc_clean.core.d3_comparison_protocol import (
    D3ComparisonProtocolPackage,
    D3ExpectedApplicationBaseline,
    validate_d3_comparison_protocol_payload,
)
from qc_clean.core.d3_gold import D3GoldSetPackage, validate_d3_gold_set_payload


D3_COMPARISON_PREFLIGHT_CAUTION = (
    "D3 comparison preflight is process metadata only; it is not a held-out D3 "
    "benchmark result, not expert-parity evidence, not methodological-validity "
    "evidence, and not superiority evidence."
)


class D3ComparisonPreflightError(BaseModel):
    """One D3 baseline comparison preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D3ComparisonPreflightReport(BaseModel):
    """Machine-readable report for D3 baseline comparison preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d3_baseline_comparison_preflight"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall preflight status")
    protocol_id: str | None = Field(default=None, description="Protocol ID when available")
    project_id: str | None = Field(default=None, description="Project ID when available")
    gold_set_id: str | None = Field(default=None, description="Gold-set ID when available")
    split: str | None = Field(default=None, description="Comparison split when available")
    expected_prediction_count: int = Field(description="Number of expected baseline predictions")
    prediction_package_count: int = Field(description="Number of prediction packages supplied")
    baseline_count: int = Field(description="Number of actual baseline records supplied")
    errors: list[D3ComparisonPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d3_comparison_payloads(
    protocol_payload: Any,
    gold_payload: Any,
    prediction_payloads: list[Any],
    *,
    prediction_file_sha256_by_baseline: Mapping[str, str] | None = None,
) -> D3ComparisonPreflightReport:
    """Cross-check D3 comparison gold/predictions against a registered protocol."""
    errors: list[D3ComparisonPreflightError] = []
    protocol = _validate_protocol(protocol_payload, errors)
    gold = _validate_gold(gold_payload, errors)
    predictions = _validate_predictions(prediction_payloads, errors)
    if protocol is not None and gold is not None:
        _check_gold_matches_protocol(protocol, gold, errors)
    if protocol is not None and predictions:
        _check_predictions_match_protocol(
            protocol,
            predictions,
            prediction_file_sha256_by_baseline or {},
            errors,
        )
    return _build_report(
        protocol=protocol,
        gold=gold,
        predictions=predictions,
        errors=errors,
    )


def _validate_protocol(
    payload: Any,
    errors: list[D3ComparisonPreflightError],
) -> D3ComparisonProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d3_comparison_protocol_payload(payload)
    except ValueError as exc:
        errors.append(D3ComparisonPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_gold(
    payload: Any,
    errors: list[D3ComparisonPreflightError],
) -> D3GoldSetPackage | None:
    """Validate versioned D3 gold payload and append a preflight error on failure."""
    try:
        return validate_d3_gold_set_payload(payload)
    except ValueError as exc:
        errors.append(D3ComparisonPreflightError(field="gold", message=str(exc)))
        return None


def _validate_predictions(
    payloads: list[Any],
    errors: list[D3ComparisonPreflightError],
) -> list[D3BaselinePackage]:
    """Validate D3 baseline prediction packages and append preflight errors."""
    packages: list[D3BaselinePackage] = []
    if not payloads:
        errors.append(
            D3ComparisonPreflightError(
                field="predictions",
                message="At least one D3 baseline prediction package is required",
            )
        )
        return packages
    for index, payload in enumerate(payloads, start=1):
        try:
            packages.append(validate_d3_baseline_package_payload(payload))
        except ValueError as exc:
            errors.append(
                D3ComparisonPreflightError(
                    field=f"prediction_package[{index}]",
                    message=str(exc),
                )
            )
    return packages


def _check_gold_matches_protocol(
    protocol: D3ComparisonProtocolPackage,
    gold: D3GoldSetPackage,
    errors: list[D3ComparisonPreflightError],
) -> None:
    """Append errors for gold package metadata drift from the protocol."""
    _check_equal("gold_set_id", protocol.gold_set_id, gold.gold_set_id, errors)
    _check_equal("dataset_name", protocol.dataset_name, gold.dataset_name, errors)
    _check_equal("split", protocol.split, gold.split, errors)
    _check_equal("corpus_sha256", protocol.corpus_sha256, gold.corpus_sha256, errors)
    _check_equal(
        "project_state_sha256",
        protocol.project_state_sha256,
        gold.project_state_sha256,
        errors,
    )
    _check_equal("prompt_frozen", protocol.prompt_frozen, gold.prompt_frozen, errors)
    _check_equal(
        "contamination_checked",
        protocol.contamination_checked,
        gold.contamination_checked,
        errors,
    )


def _check_predictions_match_protocol(
    protocol: D3ComparisonProtocolPackage,
    predictions: list[D3BaselinePackage],
    file_hashes_by_baseline: Mapping[str, str],
    errors: list[D3ComparisonPreflightError],
) -> None:
    """Append errors for prediction metadata/config drift from the protocol."""
    actual_by_name: dict[str, tuple[D3BaselinePackage, int]] = {}
    duplicate_names: set[str] = set()
    for package in predictions:
        for index, baseline in enumerate(package.application_baselines):
            if baseline.name in actual_by_name:
                duplicate_names.add(baseline.name)
            actual_by_name[baseline.name] = (package, index)
    for name in sorted(duplicate_names):
        errors.append(
            D3ComparisonPreflightError(
                field="baseline_name",
                message=f"Duplicate D3 prediction baseline name: {name}",
            )
        )

    expected_by_name = {
        expected.baseline_name: expected for expected in protocol.expected_predictions
    }
    for name in sorted(set(expected_by_name) - set(actual_by_name)):
        errors.append(
            D3ComparisonPreflightError(
                field="baseline_name",
                message=f"Expected D3 prediction baseline is missing: {name}",
            )
        )
    for name in sorted(set(actual_by_name) - set(expected_by_name)):
        errors.append(
            D3ComparisonPreflightError(
                field="baseline_name",
                message=f"Unexpected D3 prediction baseline supplied: {name}",
            )
        )

    for name, expected in expected_by_name.items():
        actual = actual_by_name.get(name)
        if actual is None:
            continue
        package, baseline_index = actual
        _check_prediction_baseline(
            protocol,
            expected,
            package,
            baseline_index,
            file_hashes_by_baseline,
            errors,
        )


def _check_prediction_baseline(
    protocol: D3ComparisonProtocolPackage,
    expected: D3ExpectedApplicationBaseline,
    package: D3BaselinePackage,
    baseline_index: int,
    file_hashes_by_baseline: Mapping[str, str],
    errors: list[D3ComparisonPreflightError],
) -> None:
    """Append errors for one expected D3 baseline prediction."""
    run = package.application_baseline_run
    baseline = package.application_baselines[baseline_index]
    _check_equal("project_id", protocol.project_id, run.project_id, errors)
    _check_equal("baseline_mode", expected.baseline_mode, run.baseline_mode, errors)
    if expected.model_name is not None:
        _check_equal("model_name", expected.model_name, run.model_name, errors)
    _check_equal(
        "application_count",
        expected.application_count,
        len(baseline.code_applications),
        errors,
    )
    if expected.prediction_file_sha256 is not None:
        actual_hash = file_hashes_by_baseline.get(expected.baseline_name)
        if actual_hash is None:
            errors.append(
                D3ComparisonPreflightError(
                    field="prediction_file_sha256",
                    message=(
                        "No SHA-256 hash was supplied for D3 baseline "
                        f"{expected.baseline_name}"
                    ),
                )
            )
        else:
            _check_equal(
                "prediction_file_sha256",
                expected.prediction_file_sha256,
                actual_hash,
                errors,
            )


def _build_report(
    *,
    protocol: D3ComparisonProtocolPackage | None,
    gold: D3GoldSetPackage | None,
    predictions: list[D3BaselinePackage],
    errors: list[D3ComparisonPreflightError],
) -> D3ComparisonPreflightReport:
    """Build the final pass/fail preflight report."""
    baseline_count = sum(len(package.application_baselines) for package in predictions)
    return D3ComparisonPreflightReport(
        schema_version=1,
        package_type="d3_baseline_comparison_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        gold_set_id=gold.gold_set_id if gold is not None else None,
        split=protocol.split if protocol is not None else None,
        expected_prediction_count=(
            len(protocol.expected_predictions) if protocol is not None else 0
        ),
        prediction_package_count=len(predictions),
        baseline_count=baseline_count,
        errors=errors,
        caution=D3_COMPARISON_PREFLIGHT_CAUTION,
    )


def _check_equal(
    field: str,
    expected: Any,
    actual: Any,
    errors: list[D3ComparisonPreflightError],
) -> None:
    """Append a standardized mismatch error."""
    if expected != actual:
        errors.append(
            D3ComparisonPreflightError(
                field=field,
                message=f"Expected {field}={expected!r}, found {actual!r}",
            )
        )
