"""D3 application-validity gold anchor contracts and validation helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")


class ApplicationGoldAnchor(BaseModel):
    """Human/adjudicated code-application anchor used for D3 scoring."""

    code_id: str = Field(description="Code ID assigned to the source span")
    doc_id: str = Field(description="Document containing the coded source span")
    start_char: int | None = Field(default=None, description="Start offset of the coded span")
    end_char: int | None = Field(default=None, description="End offset of the coded span")
    segment_id: str | None = Field(default=None, description="Segment ID when span offsets are unavailable")
    quote_text: str = Field(default="", description="Optional source text for human inspection")

    @model_validator(mode="after")
    def require_scoreable_key(self) -> "ApplicationGoldAnchor":
        """Require a deterministic comparison key for every D3 gold record."""
        if not self.code_id.strip():
            raise ValueError("D3 application gold code_id must be non-empty")
        if not self.doc_id.strip():
            raise ValueError("D3 application gold doc_id must be non-empty")
        has_start = self.start_char is not None
        has_end = self.end_char is not None
        if has_start != has_end:
            raise ValueError("D3 application gold anchors must provide both start_char and end_char")
        if has_start and has_end:
            if self.start_char is None or self.end_char is None:
                raise ValueError("D3 application gold span offsets are incomplete")
            if self.start_char < 0 or self.end_char <= self.start_char:
                raise ValueError("D3 application gold span offsets must satisfy 0 <= start_char < end_char")
            return self
        if not self.segment_id:
            raise ValueError("D3 application gold anchors require span offsets or a segment_id")
        return self


class D3AdjudicationMetadata(BaseModel):
    """Human-adjudication metadata for a D3 application gold-set package."""

    coder_count: int = Field(description="Number of independent human coders before adjudication")
    adjudicator: str = Field(description="Adjudicator identifier, name, or redacted label")
    protocol: str = Field(description="Short description of the adjudication protocol")
    human_human_agreement: dict[str, Any] | None = Field(
        default=None,
        description="Optional human-ceiling agreement metrics, such as kappa/alpha/AC1",
    )
    notes: str = Field(default="", description="Optional caveats for the adjudication process")

    @model_validator(mode="after")
    def require_protocol(self) -> "D3AdjudicationMetadata":
        """Require human-process metadata to be meaningful, not blank."""
        if self.coder_count < 1:
            raise ValueError("D3 adjudication coder_count must be at least 1")
        if not self.adjudicator.strip():
            raise ValueError("D3 adjudication adjudicator must be non-empty")
        if not self.protocol.strip():
            raise ValueError("D3 adjudication protocol must be non-empty")
        return self


class D3GoldSetPackage(BaseModel):
    """Versioned D3 application gold-set package."""

    schema_version: Literal[1] = Field(description="D3 gold-set package schema version")
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
    adjudication: D3AdjudicationMetadata = Field(description="Human adjudication process metadata")
    application_gold: list[ApplicationGoldAnchor] = Field(
        description="Adjudicated code-to-source application anchors"
    )

    @model_validator(mode="after")
    def require_gold_set_invariants(self) -> "D3GoldSetPackage":
        """Enforce held-out package provenance and exact-key uniqueness."""
        if not self.gold_set_id.strip():
            raise ValueError("D3 gold_set_id must be non-empty")
        if not self.dataset_name.strip():
            raise ValueError("D3 dataset_name must be non-empty")
        if not _is_sha256(self.corpus_sha256):
            raise ValueError("D3 corpus_sha256 must be a 64-character hex SHA-256")
        if self.project_state_sha256 is not None and not _is_sha256(self.project_state_sha256):
            raise ValueError("D3 project_state_sha256 must be a 64-character hex SHA-256")
        if not self.application_gold:
            raise ValueError("D3 gold set requires at least one application_gold anchor")

        keys = [application_gold_anchor_key(anchor) for anchor in self.application_gold]
        duplicates = sorted(key for key in set(keys) if keys.count(key) > 1)
        if duplicates:
            raise ValueError("Duplicate D3 application gold anchor key(s): " + ", ".join(duplicates))

        if self.split == "held_out":
            if not self.prompt_frozen:
                raise ValueError("held_out D3 gold sets require prompt_frozen=true")
            if not self.contamination_checked:
                raise ValueError("held_out D3 gold sets require contamination_checked=true")
            if self.adjudication.coder_count < 2:
                raise ValueError("held_out D3 gold sets require at least two coders")
        return self


def load_d3_gold_set(path: Path | str) -> D3GoldSetPackage:
    """Load and validate a versioned D3 gold-set package from disk."""
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"D3 gold-set file '{path}' could not be read: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"D3 gold-set file '{path}' is not valid JSON: {exc}") from exc
    return validate_d3_gold_set_payload(raw)


def validate_d3_gold_set_payload(payload: Any) -> D3GoldSetPackage:
    """Validate a raw JSON payload as a versioned D3 gold-set package."""
    if not isinstance(payload, dict):
        raise ValueError("D3 gold-set package must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("D3 gold-set package must include schema_version=1")
    try:
        return D3GoldSetPackage.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 gold-set package: {exc}") from exc


def application_gold_payload_for_scorecard(payload: Any) -> Any:
    """Validate D3 application-gold input and return scorecard-compatible payload."""
    if isinstance(payload, dict) and payload.get("schema_version") == 1:
        return validate_d3_gold_set_payload(payload).model_dump(mode="json")
    if isinstance(payload, dict) and isinstance(payload.get("application_gold"), list):
        _validate_application_gold_anchors(payload["application_gold"])
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("code_applications"), list):
        _validate_application_gold_anchors(payload["code_applications"])
        return {"application_gold": payload["code_applications"]}
    if isinstance(payload, list):
        _validate_application_gold_anchors(payload)
        return payload
    raise ValueError(
        "D3 application gold file must be a JSON list of anchors, an object with "
        "an 'application_gold' list, or an object with a 'code_applications' list"
    )


def application_gold_anchor_key(anchor: ApplicationGoldAnchor) -> str:
    """Build the exact D3 comparison key for a gold anchor."""
    if anchor.start_char is not None and anchor.end_char is not None:
        return f"{anchor.code_id}|{anchor.doc_id}|{anchor.start_char}:{anchor.end_char}"
    if anchor.segment_id:
        return f"{anchor.code_id}|{anchor.doc_id}|segment:{anchor.segment_id}"
    raise ValueError("D3 application gold anchor validation failed to produce a comparison key")


def _validate_application_gold_anchors(raw: list[Any]) -> None:
    try:
        anchors = [ApplicationGoldAnchor.model_validate(item) for item in raw]
    except ValidationError as exc:
        raise ValueError(f"Invalid D3 application gold annotations: {exc}") from exc
    keys = [application_gold_anchor_key(anchor) for anchor in anchors]
    duplicates = sorted(key for key in set(keys) if keys.count(key) > 1)
    if duplicates:
        raise ValueError("Duplicate D3 application gold anchor key(s): " + ", ".join(duplicates))


def _is_sha256(value: str) -> bool:
    return bool(_SHA256_RE.fullmatch(value))
