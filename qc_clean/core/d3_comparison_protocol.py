"""D3 application-baseline comparison protocol package contracts."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D3_COMPARISON_PROTOCOL_CAUTION = (
    "D3 comparison protocol validation is process metadata only; it is not "
    "held-out D3 evidence, expert-parity evidence, methodological-validity "
    "evidence, superiority evidence, or SOTA evidence."
)

D3ComparisonMetric = Literal[
    "recall",
    "precision",
    "f1",
    "mean_best_gold_iou",
    "mean_best_predicted_iou",
    "mean_best_gold_modified_hausdorff_distance",
    "mean_best_predicted_modified_hausdorff_distance",
]
D3ComparisonOperator = Literal[">=", ">", "<=", "<", "=="]
D3MetricCriteriaStatus = Literal["pass", "fail", "missing"]

_PROPORTION_METRICS: set[D3ComparisonMetric] = {
    "recall",
    "precision",
    "f1",
    "mean_best_gold_iou",
    "mean_best_predicted_iou",
}
_SPAN_OVERLAP_METRICS: set[D3ComparisonMetric] = {
    "mean_best_gold_iou",
    "mean_best_predicted_iou",
    "mean_best_gold_modified_hausdorff_distance",
    "mean_best_predicted_modified_hausdorff_distance",
}


class D3ExpectedApplicationBaseline(BaseModel):
    """One expected D3 application-baseline prediction package/baseline."""

    model_config = ConfigDict(extra="forbid")

    baseline_name: str = Field(description="Expected baseline record name")
    baseline_mode: str = Field(description="Expected baseline-generation mode")
    model_name: str | None = Field(
        default=None,
        description="Optional expected model or tool name for this baseline",
    )
    application_count: int = Field(
        description="Expected number of predicted code applications for this baseline"
    )
    trace_id: str | None = Field(
        default=None,
        description="Optional expected trace ID for generated baseline predictions",
    )
    max_budget: float | None = Field(
        default=None,
        description="Optional maximum budget registered for baseline generation",
    )
    prediction_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hash lock for the baseline prediction file",
    )

    @model_validator(mode="after")
    def require_expected_prediction_invariants(self) -> "D3ExpectedApplicationBaseline":
        """Enforce meaningful expected-baseline metadata."""
        self.baseline_name = self.baseline_name.strip()
        self.baseline_mode = self.baseline_mode.strip()
        if not self.baseline_name:
            raise ValueError("D3 expected baseline_name must be non-empty")
        if not self.baseline_mode:
            raise ValueError("D3 expected baseline_mode must be non-empty")
        if self.model_name is not None:
            self.model_name = self.model_name.strip()
            if not self.model_name:
                raise ValueError("D3 expected model_name must be non-empty when supplied")
        if self.application_count < 0:
            raise ValueError("D3 expected application_count must be non-negative")
        if self.trace_id is not None:
            self.trace_id = self.trace_id.strip()
            if not self.trace_id:
                raise ValueError("D3 expected trace_id must be non-empty when supplied")
        if self.max_budget is not None and self.max_budget < 0:
            raise ValueError("D3 expected max_budget must be non-negative when supplied")
        if self.prediction_file_sha256 is not None and not _is_sha256(
            self.prediction_file_sha256
        ):
            raise ValueError(
                "D3 expected prediction_file_sha256 must be a 64-character SHA-256"
            )
        return self


class D3ComparisonMetricCriterion(BaseModel):
    """One pre-registered D3 comparison metric criterion."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(description="Stable unique criterion ID")
    baseline_name: str = Field(description="Expected baseline this criterion evaluates")
    metric: D3ComparisonMetric = Field(description="D3 comparison metric governed")
    operator: D3ComparisonOperator = Field(description="Threshold comparison operator")
    threshold: float = Field(description="Pre-registered numeric threshold")
    rationale: str = Field(description="Human-readable pre-registration rationale")

    @model_validator(mode="after")
    def require_metric_criterion_invariants(self) -> "D3ComparisonMetricCriterion":
        """Enforce interpretable threshold criteria."""
        self.criterion_id = self.criterion_id.strip()
        self.baseline_name = self.baseline_name.strip()
        self.rationale = self.rationale.strip()
        if not self.criterion_id:
            raise ValueError("D3 metric criterion_id must be non-empty")
        if not self.baseline_name:
            raise ValueError("D3 metric criterion baseline_name must be non-empty")
        if not self.rationale:
            raise ValueError("D3 metric criterion rationale must be non-empty")
        if not math.isfinite(self.threshold):
            raise ValueError("D3 metric criterion threshold must be finite")
        if self.metric in _PROPORTION_METRICS and not 0 <= self.threshold <= 1:
            raise ValueError(
                "D3 metric criterion threshold for exact/span-IoU metrics must be between 0 and 1"
            )
        if self.metric not in _PROPORTION_METRICS and self.threshold < 0:
            raise ValueError(
                "D3 metric criterion threshold for Modified Hausdorff metrics must be non-negative"
            )
        return self


