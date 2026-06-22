"""Validation helpers for versioned D7 baseline prediction packages."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from qc_clean.core.d7_live_baseline import D7LiveBaselinePackage
from qc_clean.core.d7_retrieval import D7RetrievalBaselinePackage


D7BaselinePackage = D7RetrievalBaselinePackage | D7LiveBaselinePackage
D7_BASELINE_PACKAGE_TYPES = frozenset({
    "qualitative_coding.d7_retrieval_predictions",
    "qualitative_coding.d7_live_baseline_predictions",
})
D7_BASELINE_PACKAGE_CAUTION = (
    "D7 baseline package validation is package/provenance validation only; it is "
    "not held-out D7 evidence, live-baseline evidence, methodological-validity "
    "evidence, or superiority evidence."
)


class D7BaselinePackageValidationReport(BaseModel):
    """Machine-readable summary for a valid D7 baseline package."""

    schema_version: Literal[1] = Field(1, description="Report schema version")
    package_type: Literal["d7_baseline_package_validation"] = Field(
        "d7_baseline_package_validation",
        description="Report package type",
    )
    status: Literal["pass"] = Field(description="Validation status")
    prediction_package_type: str = Field(description="Validated prediction package type")
    project_id: str = Field(description="Project ID recorded in the prediction package")
    baseline_mode: str = Field(description="Retrieval or live baseline mode")
    baseline_count: int = Field(description="Number of baseline records in the package")
    baseline_names: list[str] = Field(description="Baseline names in package order")
    candidate_count: int = Field(description="Number of candidate anchors generated")
    selected_candidate_count: int | None = Field(
        default=None,
        description="Number of live-selected candidates, if this is a live package",
    )
    caution: str = Field(description="Claim-discipline caveat for validation reports")


def validate_d7_baseline_package_payload(payload: Any) -> D7BaselinePackage:
    """Validate a versioned D7 retrieval or live-baseline prediction package."""
    try:
        return D7RetrievalBaselinePackage.model_validate(payload)
    except ValidationError as retrieval_exc:
        try:
            return D7LiveBaselinePackage.model_validate(payload)
        except ValidationError as live_exc:
            raise ValueError(
                "Invalid D7 baseline package. Retrieval package error: "
                f"{retrieval_exc}; live baseline package error: {live_exc}"
            ) from live_exc


def build_d7_baseline_package_report(
    package: D7BaselinePackage,
) -> D7BaselinePackageValidationReport:
    """Return a compact validation report for a valid D7 baseline package."""
    baseline_names = [baseline.name for baseline in package.disconfirmation_baselines]
    if isinstance(package, D7RetrievalBaselinePackage):
        metadata = package.retrieval_run
        return D7BaselinePackageValidationReport(
            status="pass",
            prediction_package_type=package.package_type,
            project_id=metadata.project_id,
            baseline_mode=metadata.retrieval_mode,
            baseline_count=len(package.disconfirmation_baselines),
            baseline_names=baseline_names,
            candidate_count=metadata.candidate_count,
            selected_candidate_count=None,
            caution=D7_BASELINE_PACKAGE_CAUTION,
        )

    metadata = package.live_baseline_run
    return D7BaselinePackageValidationReport(
        status="pass",
        prediction_package_type=package.package_type,
        project_id=metadata.project_id,
        baseline_mode=metadata.baseline_mode,
        baseline_count=len(package.disconfirmation_baselines),
        baseline_names=baseline_names,
        candidate_count=metadata.candidate_count,
        selected_candidate_count=metadata.selected_candidate_count,
        caution=D7_BASELINE_PACKAGE_CAUTION,
    )


def d7_baselines_payload_for_scorecard(raw: Any) -> list[dict[str, Any]]:
    """Return scorecard-compatible D7 baseline rows from raw or package payloads."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        package_type = raw.get("package_type")
        if package_type in D7_BASELINE_PACKAGE_TYPES:
            package = validate_d7_baseline_package_payload(raw)
            return [
                baseline.model_dump(mode="json")
                for baseline in package.disconfirmation_baselines
            ]
        if package_type is not None:
            raise ValueError(f"Unsupported D7 baseline package_type: {package_type}")
        if isinstance(raw.get("disconfirmation_baselines"), list):
            return raw["disconfirmation_baselines"]
    raise ValueError(
        "D7 baselines payload must be a JSON list, a legacy object with a "
        "'disconfirmation_baselines' list, or a recognized versioned D7 baseline package"
    )
