"""Validate sampling-frame adequacy protocol and result packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

SamplingFrameAdequacySplit = Literal["held_out", "dev", "public_comparator"]
SamplingFrameAdequacyDimension = Literal[
    "population_alignment",
    "frame_coverage",
    "recruitment_selection_fit",
    "inclusion_exclusion_fit",
    "transferability_limits",
]
SamplingFrameAdequacyRating = Literal[
    "adequate",
    "partial",
    "inadequate",
    "not_assessable",
]

REQUIRED_SAMPLING_FRAME_ADEQUACY_DIMENSIONS: set[SamplingFrameAdequacyDimension] = {
    "population_alignment",
    "frame_coverage",
    "recruitment_selection_fit",
    "inclusion_exclusion_fit",
    "transferability_limits",
}

SAMPLING_FRAME_ADEQUACY_PROTOCOL_CAUTION = (
    "Sampling-frame adequacy protocol packages are pre-evaluation "
    "process/provenance metadata only; they are not sampling-frame adequacy "
    "evidence, not permission for population generalization, not "
    "methodological-validity evidence, and not SOTA evidence."
)

SAMPLING_FRAME_ADEQUACY_RESULT_CAUTION = (
    "Sampling-frame adequacy result packages record reviewer judgments for "
    "preflight; they are not automatically population-generalization "
    "permission, not methodological-validity proof, and not SOTA evidence."
)


class SamplingFrameReviewerPlan(BaseModel):
    """Reviewer plan for sampling-frame adequacy evaluation."""

    reviewer_types: list[str] = Field(
        description="Reviewer types, such as methodologist or domain_expert"
    )
    planned_reviewer_count: int = Field(description="Planned number of reviewers")
    qualification: str = Field(description="Reviewer qualification statement")

    @model_validator(mode="after")
    def require_reviewer_plan(self) -> "SamplingFrameReviewerPlan":
        """Reject empty or underspecified reviewer plans."""
        self.reviewer_types = _clean_unique_strings(
            self.reviewer_types,
            "sampling-frame reviewer_plan.reviewer_types",
        )
        self.qualification = self.qualification.strip()
        _require_non_empty("reviewer_plan.qualification", self.qualification)
        if self.planned_reviewer_count < 1:
            raise ValueError(
                "sampling-frame reviewer_plan.planned_reviewer_count must be at least 1"
            )
        return self


class SamplingFrameAdequacySuccessCriterion(BaseModel):
    """One pre-registered sampling-frame adequacy success criterion."""

    dimension: SamplingFrameAdequacyDimension = Field(
        description="Sampling-frame adequacy dimension governed"
    )
    pass_condition: str = Field(description="Pre-registered pass/fail condition")
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "SamplingFrameAdequacySuccessCriterion":
        """Reject criteria without interpretable conditions."""
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        _require_non_empty("success_criteria.pass_condition", self.pass_condition)
        return self


class SamplingFrameAdequacyProtocolPackage(BaseModel):
    """Versioned protocol package for sampling-frame adequacy evaluation."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["qualitative_coding.sampling_frame_adequacy_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the protocol governs")
    dataset_name: str = Field(description="Human-readable dataset name")
    split: SamplingFrameAdequacySplit = Field(description="Evaluation split")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    corpus_scope_sha256: str | None = Field(
        default=None,
        description="Expected CorpusScope SHA-256 when available",
    )
    scope_frozen: bool = Field(description="Whether scope text/metadata were frozen")
    contamination_checked: bool = Field(description="Whether contamination was checked")
    registered_before_evaluation: bool = Field(
        description="Whether this protocol was registered before evaluation"
    )
    reviewer_plan: SamplingFrameReviewerPlan = Field(description="Reviewer plan")
    dimensions: list[SamplingFrameAdequacyDimension] = Field(
        description="Sampling-frame adequacy dimensions configured"
    )
    outcome_file: str | None = Field(
        default=None,
        description="Optional path to the future adequacy result file",
    )
    outcome_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 lock for the future adequacy result file",
    )
    success_criteria: list[SamplingFrameAdequacySuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=SAMPLING_FRAME_ADEQUACY_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol consumers",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "SamplingFrameAdequacyProtocolPackage":
        """Enforce sampling-frame protocol metadata invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.caution = self.caution.strip()
        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("project_id", self.project_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError(
                "sampling-frame protocol corpus_sha256 must be a 64-character SHA-256"
            )
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "sampling-frame protocol project_state_sha256 must be a 64-character SHA-256"
            )
        if self.corpus_scope_sha256 is not None and not _is_sha256(
            self.corpus_scope_sha256
        ):
            raise ValueError(
                "sampling-frame protocol corpus_scope_sha256 must be a 64-character SHA-256"
            )
        if self.outcome_file is not None:
            self.outcome_file = self.outcome_file.strip() or None
        if self.outcome_file_sha256 is not None and not _is_sha256(
            self.outcome_file_sha256
        ):
            raise ValueError(
                "sampling-frame protocol outcome_file_sha256 must be a 64-character SHA-256"
            )
        _require_required_dimensions(self.dimensions)
        _check_success_criteria_cover_dimensions(self.dimensions, self.success_criteria)
        if self.split == "held_out":
            if not self.scope_frozen:
                raise ValueError("held_out sampling-frame protocols require scope_frozen=true")
            if not self.contamination_checked:
                raise ValueError(
                    "held_out sampling-frame protocols require contamination_checked=true"
                )
            if not self.registered_before_evaluation:
                raise ValueError(
                    "held_out sampling-frame protocols require registered_before_evaluation=true"
                )
            if self.project_state_sha256 is None:
                raise ValueError(
                    "held_out sampling-frame protocols require project_state_sha256"
                )
            if self.corpus_scope_sha256 is None:
                raise ValueError(
                    "held_out sampling-frame protocols require corpus_scope_sha256"
                )
        return self


class SamplingFrameAdequacyEvaluation(BaseModel):
    """One reviewer judgment for one sampling-frame adequacy dimension."""

    reviewer: str = Field(description="Reviewer identifier")
    reviewer_type: str = Field(description="Reviewer type")
    dimension: SamplingFrameAdequacyDimension = Field(
        description="Sampling-frame adequacy dimension evaluated"
    )
    rating: SamplingFrameAdequacyRating = Field(description="Reviewer rating")
    rationale: str = Field(description="Reviewer rationale")
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="Scope/corpus/protocol references used by the reviewer",
    )
    recommendation: str = Field(default="", description="Optional remediation recommendation")

    @model_validator(mode="after")
    def require_evaluation_fields(self) -> "SamplingFrameAdequacyEvaluation":
        """Reject underspecified evaluation rows."""
        self.reviewer = self.reviewer.strip()
        self.reviewer_type = self.reviewer_type.strip()
        self.rationale = self.rationale.strip()
        self.recommendation = self.recommendation.strip()
        _require_non_empty("evaluation.reviewer", self.reviewer)
        _require_non_empty("evaluation.reviewer_type", self.reviewer_type)
        _require_non_empty("evaluation.rationale", self.rationale)
        self.evidence_refs = _clean_unique_strings(
            self.evidence_refs,
            "sampling-frame evidence_refs",
            allow_empty=True,
        )
        return self


class SamplingFrameAdequacyResultPackage(BaseModel):
    """Concrete sampling-frame adequacy reviewer result package."""

    schema_version: Literal[1] = Field(description="Result package schema version")
    package_type: Literal["qualitative_coding.sampling_frame_adequacy_results"] = Field(
        description="Stable result package type"
    )
    protocol_id: str = Field(description="Protocol ID this result follows")
    project_id: str = Field(description="Project ID this result applies to")
    corpus_sha256: str = Field(description="Corpus SHA-256 from protocol time")
    project_state_sha256: str | None = Field(default=None, description="ProjectState SHA-256")
    corpus_scope_sha256: str | None = Field(default=None, description="CorpusScope SHA-256")
    evaluations: list[SamplingFrameAdequacyEvaluation] = Field(
        description="Reviewer judgments by sampling-frame adequacy dimension"
    )
    caution: str = Field(
        default=SAMPLING_FRAME_ADEQUACY_RESULT_CAUTION,
        description="Claim-discipline caveat for result consumers",
    )

    @model_validator(mode="after")
    def require_result_invariants(self) -> "SamplingFrameAdequacyResultPackage":
        """Reject malformed result packages before cross-checking."""
        self.protocol_id = self.protocol_id.strip()
        self.project_id = self.project_id.strip()
        self.caution = self.caution.strip()
        _require_non_empty("result.protocol_id", self.protocol_id)
        _require_non_empty("result.project_id", self.project_id)
        _require_non_empty("result.caution", self.caution)
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("sampling-frame result corpus_sha256 must be a SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(
            self.project_state_sha256
        ):
            raise ValueError(
                "sampling-frame result project_state_sha256 must be a SHA-256"
            )
        if self.corpus_scope_sha256 is not None and not _is_sha256(
            self.corpus_scope_sha256
        ):
            raise ValueError(
                "sampling-frame result corpus_scope_sha256 must be a SHA-256"
            )
        if not self.evaluations:
            raise ValueError("sampling-frame result package requires evaluations")
        return self


def load_sampling_frame_adequacy_protocol(
    path: str | Path,
) -> SamplingFrameAdequacyProtocolPackage:
    """Load and validate a sampling-frame adequacy protocol package."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"sampling-frame adequacy protocol file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"sampling-frame adequacy protocol file '{path}' is not valid JSON: {exc}"
        ) from exc
    return validate_sampling_frame_adequacy_protocol_payload(raw)


