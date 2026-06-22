"""D7 retrieval comparison protocol package contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")

D7_COMPARISON_PROTOCOL_CAUTION = (
    "D7 comparison protocol validation is process metadata only; it is not "
    "held-out D7 evidence, live-baseline evidence, methodological-validity "
    "evidence, or superiority evidence."
)


class D7ExpectedRetrievalPrediction(BaseModel):
    """One expected D7 retrieval prediction package/baseline."""

    baseline_name: str = Field(description="Expected baseline record name")
    retrieval_mode: str = Field(description="Expected retrieval mode")
    candidates_per_claim: int = Field(description="Expected candidate limit per claim")
    max_targets: int = Field(description="Expected maximum target claims considered")
    embedding_model: str | None = Field(
        default=None,
        description="Expected embedding model for embedding_hybrid retrieval",
    )
    embedding_dimensions: int | None = Field(
        default=None,
        description="Expected embedding dimensions when configured",
    )
    trace_id: str = Field(description="Expected retrieval export trace ID")
    max_budget: float = Field(description="Expected retrieval export max budget")
    prediction_file_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hash lock for the prediction file",
    )

    @model_validator(mode="after")
    def require_expected_prediction_invariants(self) -> "D7ExpectedRetrievalPrediction":
        """Enforce meaningful retrieval expectation metadata."""
        if not self.baseline_name.strip():
            raise ValueError("D7 expected baseline_name must be non-empty")
        if not self.retrieval_mode.strip():
            raise ValueError("D7 expected retrieval_mode must be non-empty")
        if self.candidates_per_claim < 1:
            raise ValueError("D7 expected candidates_per_claim must be at least 1")
        if self.max_targets < 1:
            raise ValueError("D7 expected max_targets must be at least 1")
        if self.embedding_model is not None and not self.embedding_model.strip():
            raise ValueError("D7 expected embedding_model must be non-empty when supplied")
        if self.retrieval_mode == "embedding_hybrid" and not self.embedding_model:
            raise ValueError("D7 embedding_hybrid expectations require embedding_model")
        if self.embedding_dimensions is not None and self.embedding_dimensions < 1:
            raise ValueError("D7 expected embedding_dimensions must be at least 1 when supplied")
        if not self.trace_id.strip():
            raise ValueError("D7 expected trace_id must be non-empty")
        if self.max_budget < 0:
            raise ValueError("D7 expected max_budget must be non-negative")
        if self.prediction_file_sha256 is not None and not _is_sha256(self.prediction_file_sha256):
            raise ValueError("D7 expected prediction_file_sha256 must be a 64-character SHA-256")
        return self


class D7ComparisonProtocolPackage(BaseModel):
    """Pre-registered protocol for a D7 retrieval comparison run."""

    schema_version: Literal[1] = Field(description="D7 comparison protocol schema version")
    package_type: Literal["qualitative_coding.d7_retrieval_comparison_protocol"] = Field(
        description="Stable package type identifier"
    )
    protocol_id: str = Field(description="Stable protocol ID")
    project_id: str = Field(description="Project ID the comparison is registered for")
    dataset_name: str = Field(description="Human-readable dataset name")
    split: Literal["held_out", "dev", "public_comparator"] = Field(
        description="Evaluation split represented by this comparison"
    )
    gold_set_id: str = Field(description="Expected D7 gold-set ID")
    corpus_sha256: str = Field(description="Expected corpus SHA-256")
    project_state_sha256: str | None = Field(
        default=None,
        description="Expected ProjectState SHA-256 when available",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before scoring")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_run: bool = Field(description="Whether this protocol was registered pre-run")
    expected_predictions: list[D7ExpectedRetrievalPrediction] = Field(
        description="Prediction baselines expected in the comparison"
    )
    success_criteria: list[str] = Field(description="Human-readable pre-registered success criteria")
    caution: str = Field(description="Claim-discipline caveat for protocol consumers")

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "D7ComparisonProtocolPackage":
        """Enforce split/provenance invariants and unique expected baselines."""
        if not self.protocol_id.strip():
            raise ValueError("D7 comparison protocol_id must be non-empty")
        if not self.project_id.strip():
            raise ValueError("D7 comparison project_id must be non-empty")
        if not self.dataset_name.strip():
            raise ValueError("D7 comparison dataset_name must be non-empty")
        if not self.gold_set_id.strip():
            raise ValueError("D7 comparison gold_set_id must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D7 comparison corpus_sha256 must be a 64-character SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError("D7 comparison project_state_sha256 must be a 64-character SHA-256")
        if not self.expected_predictions:
            raise ValueError("D7 comparison protocol requires expected_predictions")
        if not self.success_criteria:
            raise ValueError("D7 comparison protocol requires success_criteria")
        if not self.caution.strip():
            raise ValueError("D7 comparison caution must be non-empty")

        names = [prediction.baseline_name for prediction in self.expected_predictions]
        duplicates = sorted(name for name in set(names) if names.count(name) > 1)
        if duplicates:
            raise ValueError("Duplicate D7 expected baseline name(s): " + ", ".join(duplicates))

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D7 comparison protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D7 comparison protocols require contamination_checked=true")
            if not self.registered_before_run:
                raise ValueError("held_out D7 comparison protocols require registered_before_run=true")
            if self.project_state_sha256 is None:
                raise ValueError("held_out D7 comparison protocols require project_state_sha256")
        return self


def load_d7_comparison_protocol(path: Path | str) -> D7ComparisonProtocolPackage:
    """Load and validate a D7 comparison protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 comparison protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 comparison protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_d7_comparison_protocol_payload(raw)


def validate_d7_comparison_protocol_payload(payload: Any) -> D7ComparisonProtocolPackage:
    """Validate a raw JSON payload as a D7 comparison protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("D7 comparison protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D7 comparison protocol package must include schema_version=1")
    try:
        return D7ComparisonProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 comparison protocol package: {exc}") from exc


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))
