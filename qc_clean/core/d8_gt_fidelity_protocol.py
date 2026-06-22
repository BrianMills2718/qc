"""Validate pre-evaluation D8 GT-fidelity protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D8ProtocolSplit = Literal["held_out", "dev", "public_comparator"]
D8RubricMetric = Literal[
    "constant_comparison",
    "category_development",
    "memo_quality",
    "saturation_justification",
]
_REQUIRED_D8_METRICS: set[D8RubricMetric] = {
    "constant_comparison",
    "category_development",
    "memo_quality",
    "saturation_justification",
}

D8_GT_FIDELITY_PROTOCOL_CAUTION = (
    "D8 GT-fidelity protocol packages are pre-evaluation process/provenance "
    "metadata only; they are not expert-rubric acceptance, not methodological-"
    "saturation evidence, not full grounded-theory evidence, and not SOTA "
    "evidence."
)


class D8EvaluatorPlan(BaseModel):
    """Evaluator plan for D8 rubric collection."""

    evaluator_types: list[str] = Field(
        description="Evaluator types, such as human_expert or llm_judge"
    )
    planned_evaluator_count: int = Field(description="Planned number of evaluators")
    qualification: str = Field(description="Evaluator qualification statement")

    @model_validator(mode="after")
    def require_evaluator_plan(self) -> "D8EvaluatorPlan":
        """Reject empty or underspecified evaluator plans."""
        self.evaluator_types = _clean_unique_strings(
            self.evaluator_types,
            "D8 evaluator_plan.evaluator_types",
        )
        self.qualification = self.qualification.strip()
        _require_non_empty("evaluator_plan.qualification", self.qualification)
        if self.planned_evaluator_count < 1:
            raise ValueError("D8 evaluator_plan.planned_evaluator_count must be at least 1")
        return self


class D8SuccessCriterion(BaseModel):
    """One pre-registered D8 success or reporting criterion."""

    metric: D8RubricMetric = Field(description="D8 rubric metric governed")
    pass_condition: str = Field(
        description="Pre-registered pass/fail or reporting condition"
    )
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "D8SuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class D8GTFidelityProtocolPackage(BaseModel):
    """Versioned protocol package for D8 GT-fidelity evaluation."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.d8_gt_fidelity_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the D8 protocol governs")
    dataset_name: str = Field(description="Human-readable D8 dataset name")
    split: D8ProtocolSplit = Field(description="Evaluation split governed by protocol")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    gt_artifact_sha256: str | None = Field(
        default=None,
        description="Expected GT artifact bundle SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen")
    contamination_checked: bool = Field(description="Whether contamination was checked")
    registered_before_evaluation: bool = Field(
        description="Whether this protocol was registered before evaluation"
    )
    evaluator_plan: D8EvaluatorPlan = Field(description="Evaluator plan")
    rubric_metrics: list[D8RubricMetric] = Field(
        description="D8 rubric metrics configured for evaluation"
    )
    target_scopes: list[str] = Field(
        description="Evaluation target scopes, such as category or memo"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future D8 result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future D8 result file",
    )
    success_criteria: list[D8SuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=D8_GT_FIDELITY_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D8GTFidelityProtocolPackage":
        """Enforce D8 protocol metadata invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.caution = self.caution.strip()
        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D8 protocol corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "D8 protocol project_state_sha256 must be a 64-character SHA-256"
            )
        if self.gt_artifact_sha256 is not None and not _is_sha256(
            self.gt_artifact_sha256
        ):
            raise ValueError(
                "D8 protocol gt_artifact_sha256 must be a 64-character SHA-256"
            )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "D8 protocol outcome_file_sha256 must be a 64-character SHA-256"
            )
        _require_required_metrics(self.rubric_metrics)
        self.target_scopes = _clean_unique_strings(
            self.target_scopes,
            "D8 target_scopes",
        )
        _check_success_criteria_cover_metrics(self.rubric_metrics, self.success_criteria)
        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D8 protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D8 protocols require contamination_checked=true")
            if not self.registered_before_evaluation:
                raise ValueError(
                    "held_out D8 protocols require registered_before_evaluation=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError("held_out D8 protocols require project_state_sha256")
            if self.gt_artifact_sha256 is None:
                raise ValueError("held_out D8 protocols require gt_artifact_sha256")
        return self


def load_d8_gt_fidelity_protocol(path: str | Path) -> D8GTFidelityProtocolPackage:
    """Load and validate a D8 GT-fidelity protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D8 protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D8 protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d8_gt_fidelity_protocol_payload(raw)


def validate_d8_gt_fidelity_protocol_payload(
    payload: Any,
) -> D8GTFidelityProtocolPackage:
    """Validate a raw JSON payload as a D8 GT-fidelity protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("D8 GT-fidelity protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D8 GT-fidelity protocol package must include schema_version=1")
    try:
        return D8GTFidelityProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D8 GT-fidelity protocol package: {exc}") from exc


def _require_required_metrics(metrics: list[D8RubricMetric]) -> None:
    """Reject duplicate or incomplete D8 metric configuration."""
    if not metrics:
        raise ValueError("D8 rubric_metrics is required")
    duplicates = sorted(metric for metric in set(metrics) if metrics.count(metric) > 1)
    if duplicates:
        raise ValueError("Duplicate D8 rubric metric(s): " + ", ".join(duplicates))
    missing = sorted(_REQUIRED_D8_METRICS - set(metrics))
    if missing:
        raise ValueError("D8 rubric_metrics missing required metric(s): " + ", ".join(missing))


def _check_success_criteria_cover_metrics(
    metrics: list[D8RubricMetric],
    criteria: list[D8SuccessCriterion],
) -> None:
    """Reject missing or out-of-scope success criteria."""
    if not criteria:
        raise ValueError("D8 success_criteria is required")
    metric_set = set(metrics)
    criterion_metrics = {criterion.metric for criterion in criteria}
    unknown = sorted(criterion_metrics - metric_set)
    if unknown:
        raise ValueError(
            "D8 success criteria reference unconfigured metric(s): " + ", ".join(unknown)
        )
    missing = sorted(metric_set - criterion_metrics)
    if missing:
        raise ValueError(
            "D8 protocol missing success criteria for metric(s): " + ", ".join(missing)
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
        raise ValueError(f"D8 protocol {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return true when value is a 64-character hexadecimal SHA-256."""
    return bool(_SHA256_RE.fullmatch(value))
