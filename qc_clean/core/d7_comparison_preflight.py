"""Preflight D7 retrieval comparison packages against a registered protocol."""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.d7_comparison_protocol import (
    D7ComparisonProtocolPackage,
    D7ExpectedRetrievalPrediction,
    validate_d7_comparison_protocol_payload,
)
from qc_clean.core.d7_gold import D7GoldSetPackage, validate_d7_gold_set_payload
from qc_clean.core.d7_live_baseline import D7LiveBaselinePackage
from qc_clean.core.d7_retrieval import D7RetrievalBaselinePackage


D7PredictionPackage = D7RetrievalBaselinePackage | D7LiveBaselinePackage

D7_COMPARISON_PREFLIGHT_CAUTION = (
    "D7 comparison preflight is process metadata only; it is not a held-out D7 "
    "benchmark result, not live-baseline evidence, not methodological-validity "
    "evidence, and not superiority evidence."
)


class D7ComparisonPreflightError(BaseModel):
    """One D7 retrieval comparison preflight error."""

    field: str = Field(description="Field or cross-check that failed")
    message: str = Field(description="Human-readable failure description")


class D7ComparisonPreflightReport(BaseModel):
    """Machine-readable report for D7 retrieval comparison preflight."""

    schema_version: Literal[1] = Field(description="Preflight report schema version")
    package_type: Literal["d7_retrieval_comparison_preflight"] = Field(
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
    errors: list[D7ComparisonPreflightError] = Field(
        default_factory=list,
        description="Preflight failures",
    )
    caution: str = Field(description="Claim-discipline caveat for preflight reports")


def preflight_d7_comparison_payloads(
    protocol_payload: Any,
    gold_payload: Any,
    prediction_payloads: list[Any],
    *,
    prediction_file_sha256_by_baseline: Mapping[str, str] | None = None,
) -> D7ComparisonPreflightReport:
    """Cross-check D7 comparison gold/predictions against a registered protocol."""
    errors: list[D7ComparisonPreflightError] = []
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
    errors: list[D7ComparisonPreflightError],
) -> D7ComparisonProtocolPackage | None:
    """Validate protocol payload and append a preflight error on failure."""
    try:
        return validate_d7_comparison_protocol_payload(payload)
    except ValueError as exc:
        errors.append(D7ComparisonPreflightError(field="protocol", message=str(exc)))
        return None


def _validate_gold(
    payload: Any,
    errors: list[D7ComparisonPreflightError],
) -> D7GoldSetPackage | None:
    """Validate versioned D7 gold payload and append a preflight error on failure."""
    try:
        return validate_d7_gold_set_payload(payload)
    except ValueError as exc:
        errors.append(D7ComparisonPreflightError(field="gold", message=str(exc)))
        return None


def _validate_predictions(
    payloads: list[Any],
    errors: list[D7ComparisonPreflightError],
) -> list[D7PredictionPackage]:
    """Validate retrieval prediction packages and append preflight errors."""
    packages: list[D7PredictionPackage] = []
    if not payloads:
        errors.append(
            D7ComparisonPreflightError(
                field="predictions",
                message="At least one D7 retrieval prediction package is required",
            )
        )
        return packages
    for index, payload in enumerate(payloads, start=1):
        try:
            packages.append(D7RetrievalBaselinePackage.model_validate(payload))
            continue
        except ValidationError as retrieval_exc:
            try:
                packages.append(D7LiveBaselinePackage.model_validate(payload))
                continue
            except ValidationError as live_exc:
                message = (
                    "Invalid D7 prediction package. Retrieval package error: "
                    f"{retrieval_exc}; live baseline package error: {live_exc}"
                )
            errors.append(
                D7ComparisonPreflightError(
                    field=f"prediction_package[{index}]",
                    message=message,
                )
            )
    return packages


def _check_gold_matches_protocol(
    protocol: D7ComparisonProtocolPackage,
    gold: D7GoldSetPackage,
    errors: list[D7ComparisonPreflightError],
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
    protocol: D7ComparisonProtocolPackage,
    predictions: list[D7PredictionPackage],
    file_hashes_by_baseline: Mapping[str, str],
    errors: list[D7ComparisonPreflightError],
) -> None:
    """Append errors for prediction metadata/config drift from the protocol."""
    actual_by_name: dict[str, D7PredictionPackage] = {}
    duplicate_names: set[str] = set()
    for package in predictions:
        for baseline in package.disconfirmation_baselines:
            if baseline.name in actual_by_name:
                duplicate_names.add(baseline.name)
            actual_by_name[baseline.name] = package
    for name in sorted(duplicate_names):
        errors.append(
            D7ComparisonPreflightError(
                field="baseline_name",
                message=f"Duplicate D7 prediction baseline name: {name}",
            )
        )

    expected_by_name = {
        expected.baseline_name: expected for expected in protocol.expected_predictions
    }
    for name in sorted(set(expected_by_name) - set(actual_by_name)):
        errors.append(
            D7ComparisonPreflightError(
                field="baseline_name",
                message=f"Expected D7 prediction baseline is missing: {name}",
            )
        )
    for name in sorted(set(actual_by_name) - set(expected_by_name)):
        errors.append(
            D7ComparisonPreflightError(
                field="baseline_name",
                message=f"Unexpected D7 prediction baseline supplied: {name}",
            )
        )

    for name, expected in expected_by_name.items():
        package = actual_by_name.get(name)
        if package is None:
            continue
        _check_prediction_package(protocol, expected, package, file_hashes_by_baseline, errors)


