"""Versioned INV-7 prompt-injection package contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class Inv7PromptInjectionOutcome(BaseModel):
    """One prompt-injection fixture outcome inside an INV-7 package."""

    model_config = ConfigDict(extra="allow")

    fixture_id: str = Field(description="Stable ID for the adversarial fixture")
    surface: str = Field(description="Prompt surface tested, such as thematic_coding")
    attack_type: str = Field(
        default="unspecified",
        description="Attack class, such as direct_instruction_override",
    )
    attack_succeeded: bool = Field(description="True when the attack payload was followed or leaked")
    failure_mode: str | None = Field(default=None, description="Optional failure explanation")
    evaluator: str = Field(default="unspecified", description="Evaluator or harness")
    notes: str = Field(default="", description="Optional human-readable notes")

    @model_validator(mode="after")
    def require_stable_fixture_keys(self) -> "Inv7PromptInjectionOutcome":
        """Normalize grouping keys and require stable fixture identity."""
        self.fixture_id = self.fixture_id.strip()
        self.surface = self.surface.strip()
        self.attack_type = self.attack_type.strip() or "unspecified"
        self.evaluator = self.evaluator.strip() or "unspecified"
        if not self.fixture_id:
            raise ValueError("INV-7 fixture_id must be non-empty")
        if not self.surface:
            raise ValueError("INV-7 surface must be non-empty")
        return self


class Inv7PromptInjectionPackage(BaseModel):
    """Versioned package for INV-7 structural or live prompt-injection outcomes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="INV-7 package schema version")
    package_id: str = Field(description="Stable ID for this prompt-injection package")
    mode: Literal["structural", "live_model"] = Field(description="Fixture execution mode")
    split: Literal["canary", "dev", "held_out", "public_comparator"] = Field(
        description="Evaluation split represented by this package"
    )
    fixture_set_id: str = Field(description="Stable ID for the fixture set")
    fixture_set_version: str = Field(description="Version of the fixture set")
    prompt_frozen: bool = Field(description="Whether fixture prompts were frozen before scoring")
    contamination_checked: bool = Field(description="Whether contamination checks were performed")
    evaluator: str = Field(description="Package-level evaluator or harness name")
    model: str | None = Field(default=None, description="Live model name for live_model packages")
    trace_id: str | None = Field(default=None, description="llm_client trace ID for live_model packages")
    max_budget: float | None = Field(default=None, ge=0, description="Live run budget, when applicable")
    fixture_prompt_hashes: dict[str, str] | None = Field(
        default=None,
        description="Optional SHA-256 hashes of exact live fixture prompts keyed by fixture_id",
    )
    note: str = Field(default="", description="Human-readable package caveat")
    prompt_injection_evaluations: list[Inv7PromptInjectionOutcome] = Field(
        description="Prompt-injection fixture outcomes"
    )

    @property
    def total_fixtures(self) -> int:
        """Number of fixture outcomes in the package."""
        return len(self.prompt_injection_evaluations)

    @property
    def failed(self) -> int:
        """Number of fixture outcomes where the attack succeeded."""
        return sum(1 for item in self.prompt_injection_evaluations if item.attack_succeeded)

    @property
    def passed(self) -> int:
        """Number of fixture outcomes where the attack did not succeed."""
        return self.total_fixtures - self.failed

    @model_validator(mode="after")
    def require_package_invariants(self) -> "Inv7PromptInjectionPackage":
        """Reject packages without enough protocol metadata to interpret."""
        self.package_id = self.package_id.strip()
        self.fixture_set_id = self.fixture_set_id.strip()
        self.fixture_set_version = self.fixture_set_version.strip()
        self.evaluator = self.evaluator.strip()
        if not self.package_id:
            raise ValueError("INV-7 package_id must be non-empty")
        if not self.fixture_set_id:
            raise ValueError("INV-7 fixture_set_id must be non-empty")
        if not self.fixture_set_version:
            raise ValueError("INV-7 fixture_set_version must be non-empty")
        if not self.evaluator:
            raise ValueError("INV-7 evaluator must be non-empty")
        if not self.prompt_injection_evaluations:
            raise ValueError("INV-7 package requires at least one fixture outcome")

        fixture_ids = [item.fixture_id for item in self.prompt_injection_evaluations]
        duplicates = sorted(fixture_id for fixture_id in set(fixture_ids) if fixture_ids.count(fixture_id) > 1)
        if duplicates:
            raise ValueError("Duplicate INV-7 fixture_id(s): " + ", ".join(duplicates))

        if self.fixture_prompt_hashes is not None:
            _validate_fixture_prompt_hashes(
                self.fixture_prompt_hashes,
                expected_fixture_ids=set(fixture_ids),
            )

        if self.mode == "live_model":
            if not self.model or not self.model.strip():
                raise ValueError("live_model INV-7 packages require model metadata")
            if not self.trace_id or not self.trace_id.strip():
                raise ValueError("live_model INV-7 packages require trace_id metadata")
            if self.max_budget is None:
                raise ValueError("live_model INV-7 packages require max_budget metadata")
            self.model = self.model.strip()
            self.trace_id = self.trace_id.strip()

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out INV-7 packages require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out INV-7 packages require contamination_checked=true")
        return self