def validate_sampling_frame_adequacy_protocol_payload(
    payload: Any,
) -> SamplingFrameAdequacyProtocolPackage:
    """Validate a raw JSON payload as a sampling-frame adequacy protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("sampling-frame adequacy protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError(
            "sampling-frame adequacy protocol package must include schema_version=1"
        )
    try:
        return SamplingFrameAdequacyProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            f"Invalid sampling-frame adequacy protocol package: {exc}"
        ) from exc


def validate_sampling_frame_adequacy_result_payload(
    payload: Any,
) -> SamplingFrameAdequacyResultPackage:
    """Validate a raw JSON payload as a sampling-frame adequacy result package."""
    if not isinstance(payload, dict):
        raise ValueError("sampling-frame adequacy result package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError(
            "sampling-frame adequacy result package must include schema_version=1"
        )
    try:
        return SamplingFrameAdequacyResultPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid sampling-frame adequacy result package: {exc}") from exc


def _require_required_dimensions(
    dimensions: list[SamplingFrameAdequacyDimension],
) -> None:
    """Reject duplicate or incomplete sampling-frame dimension configuration."""
    if not dimensions:
        raise ValueError("sampling-frame adequacy dimensions are required")
    duplicates = sorted(
        dimension for dimension in set(dimensions) if dimensions.count(dimension) > 1
    )
    if duplicates:
        raise ValueError(
            "Duplicate sampling-frame adequacy dimension(s): " + ", ".join(duplicates)
        )
    missing = sorted(REQUIRED_SAMPLING_FRAME_ADEQUACY_DIMENSIONS - set(dimensions))
    if missing:
        raise ValueError(
            "sampling-frame adequacy dimensions missing required dimension(s): "
            + ", ".join(missing)
        )


def _check_success_criteria_cover_dimensions(
    dimensions: list[SamplingFrameAdequacyDimension],
    criteria: list[SamplingFrameAdequacySuccessCriterion],
) -> None:
    """Reject missing or out-of-scope success criteria."""
    if not criteria:
        raise ValueError("sampling-frame adequacy success_criteria are required")
    dimension_set = set(dimensions)
    criterion_dimensions = {criterion.dimension for criterion in criteria}
    unknown = sorted(criterion_dimensions - dimension_set)
    if unknown:
        raise ValueError(
            "sampling-frame adequacy success criteria reference unconfigured "
            "dimension(s): "
            + ", ".join(unknown)
        )
    missing = sorted(dimension_set - criterion_dimensions)
    if missing:
        raise ValueError(
            "sampling-frame adequacy protocol missing success criteria for "
            "dimension(s): "
            + ", ".join(missing)
        )


def _clean_unique_strings(
    values: list[str],
    field_name: str,
    *,
    allow_empty: bool = False,
) -> list[str]:
    """Trim, validate, and de-duplicate a string list."""
    cleaned = [value.strip() for value in values]
    if not cleaned and allow_empty:
        return []
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
        raise ValueError(f"sampling-frame adequacy {field_name} must be non-empty")


def _is_sha256(value: str) -> bool:
    """Return true when value is a 64-character SHA-256 hex digest."""
    return bool(_SHA256_RE.fullmatch(value))