def _check_prediction_package(
    protocol: D7ComparisonProtocolPackage,
    expected: D7ExpectedRetrievalPrediction,
    package: D7PredictionPackage,
    file_hashes_by_baseline: Mapping[str, str],
    errors: list[D7ComparisonPreflightError],
) -> None:
    """Append errors for one expected prediction package."""
    metadata = _prediction_metadata(package)
    _check_equal("project_id", protocol.project_id, metadata["project_id"], errors)
    _check_equal("corpus_sha256", protocol.corpus_sha256, metadata["corpus_sha256"], errors)
    _check_equal(
        "project_state_sha256",
        protocol.project_state_sha256,
        metadata["project_state_sha256"],
        errors,
    )
    _check_equal("baseline_mode", expected.baseline_mode, metadata["baseline_mode"], errors)
    _check_equal("model", expected.model, metadata["model"], errors)
    _check_equal("retrieval_mode", expected.retrieval_mode, metadata["retrieval_mode"], errors)
    _check_equal(
        "candidates_per_claim",
        expected.candidates_per_claim,
        metadata["candidates_per_claim"],
        errors,
    )
    _check_equal("max_targets", expected.max_targets, metadata["max_targets"], errors)
    _check_equal("embedding_model", expected.embedding_model, metadata["embedding_model"], errors)
    _check_equal(
        "embedding_dimensions",
        expected.embedding_dimensions,
        metadata["embedding_dimensions"],
        errors,
    )
    _check_equal("trace_id", expected.trace_id, metadata["trace_id"], errors)
    _check_equal("max_budget", expected.max_budget, metadata["max_budget"], errors)
    if expected.prediction_file_sha256 is not None:
        actual_hash = file_hashes_by_baseline.get(expected.baseline_name)
        if actual_hash is None:
            errors.append(
                D7ComparisonPreflightError(
                    field="prediction_file_sha256",
                    message=(
                        f"Prediction file hash was not supplied for baseline "
                        f"{expected.baseline_name!r}"
                    ),
                )
            )
        elif actual_hash.lower() != expected.prediction_file_sha256.lower():
            errors.append(
                D7ComparisonPreflightError(
                    field="prediction_file_sha256",
                    message=(
                        f"Protocol prediction_file_sha256 for {expected.baseline_name!r} "
                        f"{expected.prediction_file_sha256!r} does not match actual "
                        f"prediction file hash {actual_hash!r}"
                    ),
                )
            )


def _prediction_metadata(package: D7PredictionPackage) -> dict[str, Any]:
    """Return normalized metadata shared by retrieval and live prediction packages."""
    if isinstance(package, D7RetrievalBaselinePackage):
        metadata = package.retrieval_run
        return {
            "baseline_mode": "retrieval",
            "model": None,
            "project_id": metadata.project_id,
            "project_state_sha256": metadata.project_state_sha256,
            "corpus_sha256": metadata.corpus_sha256,
            "retrieval_mode": metadata.retrieval_mode,
            "embedding_model": metadata.embedding_model,
            "embedding_dimensions": metadata.embedding_dimensions,
            "max_targets": metadata.max_targets,
            "candidates_per_claim": metadata.candidates_per_claim,
            "trace_id": metadata.trace_id,
            "max_budget": metadata.max_budget,
        }
    metadata = package.live_baseline_run
    return {
        "baseline_mode": metadata.baseline_mode,
        "model": metadata.model,
        "project_id": metadata.project_id,
        "project_state_sha256": metadata.project_state_sha256,
        "corpus_sha256": metadata.corpus_sha256,
        "retrieval_mode": metadata.retrieval_mode,
        "embedding_model": metadata.embedding_model,
        "embedding_dimensions": metadata.embedding_dimensions,
        "max_targets": metadata.max_targets,
        "candidates_per_claim": metadata.candidates_per_claim,
        "trace_id": metadata.trace_id,
        "max_budget": metadata.max_budget,
    }


def _check_equal(
    field: str,
    expected: Any,
    actual: Any,
    errors: list[D7ComparisonPreflightError],
) -> None:
    """Append a field mismatch error when values differ."""
    if expected != actual:
        errors.append(
            D7ComparisonPreflightError(
                field=field,
                message=f"Protocol {field} {expected!r} does not match supplied {actual!r}",
            )
        )


def _build_report(
    *,
    protocol: D7ComparisonProtocolPackage | None,
    gold: D7GoldSetPackage | None,
    predictions: list[D7PredictionPackage],
    errors: list[D7ComparisonPreflightError],
) -> D7ComparisonPreflightReport:
    """Build the final preflight report."""
    return D7ComparisonPreflightReport(
        schema_version=1,
        package_type="d7_retrieval_comparison_preflight",
        status="fail" if errors else "pass",
        protocol_id=protocol.protocol_id if protocol is not None else None,
        project_id=protocol.project_id if protocol is not None else None,
        gold_set_id=gold.gold_set_id if gold is not None else None,
        split=protocol.split if protocol is not None else None,
        expected_prediction_count=(
            len(protocol.expected_predictions) if protocol is not None else 0
        ),
        prediction_package_count=len(predictions),
        baseline_count=sum(len(package.disconfirmation_baselines) for package in predictions),
        errors=errors,
        caution=D7_COMPARISON_PREFLIGHT_CAUTION,
    )
