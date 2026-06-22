"""Validate pre-evaluation confidence-calibration protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

ConfidenceCalibrationProtocolSplit = Literal["held_out", "dev", "public_comparator"]
ConfidenceCalibrationOutcomeMetric = Literal[
    "accuracy",
    "mean_confidence",
    "brier_score",
    "expected_calibration_error",
]
_REQUIRED_CONFIDENCE_CALIBRATION_METRICS: set[ConfidenceCalibrationOutcomeMetric] = {
    "accuracy",
    "brier_score",
    "expected_calibration_error",
}

CONFIDENCE_CALIBRATION_PROTOCOL_CAUTION = (
    "Confidence-calibration protocol packages are pre-evaluation process/"
    "provenance metadata only; they are not calibration proof, not held-out "
    "correctness evidence, not methodological-validity evidence, and not SOTA "
    "evidence."
)


class ConfidenceCalibrationLabelPlan(BaseModel):
    """Correctness-label source plan for confidence calibration."""

    label_sources: list[str] = Field(
        description="Correctness label sources, such as expert_adjudication"
    )
    planned_labeler_count: int = Field(description="Planned number of labelers")
    qualification: str = Field(description="Labeler or label-source qualification")

    @model_validator(mode="after")
    def require_label_plan(self) -> "ConfidenceCalibrationLabelPlan":
        """Reject empty or underspecified label-source plans."""
        self.label_sources = _clean_unique_strings(
            self.label_sources,
            "confidence calibration label_plan.label_sources",
        )
        self.qualification = self.qualification.strip()
        _require_non_empty("label_plan.qualification", self.qualification)
        if self.planned_labeler_count < 1:
            raise ValueError(
                "confidence calibration label_plan.planned_labeler_count must be at least 1"
            )
        return self


class ConfidenceCalibrationSuccessCriterion(BaseModel):
    """One pre-registered calibration success or reporting criterion."""

    metric: ConfidenceCalibrationOutcomeMetric = Field(
        description="Confidence-calibration outcome metric governed"
    )
    pass_condition: str = Field(
        description="Pre-registered pass/fail or reporting condition"
    )
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "ConfidenceCalibrationSuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class ConfidenceCalibrationProtocolPackage(BaseModel):
    """Versioned protocol package for confidence-calibration evaluation."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.confidence_calibration_protocol"] = (
        Field(description="Stable package type identifier")
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the protocol governs")
    dataset_name: str = Field(description="Human-readable calibration dataset name")
    split: ConfidenceCalibrationProtocolSplit = Field(
        description="Evaluation split governed by protocol"
    )
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    prediction_artifact_sha256: str | None = Field(
        default=None,
        description="Expected frozen prediction/confidence artifact SHA-256",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen")
    contamination_checked: bool = Field(description="Whether contamination was checked")
    registered_before_evaluation: bool = Field(
        description="Whether this protocol was registered before evaluation"
    )
    label_plan: ConfidenceCalibrationLabelPlan = Field(
        description="Correctness-label source plan"
    )
    target_surfaces: list[str] = Field(
        description="Prediction surfaces covered, such as thematic_coding"
    )
    confidence_source: str = Field(
        description="Source of confidence values, such as system_confidence_field"
    )
    planned_item_count: int = Field(description="Planned number of calibration items")
    outcome_metrics: list[ConfidenceCalibrationOutcomeMetric] = Field(
        description="Calibration outcome metrics configured for evaluation"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future calibration result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future calibration result file",
    )
    success_criteria: list[ConfidenceCalibrationSuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=CONFIDENCE_CALIBRATION_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "ConfidenceCalibrationProtocolPackage":
        """Enforce confidence-calibration protocol metadata invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.confidence_source = self.confidence_source.strip()
        self.caution = self.caution.strip()
        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("confidence_source", self.confidence_source)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError(
                "confidence calibration protocol corpus_sha256 must be a 64-character SHA-256"
            )
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "confidence calibration protocol project_state_sha256 must be a "
                "64-character SHA-256"
            )
        if self.prediction_artifact_sha256 is not None and not _is_sha256(
            self.prediction_artifact_sha256
        ):
            raise ValueError(
                "confidence calibration protocol prediction_artifact_sha256 must "
                "be a 64-character SHA-256"
            )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "confidence calibration protocol outcome_file_sha256 must be a "
                "64-character SHA-256"
            )
        self.target_surfaces = _clean_unique_strings(
            self.target_surfaces,
            "confidence calibration target_surfaces",
        )
        _require_outcome_metrics(self.outcome_metrics)
        _check_success_criteria_cover_metrics(
            self.outcome_metrics,
            self.success_criteria,
        )
        if self.planned_item_count < 1:
            raise ValueError(
                "confidence calibration protocol planned_item_count must be at least 1"
            )
        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError(
                    "held_out confidence calibration protocols require prompt_frozen=true"
                )
            if not self.contamination_checked:
                raise ValueError(
                    "held_out confidence calibration protocols require "
                    "contamination_checked=true"
                )
            if not self.registered_before_evaluation:
                raise ValueError(
                    "held_out confidence calibration protocols require "
                    "registered_before_evaluation=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError(
                    "held_out confidence calibration protocols require "
                    "project_state_sha256"
                )
            if self.prediction_artifact_sha256 is None:
                raise ValueError(
                    "held_out confidence calibration protocols require "
                    "prediction_artifact_sha256"
                )
        return self


def load_confidence_calibration_protocol(
    path: str | Path,
) -> ConfidenceCalibrationProtocolPackage:
    """Load and validate a confidence-calibration protocol package."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Confidence calibration protocol file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Confidence calibration protocol file '{path}' is not valid JSON: {exc}"
        ) from exc
    return validate_confidence_calibration_protocol_payload(raw)


def validate_confidence_calibration_protocol_payload(
    payload: Any,
) -> ConfidenceCalibrationProtocolPackage:
    """Validate a raw JSON payload as a confidence-calibration protocol."""
    if not isinstance(payload, dict):
        raise ValueError("Confidence calibration protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError(
            "Confidence calibration protocol package must include schema_version=1"
        )
    try:
        return ConfidenceCalibrationProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid confidence calibration protocol package: {exc}"
        ) from exc


def _require_outcome_metrics(
    metrics: list[ConfidenceCalibrationOutcomeMetric],
) -> None:
    """Reject duplicate or incomplete calibration metric configuration."""
    if not metrics:
        raise ValueError("confidence calibration outcome_metrics is required")
    duplicates = sorted(metric for metric in set(metrics) if metrics.count(metric) > 1)
    if duplicates:
        raise ValueError(
            "Duplicate confidence calibration outcome metric(s): "
            + ", ".join(duplicates)
        )
    missing = sorted(_REQUIRED_CONFIDENCE_CALIBRATION_METRICS - set(metrics))
    if missing:
        raise ValueError(
            "confidence calibration outcome_metrics missing required metric(s): "
            + ", ".join(missing)
        )


def _check_success_criteria_cover_metrics(
    metrics: list[ConfidenceCalibrationOutcomeMetric],
    criteria: list[ConfidenceCalibrationSuccessCriterion],
) -> None:
    """Reject missing or out-of-scope success criteria."""
    if not criteria:
        raise ValueError("confidence calibration success_criteria is required")
    metric_set = set(metrics)
    criterion_metrics = {criterion.metric for criterion in criteria}
    unknown = sorted(criterion_metrics - metric_set)
    if unknown:
        raise ValueError(
            "confidence calibration success criteria reference unconfigured "
            "metric(s): " + ", ".join(unknown)
        )
    missing = sorted(metric_set - criterion_metrics)
    if missing:
        raise ValueError(
            "confidence calibration protocol missing success criteria for "
            "metric(s): " + ", ".join(missing)
        )


def _clean_unique_strings(values: list[str], field_name: str) -> list[str]:
    """Trim, validate, and de-duplicate a string list."""
    cleaned = [value.strip() for value in values]
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    empty_indexes = [str(index) for index, value in enumerate(cleaned) if not value]
    if empty_indexes:
        raise ValueError(
            f"{field_name} contains empty value(s) at index: "
            f"{', '.join(empty_indexes)}"
        )
    duplicates = sorted(value for value in set(cleaned) if cleaned.count(value) > 1)
    if duplicates:
        raise ValueError(f"Duplicate {field_name}: " + ", ".join(duplicates))
    return cleaned


def _require_non_empty(field_name: str, value: str) -> None:
    """Raise if a string field is empty after trimming whitespace."""
    if not value:
        raise ValueError(
            f"confidence calibration protocol {field_name} must be non-empty"
        )


def _is_sha256(value: str) -> bool:
    """Return whether a string is a SHA-256 hex digest."""
    return bool(_SHA256_RE.fullmatch(value))