def _validate_fixture_prompt_hashes(
    fixture_prompt_hashes: dict[str, str],
    *,
    expected_fixture_ids: set[str],
) -> None:
    """Validate optional exact-prompt hashes against fixture IDs."""
    hash_fixture_ids = set(fixture_prompt_hashes)
    if hash_fixture_ids != expected_fixture_ids:
        missing = sorted(expected_fixture_ids - hash_fixture_ids)
        extra = sorted(hash_fixture_ids - expected_fixture_ids)
        raise ValueError(
            "fixture_prompt_hashes keys must exactly match prompt_injection_evaluations "
            f"fixture_id values; missing={missing}, extra={extra}"
        )

    malformed = sorted(
        fixture_id
        for fixture_id, digest in fixture_prompt_hashes.items()
        if not _is_lower_sha256_hex(digest)
    )
    if malformed:
        raise ValueError(
            "fixture_prompt_hashes values must be lowercase SHA-256 hex digests "
            f"for fixture_id(s): {', '.join(malformed)}"
        )


def _is_lower_sha256_hex(value: str) -> bool:
    """Return true for lowercase 64-character SHA-256 hex strings."""
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def load_inv7_prompt_injection_package(path: Path | str) -> Inv7PromptInjectionPackage:
    """Load and validate a schema_version=1 INV-7 prompt-injection package."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"INV-7 prompt-injection package '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"INV-7 prompt-injection package '{path}' is not valid JSON: {exc}") from exc
    return validate_inv7_prompt_injection_package_payload(raw)


def validate_inv7_prompt_injection_package_payload(payload: Any) -> Inv7PromptInjectionPackage:
    """Validate a raw JSON payload as a versioned INV-7 package."""
    if not isinstance(payload, dict):
        raise ValueError("INV-7 prompt-injection package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("INV-7 prompt-injection package must include schema_version=1")
    try:
        return Inv7PromptInjectionPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid INV-7 prompt-injection package: {exc}") from exc


def prompt_injection_payload_for_scorecard(payload: Any) -> list[dict[str, Any]]:
    """Validate prompt-injection input and return Phase 0 scorecard outcomes."""
    if isinstance(payload, dict) and payload.get("schema_version") == 1:
        package = validate_inv7_prompt_injection_package_payload(payload)
        return [
            item.model_dump(mode="json")
            for item in package.prompt_injection_evaluations
        ]
    if isinstance(payload, dict) and isinstance(payload.get("prompt_injection_evaluations"), list):
        return _validated_outcome_payload(payload["prompt_injection_evaluations"])
    if isinstance(payload, list):
        return _validated_outcome_payload(payload)
    raise ValueError(
        "Prompt injection file must be a JSON list of fixture outcomes, an "
        "object with a 'prompt_injection_evaluations' list, or a schema_version=1 "
        "INV-7 prompt-injection package"
    )


def _validated_outcome_payload(raw: list[Any]) -> list[dict[str, Any]]:
    try:
        outcomes = [Inv7PromptInjectionOutcome.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid prompt_injection_evaluations metadata: {exc}") from exc
    return [item.model_dump(mode="json") for item in outcomes]
