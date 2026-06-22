"""Validate pre-evaluation D9 interpretive-preference protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D9ProtocolSplit = Literal["held_out", "dev", "public_comparator"]
D9OutcomeMetric = Literal[
    "system_minus_human_preference_rate",
    "system_preference_rate",
    "tie_rate",
]
_REQUIRED_D9_METRICS: set[D9OutcomeMetric] = {
    "system_minus_human_preference_rate",
}

D9_INTERPRETIVE_PREFERENCE_PROTOCOL_CAUTION = (
    "D9 interpretive-preference protocol packages are pre-evaluation "
    "process/provenance metadata only; they are not blind expert-parity "
    "evidence, not interpretive-depth evidence, not methodological-validity "
    "evidence, and not SOTA evidence."
)


class D9EvaluatorPlan(BaseModel):
    """Evaluator plan for D9 blind preference collection."""

    evaluator_types: list[str] = Field(
        description="Evaluator types, such as human_expert or llm_judge"
    )
    planned_evaluator_count: int = Field(description="Planned number of evaluators")
    qualification: str = Field(description="Evaluator qualification statement")

    @model_validator(mode="after")
    def require_evaluator_plan(self) -> "D9EvaluatorPlan":
        """Reject empty or underspecified evaluator plans."""
        self.evaluator_types = _clean_unique_strings(
            self.evaluator_types,
            "D9 evaluator_plan.evaluator_types",
        )
        self.qualification = self.qualification.strip()
        _require_non_empty("evaluator_plan.qualification", self.qualification)
        if self.planned_evaluator_count < 1:
            raise ValueError("D9 evaluator_plan.planned_evaluator_count must be at least 1")
        return self


class D9SuccessCriterion(BaseModel):
    """One pre-registered D9 success or reporting criterion."""

    metric: D9OutcomeMetric = Field(description="D9 outcome metric governed")
    pass_condition: str = Field(
        description="Pre-registered pass/fail or reporting condition"
    )
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "D9SuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class D9InterpretivePreferenceProtocolPackage(BaseModel):
    """Versioned protocol package for D9 interpretive-preference evaluation."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.d9_interpretive_preference_protocol"] = (
        Field(description="Stable package type identifier")
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the D9 protocol governs")
    dataset_name: str = Field(description="Human-readable D9 dataset name")
    split: D9ProtocolSplit = Field(description="Evaluation split governed by protocol")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    comparison_artifact_sha256: str | None = Field(
        default=None,
        description="Expected system/human comparison artifact SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen")
    contamination_checked: bool = Field(description="Whether contamination was checked")
    registered_before_evaluation: bool = Field(
        description="Whether this protocol was registered before evaluation"
    )
    blinded: bool = Field(
        description="Whether evaluators are blinded to system/human condition"
    )
    evaluator_plan: D9EvaluatorPlan = Field(description="Evaluator plan")
    target_criteria: list[str] = Field(
        description="Preference criteria, such as interpretive_depth"
    )
    target_surfaces: list[str] = Field(
        description="Compared surfaces, such as codebook or themes"
    )
    planned_case_count: int = Field(description="Planned number of comparison cases")
    non_inferiority_margin: float = Field(
        description="Pre-registered tolerated system-minus-human preference deficit"
    )
    outcome_metrics: list[D9OutcomeMetric] = Field(
        description="D9 outcome metrics configured for evaluation"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future D9 result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future D9 result file",
    )
    success_criteria: list[D9SuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=D9_INTERPRETIVE_PREFERENCE_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D9InterpretivePreferenceProtocolPackage":
        """Enforce D9 protocol metadata invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.caution = self.caution.strip()
        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D9 protocol corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "D9 protocol project_state_sha256 must be a 64-character SHA-256"
            )
        if self.comparison_artifact_sha256 is not None and not _is_sha256(
            self.comparison_artifact_sha256
        ):
            raise ValueError(
                "D9 protocol comparison_artifact_sha256 must be a 64-character SHA-256"
            )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "D9 protocol outcome_file_sha256 must be a 64-character SHA-256"
            )
        self.target_criteria = _clean_unique_strings(
            self.target_criteria,
            "D9 target_criteria",
        )
        self.target_surfaces = _clean_unique_strings(
            self.target_surfaces,
            "D9 target_surfaces",
        )
        _require_outcome_metrics(self.outcome_metrics)
        _check_success_criteria_cover_metrics(self.outcome_metrics, self.success_criteria)
        if self.planned_case_count < 1:
            raise ValueError("D9 protocol planned_case_count must be at least 1")
        if not 0 < self.non_inferiority_margin < 1:
            raise ValueError("D9 protocol non_inferiority_margin must be between 0 and 1")
        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D9 protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D9 protocols require contamination_checked=true")
            if not self.registered_before_evaluation:
                raise ValueError(
                    "held_out D9 protocols require registered_before_evaluation=true"
                )
            if not self.blinded:
                raise ValueError("held_out D9 protocols require blinded=true")
            if self.project_state_sha256 is None:
                raise ValueError("held_out D9 protocols require project_state_sha256")
            if self.comparison_artifact_sha256 is None:
                raise ValueError(
                    "held_out D9 protocols require comparison_artifact_sha256"
                )
        return self


def load_d9_interpretive_preference_protocol(
    path: str | Path,
) -> D9InterpretivePreferenceProtocolPackage:
    """Load and validate a D9 interpretive-preference protocol package."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D9 protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D9 protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d9_interpretive_preference_protocol_payload(raw)


def validate_d9_interpretive_preference_protocol_payload(
    payload: Any,
) -> D9InterpretivePreferenceProtocolPackage:
    """Validate a raw JSON payload as a D9 interpretive-preference protocol."""
    if not isinstance(payload, dict):
        raise ValueError("D9 interpretive-preference protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError(
            "D9 interpretive-preference protocol package must include schema_version=1"
        )
    try:
        return D9InterpretivePreferenceProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid D9 interpretive-preference protocol package: {exc}"
        ) from exc


def _require_outcome_metrics(metrics: list[D9OutcomeMetric]) -> None:
    """Reject duplicate or unusable D9 outcome metric configuration."""
    if not metrics:
        raise ValueError("D9 outcome_metrics is required")
    duplicates = sorted(metric for metric in set(metrics) if metrics.count(metric) > 1)
    if duplicates:
        raise ValueError("Duplicate D9 outcome metric(s): " + ", ".join(duplicates))
    missing = sorted(_REQUIRED_D9_METRICS - set(metrics))
    if missing:
        raise ValueError(
            "D9 outcome_metrics missing required metric(s): " + ", ".join(missing)
        )


def _check_success_criteria_cover_metrics(
    metrics: list[D9OutcomeMetric],
    criteria: list[D9SuccessCriterion],
) -> None:
    """Reject missing or out-of-scope success criteria."""
    if not criteria:
        raise ValueError("D9 success_criteria is required")
    metric_set = set(metrics)
    criterion_metrics = {criterion.metric for criterion in criteria}
    unknown = sorted(criterion_metrics - metric_set)
    if unknown:
        raise ValueError(
            "D9 success criteria reference unconfigured metric(s): " + ", ".join(unknown)
        )
    missing = sorted(metric_set - criterion_metrics)
    if missing:
        raise ValueError(
            "D9 protocol missing success criteria for metric(s): " + ", ".join(missing)
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
        raise ValueError(f"D9 protocol {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return whether a string is a 64-character SHA-256 digest."""
    return bool(_SHA256_RE.fullmatch(value))
