"""Validate pre-registered adjudication protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator

from qc_clean.core.adjudication_sample import TargetType


ProtocolSplit = Literal["held_out", "dev", "public_comparator"]
TargetDimension = Literal["d3_application_validity", "d7_disconfirmation"]

PROTOCOL_CAUTION = (
    "Adjudication protocol packages are pre-registration metadata only; they "
    "are not expert evidence, labels, correctness estimates, validity evidence, "
    "or benchmark results."
)

_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
_REQUIRED_TARGET_BY_DIMENSION: dict[TargetDimension, TargetType] = {
    "d3_application_validity": "code_application",
    "d7_disconfirmation": "negative_case",
}


class AdjudicationSamplingPlan(BaseModel):
    """Sampling plan recorded before adjudication labels are collected."""

    sample_package_path: str | None = Field(
        default=None,
        description="Optional path to the adjudication sample package this protocol governs",
    )
    sample_package_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 of the adjudication sample package",
    )
    target_item_types: list[TargetType] = Field(
        description="Adjudication sample target types covered by this protocol"
    )
    sampling_method: str = Field(description="Human-readable sampling method")
    planned_sample_size: int = Field(description="Planned total sample size")

    @model_validator(mode="after")
    def require_valid_sampling_plan(self) -> "AdjudicationSamplingPlan":
        """Reject empty, duplicate, or underspecified sampling plans."""
        if self.sample_package_path is not None:
            self.sample_package_path = self.sample_package_path.strip() or None
        if self.sample_package_sha256 is not None and not _is_sha256(
            self.sample_package_sha256
        ):
            raise ValueError("sample_package_sha256 must be a 64-character hex SHA-256")
        if not self.target_item_types:
            raise ValueError("Adjudication protocol sampling_plan.target_item_types is required")
        duplicates = sorted(
            item for item in set(self.target_item_types) if self.target_item_types.count(item) > 1
        )
        if duplicates:
            raise ValueError("Duplicate adjudication sample target type(s): " + ", ".join(duplicates))
        self.sampling_method = self.sampling_method.strip()
        if not self.sampling_method:
            raise ValueError("Adjudication protocol sampling_method must be non-empty")
        if self.planned_sample_size < 1:
            raise ValueError("Adjudication protocol planned_sample_size must be at least 1")
        return self


class AdjudicationSuccessCriterion(BaseModel):
    """One pre-registered success criterion for an adjudication dimension."""

    dimension: TargetDimension = Field(description="Evaluation dimension this criterion governs")
    metric: str = Field(description="Metric or scorecard field to inspect")
    pass_condition: str = Field(description="Pre-registered pass/fail or reporting condition")
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "AdjudicationSuccessCriterion":
        """Reject criteria that cannot be interpreted by a human or agent."""
        self.metric = self.metric.strip()
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        if not self.metric:
            raise ValueError("Adjudication success criterion metric must be non-empty")
        if not self.pass_condition:
            raise ValueError("Adjudication success criterion pass_condition must be non-empty")
        return self


class AdjudicationProtocolPackage(BaseModel):
    """Versioned adjudication protocol package for pre-label registration."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["adjudication_protocol"] = Field(description="Protocol package kind")
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID this protocol governs")
    dataset_name: str = Field(description="Human-readable adjudication dataset name")
    split: ProtocolSplit = Field(description="Evaluation split governed by this protocol")
    corpus_sha256: str = Field(description="SHA-256 hash of the corpus payload")
    project_state_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hash of the ProjectState used for sampling",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before labeling")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_labeling: bool = Field(
        description="Whether this protocol was registered before labels were collected"
    )
    coder_count: int = Field(description="Number of independent human coders before adjudication")
    adjudicator: str = Field(description="Adjudicator identifier, name, or redacted label")
    coder_qualification: str = Field(description="Coder expertise/qualification statement")
    target_dimensions: list[TargetDimension] = Field(
        description="Evaluation dimensions governed by this protocol"
    )
    sampling_plan: AdjudicationSamplingPlan = Field(description="Pre-label sampling plan")
    success_criteria: list[AdjudicationSuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol packages",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "AdjudicationProtocolPackage":
        """Enforce held-out and dimension/target compatibility invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.adjudicator = self.adjudicator.strip()
        self.coder_qualification = self.coder_qualification.strip()
        self.caution = self.caution.strip()

        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("adjudicator", self.adjudicator)
        _require_non_empty("coder_qualification", self.coder_qualification)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("corpus_sha256 must be a 64-character hex SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError("project_state_sha256 must be a 64-character hex SHA-256")
        if self.coder_count < 1:
            raise ValueError("Adjudication protocol coder_count must be at least 1")
        if not self.target_dimensions:
            raise ValueError("Adjudication protocol target_dimensions is required")
        duplicates = sorted(
            dimension
            for dimension in set(self.target_dimensions)
            if self.target_dimensions.count(dimension) > 1
        )
        if duplicates:
            raise ValueError(
                "Duplicate adjudication target dimension(s): " + ", ".join(duplicates)
            )
        if not self.success_criteria:
            raise ValueError("Adjudication protocol success_criteria is required")

        target_types = set(self.sampling_plan.target_item_types)
        for dimension in self.target_dimensions:
            required_target = _REQUIRED_TARGET_BY_DIMENSION[dimension]
            if required_target not in target_types:
                raise ValueError(
                    f"{dimension} adjudication protocols require {required_target} "
                    "sample target type"
                )

        criterion_dimensions = {criterion.dimension for criterion in self.success_criteria}
        unknown_dimensions = sorted(criterion_dimensions - set(self.target_dimensions))
        if unknown_dimensions:
            raise ValueError(
                "Adjudication success criteria reference unconfigured dimension(s): "
                + ", ".join(unknown_dimensions)
            )
        missing_criteria = sorted(set(self.target_dimensions) - criterion_dimensions)
        if missing_criteria:
            raise ValueError(
                "Adjudication protocol missing success criteria for dimension(s): "
                + ", ".join(missing_criteria)
            )

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out adjudication protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError(
                    "held_out adjudication protocols require contamination_checked=true"
                )
            if not self.registered_before_labeling:
                raise ValueError(
                    "held_out adjudication protocols require registered_before_labeling=true"
                )
            if self.coder_count < 2:
                raise ValueError("held_out adjudication protocols require at least two coders")
        return self


def load_adjudication_protocol(path: str | Path) -> AdjudicationProtocolPackage:
    """Load and validate a versioned adjudication protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Adjudication protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Adjudication protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_adjudication_protocol_payload(raw)


def validate_adjudication_protocol_payload(payload: Any) -> AdjudicationProtocolPackage:
    """Validate a raw JSON payload as a versioned adjudication protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("Adjudication protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Adjudication protocol package must include schema_version=1")
    try:
        return AdjudicationProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid adjudication protocol package: {exc}") from exc


def _require_non_empty(field_name: str, value: str) -> None:
    """Raise if a string field is empty after trimming whitespace."""
    if not value:
        raise ValueError(f"Adjudication protocol {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return true when value is a 64-character hexadecimal SHA-256 string."""
    return bool(_SHA256_RE.fullmatch(value))
