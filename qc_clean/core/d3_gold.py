"""D3 application-validity gold anchor contracts and validation helpers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError, model_validator


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


def application_gold_payload_for_scorecard(payload: Any) -> Any:
    """Validate D3 application-gold input and return scorecard-compatible payload."""
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
