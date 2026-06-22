"""Validation helpers for versioned D3 baseline prediction packages."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from qc_clean.core.bench import ApplicationBaselinePrediction


D3_BASELINE_PACKAGE_TYPE = "qualitative_coding.d3_application_baseline_predictions"
D3_BASELINE_PACKAGE_TYPES = frozenset({D3_BASELINE_PACKAGE_TYPE})
D3_BASELINE_PACKAGE_CAUTION = (
    "D3 baseline package validation is package/provenance validation only; it is "
    "not held-out D3 evidence, live-baseline evidence, methodological-validity "
    "evidence, or superiority evidence."
)


class D3BaselineRunMetadata(BaseModel):
    """Run metadata for a D3 application-baseline prediction package."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(description="Project ID the baseline predictions target")
    baseline_mode: str = Field(description="Stable baseline-generation mode")
    generated_at: str = Field(
        default="",
        description="Optional timestamp for when the baseline package was generated",
    )
    model_name: str | None = Field(
        default=None,
        description="Optional model name used to generate baseline predictions",
    )
    application_count: int = Field(
        default=0,
        description="Total number of predicted code applications in this package",
    )
    notes: str = Field(default="", description="Optional package-generation notes")

    @model_validator(mode="after")
    def require_metadata(self) -> "D3BaselineRunMetadata":
        """Require stable metadata before baseline rows can be treated as a package."""
        if not self.project_id.strip():
            raise ValueError("D3 baseline project_id must be non-empty")
        if not self.baseline_mode.strip():
            raise ValueError("D3 baseline baseline_mode must be non-empty")
        if self.application_count < 0:
            raise ValueError("D3 baseline application_count must be non-negative")
        self.project_id = self.project_id.strip()
        self.baseline_mode = self.baseline_mode.strip()
        return self


class D3BaselinePackage(BaseModel):
    """Versioned D3 application-baseline prediction package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="D3 baseline package schema version")
    package_type: Literal[
        "qualitative_coding.d3_application_baseline_predictions"
    ] = Field(description="D3 baseline package type")
    application_baseline_run: D3BaselineRunMetadata = Field(
        description="Baseline generation metadata"
    )
    application_baselines: list[ApplicationBaselinePrediction] = Field(
        description="Baseline-predicted code applications using the D3 exact anchor schema"
    )

    @model_validator(mode="after")
    def require_package_invariants(self) -> "D3BaselinePackage":
        """Reject empty packages and duplicate baseline names."""
        if not self.application_baselines:
            raise ValueError("D3 baseline package requires at least one application_baselines row")
        names = [baseline.name for baseline in self.application_baselines]
        duplicates = sorted(name for name in set(names) if names.count(name) > 1)
        if duplicates:
            raise ValueError("Duplicate D3 baseline name(s): " + ", ".join(duplicates))
        actual_application_count = sum(
            len(baseline.code_applications)
            for baseline in self.application_baselines
        )
        expected_count = self.application_baseline_run.application_count
        if expected_count != actual_application_count:
            raise ValueError(
                "D3 baseline application_count does not match baseline rows: "
                f"expected {expected_count}, found {actual_application_count}"
            )
        return self


class D3BaselinePackageValidationReport(BaseModel):
    """Machine-readable summary for a valid D3 baseline package."""

    schema_version: Literal[1] = Field(1, description="Report schema version")
    package_type: Literal["d3_baseline_package_validation"] = Field(
        "d3_baseline_package_validation",
        description="Report package type",
    )
    status: Literal["pass"] = Field(description="Validation status")
    prediction_package_type: str = Field(description="Validated prediction package type")
    project_id: str = Field(description="Project ID recorded in the baseline package")
    baseline_mode: str = Field(description="Baseline generation mode")
    baseline_count: int = Field(description="Number of baseline records in the package")
    baseline_names: list[str] = Field(description="Baseline names in package order")
    application_count: int = Field(description="Number of predicted applications")
    caution: str = Field(description="Claim-discipline caveat for validation reports")


def validate_d3_baseline_package_payload(payload: Any) -> D3BaselinePackage:
    """Validate a versioned D3 application-baseline prediction package."""
    try:
        return D3BaselinePackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 baseline package: {exc}") from exc


def build_d3_baseline_package_report(
    package: D3BaselinePackage,
) -> D3BaselinePackageValidationReport:
    """Return a compact validation report for a valid D3 baseline package."""
    return D3BaselinePackageValidationReport(
        status="pass",
        prediction_package_type=package.package_type,
        project_id=package.application_baseline_run.project_id,
        baseline_mode=package.application_baseline_run.baseline_mode,
        baseline_count=len(package.application_baselines),
        baseline_names=[baseline.name for baseline in package.application_baselines],
        application_count=package.application_baseline_run.application_count,
        caution=D3_BASELINE_PACKAGE_CAUTION,
    )


def d3_baselines_payload_for_scorecard(raw: Any) -> list[dict[str, Any]]:
    """Return scorecard-compatible D3 baseline rows from raw or package payloads."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        package_type = raw.get("package_type")
        if package_type in D3_BASELINE_PACKAGE_TYPES:
            package = validate_d3_baseline_package_payload(raw)
            return [
                baseline.model_dump(mode="json")
                for baseline in package.application_baselines
            ]
        if package_type is not None:
            raise ValueError(f"Unsupported D3 baseline package_type: {package_type}")
        if isinstance(raw.get("application_baselines"), list):
            return raw["application_baselines"]
    raise ValueError(
        "D3 baselines payload must be a JSON list, a legacy object with an "
        "'application_baselines' list, or a recognized versioned D3 baseline package"
    )