class D3MetricCriterionResult(BaseModel):
    """Evaluation result for one D3 comparison metric criterion."""

    model_config = ConfigDict(extra="forbid")

    criterion_id: str = Field(description="Stable unique criterion ID")
    baseline_name: str = Field(description="Baseline evaluated")
    metric: D3ComparisonMetric = Field(description="Metric evaluated")
    operator: D3ComparisonOperator = Field(description="Threshold comparison operator")
    threshold: float = Field(description="Pre-registered threshold")
    observed_value: float | None = Field(
        description="Observed metric value, or null when unavailable"
    )
    status: D3MetricCriteriaStatus = Field(description="Criterion evaluation status")
    rationale: str = Field(description="Pre-registered rationale")
    message: str = Field(description="Human-readable criterion result explanation")


class D3MetricCriteriaReport(BaseModel):
    """Machine-readable D3 metric-criteria evaluation report."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Metric criteria report schema version")
    package_type: Literal["d3_application_baseline_comparison_metric_criteria"] = Field(
        description="Report package kind"
    )
    status: Literal["pass", "fail"] = Field(description="Overall criteria status")
    protocol_id: str = Field(description="Protocol ID evaluated")
    criterion_count: int = Field(description="Number of criteria evaluated")
    passed_count: int = Field(description="Number of passing criteria")
    failed_count: int = Field(description="Number of failed criteria")
    missing_count: int = Field(description="Number of criteria with missing metric values")
    results: list[D3MetricCriterionResult] = Field(
        description="Per-criterion evaluation rows"
    )
    caution: str = Field(description="Claim-discipline caveat for criteria consumers")


class D3ComparisonProtocolPackage(BaseModel):
    """Pre-registered protocol for a D3 application-baseline comparison run."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="D3 comparison protocol schema version")
    package_type: Literal[
        "qualitative_coding.d3_application_baseline_comparison_protocol"
    ] = Field(description="Stable package type identifier")
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the comparison is registered for")
    dataset_name: str = Field(description="Human-readable dataset name")
    split: Literal["held_out", "dev", "public_comparator"] = Field(
        description="Evaluation split represented by this comparison"
    )
    gold_set_id: str = Field(description="Expected D3 gold-set ID")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before scoring")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_run: bool = Field(description="Whether this protocol was registered pre-run")
    expected_predictions: list[D3ExpectedApplicationBaseline] = Field(
        description="Application baselines expected in the comparison"
    )
    success_criteria: list[str] = Field(description="Human-readable pre-registered success criteria")
    metric_criteria: list[D3ComparisonMetricCriterion] = Field(
        default_factory=list,
        description="Optional machine-checkable pre-registered metric criteria",
    )
    caution: str = Field(description="Claim-discipline caveat for protocol consumers")

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D3ComparisonProtocolPackage":
        """Enforce split/provenance invariants and unique expected baselines."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.gold_set_id = self.gold_set_id.strip()
        self.success_criteria = [criterion.strip() for criterion in self.success_criteria]
        self.caution = self.caution.strip()
        if not self.protocol_id:
            raise ValueError("D3 comparison protocol_id must be non-empty")
        if not self.project_id:
            raise ValueError("D3 comparison project_id must be non-empty")
        if not self.dataset_name:
            raise ValueError("D3 comparison dataset_name must be non-empty")
        if not self.gold_set_id:
            raise ValueError("D3 comparison gold_set_id must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D3 comparison corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "D3 comparison project_state_sha256 must be a 64-character SHA-256"
            )
        if not self.expected_predictions:
            raise ValueError("D3 comparison protocol requires expected_predictions")
        if not self.success_criteria or any(not criterion for criterion in self.success_criteria):
            raise ValueError("D3 comparison protocol requires non-empty success_criteria")
        if not self.caution:
            raise ValueError("D3 comparison caution must be non-empty")

        names = [prediction.baseline_name for prediction in self.expected_predictions]
        duplicates = sorted(name for name in set(names) if names.count(name) > 1)
        if duplicates:
            raise ValueError("Duplicate D3 expected baseline name(s): " + ", ".join(duplicates))

        criterion_ids = [criterion.criterion_id for criterion in self.metric_criteria]
        duplicate_criteria = sorted(
            criterion_id
            for criterion_id in set(criterion_ids)
            if criterion_ids.count(criterion_id) > 1
        )
        if duplicate_criteria:
            raise ValueError(
                "Duplicate D3 metric criterion ID(s): " + ", ".join(duplicate_criteria)
            )
        expected_names = set(names)
        unknown_baselines = sorted(
            criterion.baseline_name
            for criterion in self.metric_criteria
            if criterion.baseline_name not in expected_names
        )
        if unknown_baselines:
            raise ValueError(
                "D3 metric criteria reference unknown baseline(s): "
                + ", ".join(unknown_baselines)
            )

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D3 comparison protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError(
                    "held_out D3 comparison protocols require contamination_checked=true"
                )
            if not self.registered_before_run:
                raise ValueError(
                    "held_out D3 comparison protocols require registered_before_run=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError("held_out D3 comparison protocols require project_state_sha256")
        return self


def load_d3_comparison_protocol(path: Path | str) -> D3ComparisonProtocolPackage:
    """Load and validate a D3 comparison protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D3 comparison protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D3 comparison protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d3_comparison_protocol_payload(raw)


