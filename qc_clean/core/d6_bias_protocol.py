"""Validate pre-run D6 bias-audit protocol packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D6BiasDimension = Literal["bias_stratified_d6", "bias_counterfactual_d6"]
D6ProtocolSplit = Literal["held_out", "dev", "public_comparator"]

D6_BIAS_PROTOCOL_CAUTION = (
    "D6 bias protocol packages are pre-run process/provenance metadata only; "
    "they are not a populated bias audit, not causal proof, not bias-free "
    "evidence, not methodological-validity evidence, and not benchmark results."
)


class D6AttributePolicy(BaseModel):
    """Ethical and provenance policy for respondent attributes used in D6."""

    attributes: list[str] = Field(
        description="Respondent attributes planned for stratified/counterfactual analysis"
    )
    attribute_source: str = Field(
        description="Where respondent attribute labels come from"
    )
    ethical_review: str = Field(
        description="Ethical review or permissibility statement for using attributes"
    )
    use_permitted: bool = Field(
        description="Whether this protocol permits using these attributes for D6"
    )
    privacy_protection: str = Field(
        description="How individual privacy is protected in attribute reporting"
    )

    @model_validator(mode="after")
    def require_attribute_policy(self) -> "D6AttributePolicy":
        """Reject unusable or ethically unapproved attribute policies."""
        self.attributes = _clean_unique_strings(
            self.attributes,
            "D6 bias attribute_policy.attributes",
        )
        self.attribute_source = self.attribute_source.strip()
        self.ethical_review = self.ethical_review.strip()
        self.privacy_protection = self.privacy_protection.strip()
        _require_non_empty("attribute_policy.attribute_source", self.attribute_source)
        _require_non_empty("attribute_policy.ethical_review", self.ethical_review)
        _require_non_empty("attribute_policy.privacy_protection", self.privacy_protection)
        if not self.use_permitted:
            raise ValueError("D6 bias attribute_policy requires use_permitted=true")
        return self


class D6BiasCaseSet(BaseModel):
    """Frozen case-set metadata for a D6 bias protocol."""

    case_set_id: str = Field(description="Stable ID for the D6 case set")
    case_set_version: str = Field(description="Version of the D6 case set")
    case_set_path: str | None = Field(
        default=None,
        description="Optional path to the frozen D6 case-set file",
    )
    case_set_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 of the frozen D6 case-set file",
    )
    planned_case_count: int = Field(description="Planned number of D6 cases")
    minimum_group_size: int | None = Field(
        default=None,
        description="Optional pre-registered minimum group size for reporting",
    )

    @model_validator(mode="after")
    def require_case_set_metadata(self) -> "D6BiasCaseSet":
        """Reject underspecified case-set metadata."""
        self.case_set_id = self.case_set_id.strip()
        self.case_set_version = self.case_set_version.strip()
        _require_non_empty("case_set.case_set_id", self.case_set_id)
        _require_non_empty("case_set.case_set_version", self.case_set_version)
        if self.case_set_path is not None:
            self.case_set_path = self.case_set_path.strip() or None
        if self.case_set_sha256 is not None and not _is_sha256(self.case_set_sha256):
            raise ValueError("D6 bias case_set_sha256 must be a 64-character SHA-256")
        if self.planned_case_count < 1:
            raise ValueError("D6 bias planned_case_count must be at least 1")
        if self.minimum_group_size is not None and self.minimum_group_size < 1:
            raise ValueError("D6 bias minimum_group_size must be at least 1")
        return self


class D6StratifiedStrategy(BaseModel):
    """Pre-registered strategy for D6 stratified correctness rows."""

    attributes: list[str] = Field(description="Attributes to use for stratified D6")
    surfaces: list[str] = Field(description="Scored surfaces included in stratified D6")
    correctness_label_source: str = Field(
        description="Source of correctness labels for stratified rows"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future stratified result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future stratified result file",
    )
    minimum_group_size: int | None = Field(
        default=None,
        description="Optional minimum group size for stratified reporting",
    )

    @model_validator(mode="after")
    def require_stratified_strategy(self) -> "D6StratifiedStrategy":
        """Reject unusable stratified strategy metadata."""
        self.attributes = _clean_unique_strings(
            self.attributes,
            "D6 bias stratified_strategy.attributes",
        )
        self.surfaces = _clean_unique_strings(
            self.surfaces,
            "D6 bias stratified_strategy.surfaces",
        )
        self.correctness_label_source = self.correctness_label_source.strip()
        _require_non_empty(
            "stratified_strategy.correctness_label_source",
            self.correctness_label_source,
        )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "D6 bias stratified_strategy.outcome_file_sha256 must be a "
                "64-character SHA-256"
            )
        if self.minimum_group_size is not None and self.minimum_group_size < 1:
            raise ValueError("D6 bias stratified_strategy.minimum_group_size must be at least 1")
        return self


class D6CounterfactualStrategy(BaseModel):
    """Pre-registered strategy for D6 counterfactual identity-cue swaps."""

    identity_cues: list[str] = Field(
        description="Identity cue labels or phrases planned for counterfactual swaps"
    )
    invariant_text_policy: str = Field(
        description="How substantive text is held invariant during swaps"
    )
    generation_method: str = Field(
        description="How counterfactual variants are generated"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future counterfactual result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future counterfactual result file",
    )

    @model_validator(mode="after")
    def require_counterfactual_strategy(self) -> "D6CounterfactualStrategy":
        """Reject unusable counterfactual strategy metadata."""
        self.identity_cues = _clean_unique_strings(
            self.identity_cues,
            "D6 bias counterfactual_strategy.identity_cues",
        )
        self.invariant_text_policy = self.invariant_text_policy.strip()
        self.generation_method = self.generation_method.strip()
        _require_non_empty(
            "counterfactual_strategy.invariant_text_policy",
            self.invariant_text_policy,
        )
        _require_non_empty(
            "counterfactual_strategy.generation_method",
            self.generation_method,
        )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "D6 bias counterfactual_strategy.outcome_file_sha256 must be a "
                "64-character SHA-256"
            )
        return self


class D6BiasSuccessCriterion(BaseModel):
    """One pre-registered success or reporting criterion for D6."""

    dimension: D6BiasDimension = Field(description="D6 scorecard dimension governed")
    metric: str = Field(description="Metric or scorecard field to inspect")
    pass_condition: str = Field(description="Pre-registered pass/fail or reporting condition")
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "D6BiasSuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.metric = self.metric.strip()
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.metric", self.metric)
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class D6BiasProtocolPackage(BaseModel):
    """Versioned protocol package for a pre-run D6 bias audit."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.d6_bias_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the D6 protocol governs")
    dataset_name: str = Field(description="Human-readable D6 dataset name")
    split: D6ProtocolSplit = Field(description="Evaluation split governed by this protocol")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before running")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_run: bool = Field(description="Whether this protocol was registered pre-run")
    dimensions: list[D6BiasDimension] = Field(description="D6 scorecard dimensions governed")
    attribute_policy: D6AttributePolicy = Field(
        description="Ethical and provenance policy for respondent attributes"
    )
    case_set: D6BiasCaseSet = Field(description="Frozen D6 case-set metadata")
    stratified_strategy: D6StratifiedStrategy | None = Field(
        default=None,
        description="Strategy for bias_stratified_d6 when configured",
    )
    counterfactual_strategy: D6CounterfactualStrategy | None = Field(
        default=None,
        description="Strategy for bias_counterfactual_d6 when configured",
    )
    success_criteria: list[D6BiasSuccessCriterion] = Field(
        description="Pre-registered D6 success or reporting criteria"
    )
    caution: str = Field(
        default=D6_BIAS_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D6BiasProtocolPackage":
        """Enforce split/provenance and dimension/strategy invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.caution = self.caution.strip()

        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D6 bias corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError("D6 bias project_state_sha256 must be a 64-character SHA-256")
        _require_unique_dimensions(self.dimensions)
        if not self.success_criteria:
            raise ValueError("D6 bias protocol success_criteria is required")

        configured_dimensions = set(self.dimensions)
        if "bias_stratified_d6" in configured_dimensions:
            if self.stratified_strategy is None:
                raise ValueError("D6 bias_stratified_d6 protocols require stratified_strategy")
            unknown_attributes = sorted(
                set(self.stratified_strategy.attributes)
                - set(self.attribute_policy.attributes)
            )
            if unknown_attributes:
                raise ValueError(
                    "D6 stratified_strategy attributes are missing from "
                    "attribute_policy.attributes: "
                    + ", ".join(unknown_attributes)
                )
        elif self.stratified_strategy is not None:
            raise ValueError(
                "D6 stratified_strategy was supplied but bias_stratified_d6 is not configured"
            )

        if "bias_counterfactual_d6" in configured_dimensions:
            if self.counterfactual_strategy is None:
                raise ValueError(
                    "D6 bias_counterfactual_d6 protocols require counterfactual_strategy"
                )
        elif self.counterfactual_strategy is not None:
            raise ValueError(
                "D6 counterfactual_strategy was supplied but bias_counterfactual_d6 "
                "is not configured"
            )

        criterion_dimensions = {criterion.dimension for criterion in self.success_criteria}
        unknown_criteria = sorted(criterion_dimensions - configured_dimensions)
        if unknown_criteria:
            raise ValueError(
                "D6 bias success criteria reference unconfigured dimension(s): "
                + ", ".join(unknown_criteria)
            )
        missing_criteria = sorted(configured_dimensions - criterion_dimensions)
        if missing_criteria:
            raise ValueError(
                "D6 bias protocol missing success criteria for dimension(s): "
                + ", ".join(missing_criteria)
            )

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D6 bias protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError(
                    "held_out D6 bias protocols require contamination_checked=true"
                )
            if not self.registered_before_run:
                raise ValueError(
                    "held_out D6 bias protocols require registered_before_run=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError("held_out D6 bias protocols require project_state_sha256")
        return self


def load_d6_bias_protocol(path: str | Path) -> D6BiasProtocolPackage:
    """Load and validate a versioned D6 bias protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D6 bias protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D6 bias protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d6_bias_protocol_payload(raw)


def validate_d6_bias_protocol_payload(payload: Any) -> D6BiasProtocolPackage:
    """Validate a raw JSON payload as a versioned D6 bias protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("D6 bias protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D6 bias protocol package must include schema_version=1")
    try:
        return D6BiasProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D6 bias protocol package: {exc}") from exc


def _require_unique_dimensions(dimensions: list[D6BiasDimension]) -> None:
    """Reject empty or duplicate D6 dimension lists."""
    if not dimensions:
        raise ValueError("D6 bias protocol dimensions is required")
    duplicates = sorted(
        dimension for dimension in set(dimensions) if dimensions.count(dimension) > 1
    )
    if duplicates:
        raise ValueError("Duplicate D6 bias dimension(s): " + ", ".join(duplicates))


def _clean_unique_strings(values: list[str], field_name: str) -> list[str]:
    """Trim, validate, and de-duplicate a string list."""
    cleaned = [value.strip() for value in values]
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    empty_indexes = [str(index) for index, value in enumerate(cleaned) if not value]
    if empty_indexes:
        raise ValueError(f"{field_name} contains empty value(s) at index: {', '.join(empty_indexes)}")
    duplicates = sorted(value for value in set(cleaned) if cleaned.count(value) > 1)
    if duplicates:
        raise ValueError(f"Duplicate {field_name}: " + ", ".join(duplicates))
    return cleaned


def _require_non_empty(field_name: str, value: str) -> None:
    """Raise if a string field is empty after trimming whitespace."""
    if not value:
        raise ValueError(f"D6 bias protocol {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return true when value is a 64-character hexadecimal SHA-256."""
    return bool(_SHA256_RE.fullmatch(value))
