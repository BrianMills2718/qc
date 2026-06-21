"""D7 held-out gold-set package contracts and validation helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")


class DisconfirmationGoldAnchor(BaseModel):
    """Human/adjudicated contrary-evidence anchor used for D7 scoring."""

    target_claim_id: str = Field(description="AnalyticClaim ID the gold contrary evidence challenges")
    doc_id: str = Field(description="Document containing the contrary evidence")
    start_char: int | None = Field(default=None, description="Start offset of the gold source span")
    end_char: int | None = Field(default=None, description="End offset of the gold source span")
    segment_id: str | None = Field(default=None, description="Segment ID when span offsets are unavailable")
    quote_text: str = Field(default="", description="Optional evidence text for human inspection")

    @model_validator(mode="after")
    def require_exact_key(self) -> "DisconfirmationGoldAnchor":
        """Require a deterministic comparison key for every gold record."""
        has_start = self.start_char is not None
        has_end = self.end_char is not None
        if has_start != has_end:
            raise ValueError("D7 gold anchors must provide both start_char and end_char")
        if has_start and has_end:
            if self.start_char is None or self.end_char is None:
                raise ValueError("D7 gold span offsets are incomplete")
            if self.start_char < 0 or self.end_char <= self.start_char:
                raise ValueError("D7 gold span offsets must satisfy 0 <= start_char < end_char")
            return self
        if not self.segment_id:
            raise ValueError("D7 gold anchors require span offsets or a segment_id")
        return self


class D7AdjudicationMetadata(BaseModel):
    """Human-adjudication metadata for a D7 gold-set package."""

    coder_count: int = Field(description="Number of independent human coders before adjudication")
    adjudicator: str = Field(description="Adjudicator identifier, name, or redacted label")
    protocol: str = Field(description="Short description of the adjudication protocol")
    human_human_agreement: dict[str, Any] | None = Field(
        default=None,
        description="Optional human-ceiling agreement metrics, such as kappa/alpha/AC1",
    )
    notes: str = Field(default="", description="Optional caveats for the adjudication process")

    @model_validator(mode="after")
    def require_protocol(self) -> "D7AdjudicationMetadata":
        """Require human-process metadata to be meaningful, not blank."""
        if self.coder_count < 1:
            raise ValueError("D7 adjudication coder_count must be at least 1")
        if not self.adjudicator.strip():
            raise ValueError("D7 adjudication adjudicator must be non-empty")
        if not self.protocol.strip():
            raise ValueError("D7 adjudication protocol must be non-empty")
        return self


class D7GoldSetPackage(BaseModel):
    """Versioned D7 contrary-evidence gold-set package."""

    schema_version: Literal[1] = Field(description="D7 gold-set package schema version")
    gold_set_id: str = Field(description="Stable ID for this gold set")
    dataset_name: str = Field(description="Human-readable dataset name")
    split: Literal["held_out", "dev", "public_comparator"] = Field(
        description="Evaluation split represented by this gold set"
    )
    corpus_sha256: str = Field(description="SHA-256 hash of the corpus payload this gold set annotates")
    project_state_sha256: str | None = Field(
        default=None,
        description="Optional SHA-256 hash of the exact ProjectState used to build the gold set",
    )
    prompt_frozen: bool = Field(description="Whether prompts/models were frozen before scoring this split")
    contamination_checked: bool = Field(description="Whether train/test contamination checks were performed")
    adjudication: D7AdjudicationMetadata = Field(description="Human adjudication process metadata")
    contrary_evidence: list[DisconfirmationGoldAnchor] = Field(
        description="Adjudicated contrary-evidence anchors"
    )

    @model_validator(mode="after")
    def require_gold_set_invariants(self) -> "D7GoldSetPackage":
        """Enforce held-out package provenance and exact-key uniqueness."""
        if not self.gold_set_id.strip():
            raise ValueError("D7 gold_set_id must be non-empty")
        if not self.dataset_name.strip():
            raise ValueError("D7 dataset_name must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D7 corpus_sha256 must be a 64-character hex SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError("D7 project_state_sha256 must be a 64-character hex SHA-256")
        if not self.contrary_evidence:
            raise ValueError("D7 gold set requires at least one contrary_evidence anchor")

        keys = [d7_gold_anchor_key(anchor) for anchor in self.contrary_evidence]
        duplicates = sorted(key for key in set(keys) if keys.count(key) > 1)
        if duplicates:
            raise ValueError("Duplicate D7 gold anchor key(s): " + ", ".join(duplicates))

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D7 gold sets require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D7 gold sets require contamination_checked=true")
            if self.adjudication.coder_count < 2:
                raise ValueError("held_out D7 gold sets require at least two coders")
        return self


def load_d7_gold_set(path: Path | str) -> D7GoldSetPackage:
    """Load and validate a versioned D7 gold-set package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D7 gold-set file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D7 gold-set file '{path}' is not valid JSON: {exc}") from exc
    return validate_d7_gold_set_payload(raw)


def validate_d7_gold_set_payload(payload: Any) -> D7GoldSetPackage:
    """Validate a raw JSON payload as a versioned D7 gold-set package."""
    if not isinstance(payload, dict):
        raise ValueError("D7 gold-set package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D7 gold-set package must include schema_version=1")
    try:
        return D7GoldSetPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 gold-set package: {exc}") from exc


def d7_gold_payload_for_scorecard(payload: Any) -> Any:
    """Validate D7 gold input and return payload compatible with Phase 0 scoring."""
    if isinstance(payload, dict) and payload.get("schema_version") == 1:
        return validate_d7_gold_set_payload(payload).model_dump(mode="json")
    if isinstance(payload, dict) and isinstance(payload.get("contrary_evidence"), list):
        _validate_gold_anchors(payload["contrary_evidence"])
        return payload
    if isinstance(payload, list):
        _validate_gold_anchors(payload)
        return payload
    raise ValueError(
        "D7 gold file must be a JSON list of anchors, an object with a "
        "'contrary_evidence' list, or a schema_version=1 D7 gold-set package"
    )


def d7_gold_anchor_key(anchor: DisconfirmationGoldAnchor) -> str:
    """Build the exact D7 comparison key for a gold anchor."""
    if anchor.start_char is not None and anchor.end_char is not None:
        return f"{anchor.target_claim_id}|{anchor.doc_id}|{anchor.start_char}:{anchor.end_char}"
    if anchor.segment_id:
        return f"{anchor.target_claim_id}|{anchor.doc_id}|segment:{anchor.segment_id}"
    raise ValueError("D7 gold anchor validation failed to produce a comparison key")


def _validate_gold_anchors(raw: list[Any]) -> None:
    try:
        anchors = [DisconfirmationGoldAnchor.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D7 gold annotations: {exc}") from exc
    keys = [d7_gold_anchor_key(anchor) for anchor in anchors]
    duplicates = sorted(key for key in set(keys) if keys.count(key) > 1)
    if duplicates:
        raise ValueError("Duplicate D7 gold anchor key(s): " + ", ".join(duplicates))


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))
