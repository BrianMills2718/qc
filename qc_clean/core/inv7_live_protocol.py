"""Validate pre-run INV-7 live prompt-injection benchmark protocols."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


Inv7ProtocolSplit = Literal["held_out", "dev", "public_comparator", "canary"]

INV7_LIVE_PROTOCOL_CAUTION = (
    "INV-7 live protocol packages are pre-run provenance metadata only; they "
    "are not live results, not prompt-injection robustness evidence, not "
    "model-obedience evidence, not validity evidence, and not benchmark results."
)


class Inv7LiveSuccessCriterion(BaseModel):
    """One pre-registered success or reporting criterion for a live INV-7 run."""

    metric: str = Field(description="Metric or scorecard field to inspect")
    pass_condition: str = Field(description="Pre-registered pass/fail or reporting condition")
    notes: str = Field(default="", description="Optional criterion caveats")

    @model_validator(mode="after")
    def require_non_empty_fields(self) -> "Inv7LiveSuccessCriterion":
        """Reject criteria that cannot be interpreted."""
        self.metric = self.metric.strip()
        self.pass_condition = self.pass_condition.strip()
        self.notes = self.notes.strip()
        if not self.metric:
            raise ValueError("INV-7 live success criterion metric must be non-empty")
        if not self.pass_condition:
            raise ValueError("INV-7 live success criterion pass_condition must be non-empty")
        return self


class Inv7LiveProtocolPackage(BaseModel):
    """Versioned protocol package for a pre-run live INV-7 benchmark."""

    schema_version: Literal[1] = Field(description="Protocol package schema version")
    package_type: Literal["inv7_live_protocol"] = Field(description="Protocol package kind")
    protocol_id: str = Field(description="Stable protocol ID")
    dataset_name: str = Field(description="Human-readable live benchmark dataset name")
    split: Inv7ProtocolSplit = Field(description="Evaluation split governed by this protocol")
    fixture_set_id: str = Field(description="Stable ID for the fixture set")
    fixture_set_version: str = Field(description="Version of the fixture set")
    fixture_prompt_hashes: dict[str, str] = Field(
        description="SHA-256 hashes of exact live fixture prompts keyed by fixture_id"
    )
    model: str = Field(description="Live model name to run")
    trace_id: str = Field(description="llm_client trace ID prefix for this run")
    max_budget: float = Field(description="Maximum budget for the live run")
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before running")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    registered_before_run: bool = Field(
        description="Whether this protocol was registered before live execution"
    )
    success_criteria: list[Inv7LiveSuccessCriterion] = Field(
        description="Pre-registered success or reporting criteria"
    )
    caution: str = Field(
        default=INV7_LIVE_PROTOCOL_CAUTION,
        description="Claim-discipline caveat for protocol packages",
    )

    @model_validator(mode="after")
    def require_protocol_invariants(self) -> "Inv7LiveProtocolPackage":
        """Enforce pre-run protocol invariants."""
        self.protocol_id = self.protocol_id.strip()
        self.dataset_name = self.dataset_name.strip()
        self.fixture_set_id = self.fixture_set_id.strip()
        self.fixture_set_version = self.fixture_set_version.strip()
        self.model = self.model.strip()
        self.trace_id = self.trace_id.strip()
        self.caution = self.caution.strip()

        _require_non_empty("protocol_id", self.protocol_id)
        _require_non_empty("dataset_name", self.dataset_name)
        _require_non_empty("fixture_set_id", self.fixture_set_id)
        _require_non_empty("fixture_set_version", self.fixture_set_version)
        _require_non_empty("model", self.model)
        _require_non_empty("trace_id", self.trace_id)
        if self.max_budget <= 0:
            raise ValueError("INV-7 live protocol max_budget must be greater than 0")
        _validate_fixture_prompt_hashes(self.fixture_prompt_hashes)
        if not self.success_criteria:
            raise ValueError("INV-7 live protocol success_criteria is required")

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out INV-7 live protocols require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError(
                    "held_out INV-7 live protocols require contamination_checked=true"
                )
            if not self.registered_before_run:
                raise ValueError(
                    "held_out INV-7 live protocols require registered_before_run=true"
                )
        return self


def load_inv7_live_protocol(path: str | Path) -> Inv7LiveProtocolPackage:
    """Load and validate a versioned INV-7 live protocol package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"INV-7 live protocol file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INV-7 live protocol file '{path}' is not valid JSON: {exc}") from exc
    return validate_inv7_live_protocol_payload(raw)


def validate_inv7_live_protocol_payload(payload: Any) -> Inv7LiveProtocolPackage:
    """Validate a raw JSON payload as a versioned INV-7 live protocol package."""
    if not isinstance(payload, dict):
        raise ValueError("INV-7 live protocol package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("INV-7 live protocol package must include schema_version=1")
    try:
        return Inv7LiveProtocolPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid INV-7 live protocol package: {exc}") from exc


def _validate_fixture_prompt_hashes(fixture_prompt_hashes: dict[str, str]) -> None:
    """Reject empty fixture IDs or malformed prompt hashes."""
    if not fixture_prompt_hashes:
        raise ValueError("INV-7 live protocol fixture_prompt_hashes is required")
    empty_ids = sorted(fixture_id for fixture_id in fixture_prompt_hashes if not fixture_id.strip())
    if empty_ids:
        raise ValueError("INV-7 live protocol fixture_prompt_hashes fixture_id must be non-empty")
    malformed = sorted(
        fixture_id
        for fixture_id, digest in fixture_prompt_hashes.items()
        if not _is_lower_sha256_hex(digest)
    )
    if malformed:
        raise ValueError(
            "INV-7 live protocol fixture_prompt_hashes values must be lowercase "
            f"SHA-256 hex digests for fixture_id(s): {', '.join(malformed)}"
        )


def _is_lower_sha256_hex(value: str) -> bool:
    """Return true for lowercase 64-character SHA-256 hex strings."""
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _require_non_empty(field_name: str, value: str) -> None:
    """Raise if a string field is empty after trimming whitespace."""
    if not value:
        raise ValueError(f"INV-7 live protocol {field_name} must be non-empty")
