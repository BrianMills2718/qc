"""Validate pre-evaluation D4 codebook-quality protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D4ProtocolSplit = Literal["held_out", "dev", "public_comparator"]
D4RubricMetric = Literal["clarity", "specificity", "usefulness", "grounding"]
_REQUIRED_D4_METRICS: set[D4RubricMetric] = {
    "clarity",
    "specificity",
    "usefulness",
    "grounding",
}

D4_CODEBOOK_QUALITY_PROTOCOL_CAUTION = (
    "D4 codebook-quality protocol packages are pre-evaluation process/provenance "
    "metadata only; they are not blind expert evidence, not codebook-quality "
    "evidence, not methodological-validity evidence, and not SOTA evidence."
)


class D4BlindingPlan(BaseModel):
    """Blinding metadata for D4 codebook-quality evaluation."""

    raters_blinded_to_origin: bool = Field(
        description="Whether raters are blind to human/system codebook origin"
    )
    source_labels_masked: bool = Field(
        description="Whether source/origin labels are masked in evaluation materials"
    )
    blinding_method: str = Field(description="Human-readable blinding method")

    @model_validator(mode="after")
    def require_blinding(self) -> "D4BlindingPlan":
        """Reject unblinded D4 protocol metadata."""
        self.blinding_method = self.blinding_method.strip()
        _require_non_empty("blinding.blinding_method", self.blinding_method)
        if not self.raters_blinded_to_origin:
            raise ValueError("D4 protocol requires raters_blinded_to_origin=true")
        if not self.source_labels_masked:
            raise ValueError("D4 protocol requires source_labels_masked=true")
        return self


class D4EvaluatorPlan(BaseModel):
    """Evaluator plan for D4 rubric collection."""

    evaluator_types: list[str] = Field(
        description="Evaluator types, such as human_expert or llm_judge"
    )
    planned_evaluator_count: int = Field(description="Planned number of evaluators")
    qualification: str = Field(description="Evaluator qualification statement")

    @model_validator(mode="after")
    def require_evaluator_plan(self) -> "D4EvaluatorPlan":
        """Reject empty or underspecified evaluator plans."""
        self.evaluator_types = _clean_unique_strings(
            self.evaluator_types,
            "D4 evaluator_plan.evaluator_types",
        )
        self.qualification = self.qualification.strip()
        _require_non_empty("evaluator_plan.qualification", self.qualification)
        if self.planned_evaluator_count < 1:
            raise ValueError("D4 evaluator_plan.planned_evaluator_count must be at least 1")
        return self


class D4SuccessCriterion(BaseModel):
    """One pre-registered D4 success or reporting criterion."""

    metric: D4RubricMetric = Field(description="D4 rubric metric governed")
    pass_condition: str = Field(
        description="Pre-registered pass/fail or reporting condition"
    )
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "D4SuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class D4CodebookQualityProtocolPackage(BaseModel):
    """Versioned protocol package for D4 codebook-quality evaluation."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.d4_codebook_quality_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the D4 protocol governs")
    dataset_name: str = Field(description="Human-readable D4 dataset name")
    split: D4ProtocolSplit = Field(description="Evaluation split governed by this protocol")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    codebook_artifact_sha256: str | None = Field(
        default=None,
        description="Expected codebook artifact SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen pre-evaluation")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_evaluation: bool = Field(
        description="Whether this protocol was registered before evaluation"
    )
    blinding: D4BlindingPlan = Field(description="Blinding metadata")
    evaluator_plan: D4EvaluatorPlan = Field(description="Evaluator plan")
    rubric_metrics: list[D4RubricMetric] = Field(
        description="D4 rubric metrics configured for evaluation"
    )
    target_scopes: list[str] = Field(
        description="Evaluation target scopes, such as codebook or individual_code"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future D4 result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future D4 result file",
    )
    success_criteria: list[D4SuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=D4_CODEBOOK_QUALITY_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D4CodebookQualityProtocolPackage":
        """Enforce D4 protocol metadata invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.caution = self.caution.strip()
        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D4 protocol corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "D4 protocol project_state_sha256 must be a 64-character SHA-256"
            )
        if self.codebook_artifact_sha256 is not None and not _is_sha256(
            self.codebook_artifact_sha256
        ):
            raise ValueError(
                "D4 protocol codebook_artifact_sha256 must be a 64-character SHA-256"
            )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "D4 protocol outcome_file_sha256 must be a 64-character SHA-256"
            )
        _require_required_metrics(self.rubric_metrics)
        self.target_scopes = _clean_unique_strings(
            self.target_scopes,
            "D4 target_scopes",
        )
        _check_success_criteria_cover_metrics(self.rubric_metrics, self.success_criteria)
        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D4 protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D4 protocols require contamination_checked=true")
            if not self.registered_before_evaluation:
                raise ValueError(
                    "held_out D4 protocols require registered_before_evaluation=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError("held_out D4 protocols require project_state_sha256")
            if self.codebook_artifact_sha256 is None:
                raise ValueError("held_out D4 protocols require codebook_artifact_sha256")
        return self


def load_d4_codebook_quality_protocol(
    path: str | Path,
) -> D4CodebookQualityProtocolPackage:
    """Load and validate a D4 codebook-quality protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D4 protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D4 protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d4_codebook_quality_protocol_payload(raw)


def validate_d4_codebook_quality_protocol_payload(
    payload: Any,
) -> D4CodebookQualityProtocolPackage:
    """Validate a raw JSON payload as a D4 codebook-quality protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("D4 codebook-quality protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError(
            "D4 codebook-quality protocol package must include schema_version=1"
        )
    try:
        return D4CodebookQualityProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D4 codebook-quality protocol package: {exc}") from exc


def _require_required_metrics(metrics: list[D4RubricMetric]) -> None:
    """Reject duplicate or incomplete D4 metric configuration."""
    if not metrics:
        raise ValueError("D4 rubric_metrics is required")
    duplicates = sorted(metric for metric in set(metrics) if metrics.count(metric) > 1)
    if duplicates:
        raise ValueError("Duplicate D4 rubric metric(s): " + ", ".join(duplicates))
    missing = sorted(_REQUIRED_D4_METRICS - set(metrics))
    if missing:
        raise ValueError(
            "D4 rubric_metrics missing required metric(s): " + ", ".join(missing)
        )


def _check_success_criteria_cover_metrics(
    metrics: list[D4RubricMetric],
    criteria: list[D4SuccessCriterion],
) -> None:
    """Reject missing or out-of-scope success criteria."""
    if not criteria:
        raise ValueError("D4 success_criteria is required")
    metric_set = set(metrics)
    criterion_metrics = {criterion.metric for criterion in criteria}
    unknown = sorted(criterion_metrics - metric_set)
    if unknown:
        raise ValueError(
            "D4 success criteria reference unconfigured metric(s): " + ", ".join(unknown)
        )
    missing = sorted(metric_set - criterion_metrics)
    if missing:
        raise ValueError(
            "D4 protocol missing success criteria for metric(s): " + ", ".join(missing)
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
        raise ValueError(f"D4 protocol {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return true when value is a 64-character hexadecimal SHA-256."""
    return bool(_SHA256_RE.fullmatch(value))