def validate_d3_comparison_protocol_payload(payload: Any) -> D3ComparisonProtocolPackage:
    """Validate a raw JSON payload as a D3 comparison protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("D3 comparison protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D3 comparison protocol package must include schema_version=1")
    try:
        return D3ComparisonProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 comparison protocol package: {exc}") from exc


def evaluate_d3_comparison_metric_criteria(
    protocol_payload: Any,
    scorecard: Mapping[str, Any],
) -> D3MetricCriteriaReport | None:
    """Evaluate D3 protocol metric criteria against a Phase 0 scorecard."""
    protocol = validate_d3_comparison_protocol_payload(protocol_payload)
    if not protocol.metric_criteria:
        return None

    results = [
        _evaluate_metric_criterion(criterion, scorecard)
        for criterion in protocol.metric_criteria
    ]
    passed_count = sum(1 for result in results if result.status == "pass")
    failed_count = sum(1 for result in results if result.status == "fail")
    missing_count = sum(1 for result in results if result.status == "missing")
    return D3MetricCriteriaReport(
        schema_version=1,
        package_type="d3_application_baseline_comparison_metric_criteria",
        status="pass" if passed_count == len(results) else "fail",
        protocol_id=protocol.protocol_id,
        criterion_count=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        missing_count=missing_count,
        results=results,
        caution=(
            "D3 metric criteria evaluate pre-registered local comparison metrics only; "
            "they are not held-out D3 evidence, expert-parity evidence, "
            "methodological-validity evidence, superiority evidence, or SOTA evidence."
        ),
    )


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))


def _evaluate_metric_criterion(
    criterion: D3ComparisonMetricCriterion,
    scorecard: Mapping[str, Any],
) -> D3MetricCriterionResult:
    """Evaluate one D3 criterion against a Phase 0 scorecard."""
    observed = _lookup_baseline_metric(
        scorecard,
        baseline_name=criterion.baseline_name,
        metric=criterion.metric,
    )
    if observed is None:
        return D3MetricCriterionResult(
            criterion_id=criterion.criterion_id,
            baseline_name=criterion.baseline_name,
            metric=criterion.metric,
            operator=criterion.operator,
            threshold=criterion.threshold,
            observed_value=None,
            status="missing",
            rationale=criterion.rationale,
            message=(
                f"Metric {criterion.metric!r} was not available for baseline "
                f"{criterion.baseline_name!r}"
            ),
        )
    passed = _compare(observed, criterion.operator, criterion.threshold)
    return D3MetricCriterionResult(
        criterion_id=criterion.criterion_id,
        baseline_name=criterion.baseline_name,
        metric=criterion.metric,
        operator=criterion.operator,
        threshold=criterion.threshold,
        observed_value=observed,
        status="pass" if passed else "fail",
        rationale=criterion.rationale,
        message=(
            f"Observed {criterion.metric}={observed} "
            f"{'met' if passed else 'did not meet'} "
            f"{criterion.operator} {criterion.threshold}"
        ),
    )


def _lookup_baseline_metric(
    scorecard: Mapping[str, Any],
    *,
    baseline_name: str,
    metric: D3ComparisonMetric,
) -> float | None:
    """Return a D3 baseline metric value when present and numeric."""
    d3_section = scorecard.get("application_validity_d3")
    if not isinstance(d3_section, Mapping):
        return None
    baselines = d3_section.get("baselines")
    if not isinstance(baselines, Mapping):
        return None
    baseline = baselines.get(baseline_name)
    if not isinstance(baseline, Mapping):
        return None
    if metric in _SPAN_OVERLAP_METRICS:
        span_overlap = baseline.get("span_overlap")
        if not isinstance(span_overlap, Mapping):
            return None
        return _numeric_or_none(span_overlap.get(metric))
    return _numeric_or_none(baseline.get(metric))


def _numeric_or_none(value: Any) -> float | None:
    """Return finite numeric values as floats; treat everything else as missing."""
    if type(value) not in {int, float}:
        return None
    numeric = float(value)
    if not math.isfinite(numeric):
        return None
    return numeric


def _compare(observed: float, operator: D3ComparisonOperator, threshold: float) -> bool:
    """Compare an observed metric to a threshold."""
    if operator == ">=":
        return observed >= threshold
    if operator == ">":
        return observed > threshold
    if operator == "<=":
        return observed <= threshold
    if operator == "<":
        return observed < threshold
    return observed == threshold
