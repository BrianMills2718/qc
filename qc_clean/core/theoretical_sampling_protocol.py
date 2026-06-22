"""Theoretical-sampling protocol package contracts for INV-4."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

THEORETICAL_SAMPLING_PROTOCOL_CAUTION = (
    "Theoretical sampling protocol validation is process metadata only; it is "
    "not sampling adequacy evidence, not methodological saturation evidence, "
    "not full grounded-theory evidence, and not a SOTA claim."
)

TheoreticalSamplingGapType = Literal[
    "needs_properties",
    "needs_dimensions",
    "needs_supporting_applications",
    "needs_supporting_documents",
]


class TheoreticalSamplingThresholds(BaseModel):
    """Category adequacy thresholds used to target theoretical sampling."""

    min_properties: int = Field(description="Minimum named properties expected for targeted categories")
    min_dimensions: int = Field(description="Minimum dimensional variations expected for targeted categories")
    min_supporting_applications: int = Field(
        description="Minimum supporting applications expected for targeted categories"
    )
    min_supporting_documents: int = Field(
        description="Minimum supporting documents expected for targeted categories"
    )

    @model_validator(mode="after")
    def require_non_negative_thresholds(self) -> "TheoreticalSamplingThresholds":
        """Reject nonsensical negative adequacy thresholds."""
        for field_name in [
            "min_properties",
            "min_dimensions",
            "min_supporting_applications",
            "min_supporting_documents",
        ]:
            if getattr(self, field_name) < 0:
                raise ValueError(f"Theoretical sampling {field_name} must be non-negative")
        return self


class TheoreticalSamplingProtocolPackage(BaseModel):
    """Pre-registered protocol for a theoretical-sampling cycle."""

    schema_version: Literal[1] = Field(description="Theoretical sampling protocol schema version")
    package_type: Literal["qualitative_coding.theoretical_sampling_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol identifier")
    project_id: str = Field(description="Project ID the sampling protocol applies to")
    corpus_sha256: str = Field(description="SHA-256 hash of the corpus payload at protocol time")
    project_state_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hash of the ProjectState at protocol time",
    )
    registered_before_sampling: bool = Field(
        description="Whether this protocol was registered before data selection/collection"
    )
    candidate_source: Literal["loaded_uncoded_documents", "external_recruitment_pool", "mixed"] = Field(
        description="Source of candidate cases for theoretical sampling"
    )
    collection_mode: Literal["select_existing_documents", "collect_new_data", "mixed"] = Field(
        description="Whether the protocol selects loaded documents, collects new data, or both"
    )
    target_gap_codes: list[str] = Field(
        description="Code/category IDs whose diagnostic gaps motivate this sampling cycle"
    )
    target_gap_types: list[TheoreticalSamplingGapType] = Field(
        description="Diagnostic gap types the sampling cycle is intended to address"
    )
    thresholds: TheoreticalSamplingThresholds = Field(
        description="Category adequacy thresholds used by this protocol"
    )
    max_suggestions: int = Field(description="Maximum number of sampling suggestions to produce")
    collection_rules: list[str] = Field(
        description="Protocol rules for selecting or collecting additional cases"
    )
    stopping_rule: str = Field(
        description="Human-readable stopping rule for the sampling cycle"
    )
    success_criteria: list[str] = Field(
        description="Pre-registered criteria for considering the sampling cycle complete"
    )
    caution: str = Field(description="Claim-discipline caveat for protocol consumers")
    notes: str = Field(default="", description="Optional protocol notes")

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "TheoreticalSamplingProtocolPackage":
        """Reject underspecified or internally inconsistent sampling protocols."""
        if not self.protocol_id.strip():
            raise ValueError("Theoretical sampling protocol_id must be non-empty")
        if not self.project_id.strip():
            raise ValueError("Theoretical sampling project_id must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("Theoretical sampling corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError(
                "Theoretical sampling project_state_sha256 must be a 64-character SHA-256"
            )
        if not self.registered_before_sampling:
            raise ValueError("Theoretical sampling protocols must be registered before sampling")
        if self.max_suggestions < 1:
            raise ValueError("Theoretical sampling max_suggestions must be at least 1")
        if (
            self.candidate_source == "loaded_uncoded_documents"
            and self.collection_mode == "collect_new_data"
        ):
            raise ValueError(
                "loaded_uncoded_documents candidate_source cannot use collect_new_data mode"
            )
        if (
            self.candidate_source == "external_recruitment_pool"
            and self.collection_mode == "select_existing_documents"
        ):
            raise ValueError(
                "external_recruitment_pool candidate_source cannot use select_existing_documents mode"
            )
        self.target_gap_codes = _normalize_unique_nonempty(
            self.target_gap_codes,
            label="target_gap_code",
        )
        if not self.target_gap_codes:
            raise ValueError("Theoretical sampling target_gap_codes is required")
        self.target_gap_types = _normalize_unique_nonempty(
            list(self.target_gap_types),
            label="target_gap_type",
        )
        if not self.target_gap_types:
            raise ValueError("Theoretical sampling target_gap_types is required")
        self.collection_rules = _normalize_unique_nonempty(
            self.collection_rules,
            label="collection_rule",
            unique=False,
        )
        if not self.collection_rules:
            raise ValueError("Theoretical sampling collection_rules is required")
        if not self.stopping_rule.strip():
            raise ValueError("Theoretical sampling stopping_rule must be non-empty")
        self.success_criteria = _normalize_unique_nonempty(
            self.success_criteria,
            label="success_criterion",
            unique=False,
        )
        if not self.success_criteria:
            raise ValueError("Theoretical sampling success_criteria is required")
        if not self.caution.strip():
            raise ValueError("Theoretical sampling caution must be non-empty")
        return self


def load_theoretical_sampling_protocol(
    path: Path | str,
) -> TheoreticalSamplingProtocolPackage:
    """Load and validate a theoretical-sampling protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(
            f"Theoretical sampling protocol file '{path}' could not be read: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Theoretical sampling protocol file '{path}' is not valid JSON: {exc}"
        ) from exc
    return validate_theoretical_sampling_protocol_payload(raw)


def validate_theoretical_sampling_protocol_payload(
    payload: Any,
) -> TheoreticalSamplingProtocolPackage:
    """Validate a raw JSON payload as a theoretical-sampling protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("Theoretical sampling protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Theoretical sampling protocol package must include schema_version=1")
    try:
        return TheoreticalSamplingProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid theoretical sampling protocol package: {exc}") from exc


def _normalize_unique_nonempty(
    values: list[str],
    *,
    label: str,
    unique: bool = True,
) -> list[str]:
    normalized = [value.strip() for value in values if value.strip()]
    if unique:
        duplicates = sorted(value for value in set(normalized) if normalized.count(value) > 1)
        if duplicates:
            raise ValueError(
                f"Duplicate theoretical sampling {label}(s): " + ", ".join(duplicates)
            )
    return normalized


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))
