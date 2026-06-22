"""Import completed adjudication responses into D3/D7 gold packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from qc_clean.core.adjudication_sample import (
    AdjudicationResponse,
    AdjudicationSampleItem,
    AdjudicationSamplePackage,
    validate_adjudication_response_payload,
)
from qc_clean.core.d3_gold import (
    ApplicationGoldAnchor,
    D3AdjudicationMetadata,
    D3GoldSetPackage,
)
from qc_clean.core.d7_gold import (
    D7AdjudicationMetadata,
    D7GoldSetPackage,
    DisconfirmationGoldAnchor,
)


GoldSplit = Literal["held_out", "dev", "public_comparator"]

IMPORT_CAUTION = (
    "Adjudication response import creates label package artifacts only; it is "
    "not methodological validity evidence unless labels were collected under a "
    "documented expert protocol and scored separately."
)


class AdjudicationGoldImportReport(BaseModel):
    """Report for converting adjudication responses into gold package files."""

    schema_version: Literal[1] = Field(description="Import report schema version")
    package_type: Literal["adjudication_gold_import"] = Field(
        description="Import report package kind"
    )
    status: Literal["complete"] = Field(description="Overall import status")
    project_id: str = Field(description="Project ID from the response package")
    project_name: str = Field(description="Project name from the response package")
    total_response_count: int = Field(description="Completed response count in the package")
    valid_response_count: int = Field(description="Responses labeled valid")
    excluded_response_count: int = Field(
        description="Responses labeled invalid or unclear and excluded from gold anchors"
    )
    valid_d3_anchor_count: int = Field(description="D3 application anchors created")
    valid_d7_anchor_count: int = Field(description="D7 contrary-evidence anchors created")
    caution: str = Field(description="Claim-discipline caveat for generated gold packages")


class AdjudicationGoldImportResult(BaseModel):
    """In-memory result of adjudication response import."""

    report: AdjudicationGoldImportReport = Field(description="Import summary report")
    d3_gold_package: D3GoldSetPackage | None = Field(
        default=None,
        description="Generated D3 package when requested",
    )
    d7_gold_package: D7GoldSetPackage | None = Field(
        default=None,
        description="Generated D7 package when requested",
    )


def build_adjudication_gold_import(
    payload: Any,
    *,
    gold_set_id: str,
    dataset_name: str,
    coder_count: int,
    adjudicator: str,
    protocol: str,
    include_d3: bool,
    include_d7: bool,
    split: GoldSplit = "dev",
    prompt_frozen: bool = False,
    contamination_checked: bool = False,
    human_human_agreement: dict[str, Any] | None = None,
    notes: str = "",
) -> AdjudicationGoldImportResult:
    """Build D3/D7 gold packages from a completed adjudication response payload."""
    if not include_d3 and not include_d7:
        raise ValueError("At least one of include_d3 or include_d7 is required")

    validation = validate_adjudication_response_payload(payload)
    if validation.status != "complete":
        messages = "; ".join(error.message for error in validation.errors)
        raise ValueError(f"Adjudication response package is invalid: {messages}")

    package = AdjudicationSamplePackage.model_validate(payload)
    d3_anchors: list[ApplicationGoldAnchor] = []
    d7_anchors: list[DisconfirmationGoldAnchor] = []
    valid_response_count = 0
    excluded_response_count = 0

    raw_items = payload.get("items", []) if isinstance(payload, dict) else []
    raw_items_by_id = {
        raw_item.get("item_id"): raw_item
        for raw_item in raw_items
        if isinstance(raw_item, dict) and isinstance(raw_item.get("item_id"), str)
    }

    for item in package.items:
        raw_response = _raw_response_for_item(raw_items_by_id.get(item.item_id, {}))
        response = AdjudicationResponse.model_validate(raw_response)
        validity = response.validity.strip().lower()
        if validity != "valid":
            excluded_response_count += 1
            continue

        valid_response_count += 1
        if include_d3 and item.target_type == "code_application":
            d3_anchors.append(_d3_anchor_for_item(item))
        if include_d7 and item.target_type == "negative_case":
            d7_anchors.append(_d7_anchor_for_item(item))

    if include_d3 and not d3_anchors:
        raise ValueError("No valid D3 code-application responses were available to import")
    if include_d7 and not d7_anchors:
        raise ValueError("No valid D7 negative-case responses were available to import")

    d3_package = None
    d7_package = None
    if include_d3:
        d3_package = D3GoldSetPackage(
            schema_version=1,
            gold_set_id=gold_set_id,
            dataset_name=dataset_name,
            split=split,
            corpus_sha256=package.corpus_sha256,
            project_state_sha256=package.project_state_sha256,
            prompt_frozen=prompt_frozen,
            contamination_checked=contamination_checked,
            adjudication=D3AdjudicationMetadata(
                coder_count=coder_count,
                adjudicator=adjudicator,
                protocol=protocol,
                human_human_agreement=human_human_agreement,
                notes=notes,
            ),
            application_gold=d3_anchors,
        )
    if include_d7:
        d7_package = D7GoldSetPackage(
            schema_version=1,
            gold_set_id=gold_set_id,
            dataset_name=dataset_name,
            split=split,
            corpus_sha256=package.corpus_sha256,
            project_state_sha256=package.project_state_sha256,
            prompt_frozen=prompt_frozen,
            contamination_checked=contamination_checked,
            adjudication=D7AdjudicationMetadata(
                coder_count=coder_count,
                adjudicator=adjudicator,
                protocol=protocol,
                human_human_agreement=human_human_agreement,
                notes=notes,
            ),
            contrary_evidence=d7_anchors,
        )

    return AdjudicationGoldImportResult(
        report=AdjudicationGoldImportReport(
            schema_version=1,
            package_type="adjudication_gold_import",
            status="complete",
            project_id=package.project_id,
            project_name=package.project_name,
            total_response_count=validation.valid_response_count,
            valid_response_count=valid_response_count,
            excluded_response_count=excluded_response_count,
            valid_d3_anchor_count=len(d3_anchors),
            valid_d7_anchor_count=len(d7_anchors),
            caution=IMPORT_CAUTION,
        ),
        d3_gold_package=d3_package,
        d7_gold_package=d7_package,
    )


def write_adjudication_gold_import(
    result: AdjudicationGoldImportResult,
    *,
    d3_output: str | Path | None = None,
    d7_output: str | Path | None = None,
) -> dict[str, str]:
    """Write requested D3/D7 gold packages and return output paths."""
    outputs: dict[str, str] = {}
    if d3_output is not None:
        if result.d3_gold_package is None:
            raise ValueError("D3 output requested but no D3 gold package was generated")
        outputs["d3_output"] = _write_json(result.d3_gold_package.model_dump(mode="json"), d3_output)
    if d7_output is not None:
        if result.d7_gold_package is None:
            raise ValueError("D7 output requested but no D7 gold package was generated")
        outputs["d7_output"] = _write_json(result.d7_gold_package.model_dump(mode="json"), d7_output)
    return outputs


def _d3_anchor_for_item(item: AdjudicationSampleItem) -> ApplicationGoldAnchor:
    """Build one D3 gold anchor from a valid code-application item."""
    if item.source_context is None:
        raise ValueError(f"Code-application item {item.item_id} has no source context")
    code_id = str(item.payload.get("code_id") or "")
    return ApplicationGoldAnchor(
        code_id=code_id,
        doc_id=item.source_context.doc_id,
        start_char=item.source_context.start_char,
        end_char=item.source_context.end_char,
        segment_id=item.source_context.segment_id,
        quote_text=item.source_context.quote_text,
    )


def _d7_anchor_for_item(item: AdjudicationSampleItem) -> DisconfirmationGoldAnchor:
    """Build one D7 gold anchor from a valid negative-case item."""
    if item.source_context is None:
        raise ValueError(f"Negative-case item {item.item_id} has no source context")
    scope = item.payload.get("scope")
    claim_ids = scope.get("claim_ids") if isinstance(scope, dict) else None
    if not isinstance(claim_ids, list) or not claim_ids:
        raise ValueError(f"Negative-case item {item.item_id} has no target claim ID")
    return DisconfirmationGoldAnchor(
        target_claim_id=str(claim_ids[0]),
        doc_id=item.source_context.doc_id,
        start_char=item.source_context.start_char,
        end_char=item.source_context.end_char,
        segment_id=item.source_context.segment_id,
        quote_text=item.source_context.quote_text,
    )


def _raw_response_for_item(raw_item: dict[str, Any]) -> dict[str, Any]:
    """Return the raw response object accepted by the response validator."""
    response = raw_item.get("response")
    if isinstance(response, dict):
        return response
    template = raw_item.get("response_template")
    if isinstance(template, dict):
        return template
    raise ValueError(f"Item {raw_item.get('item_id', '<unknown>')} has no response")


def _write_json(payload: dict[str, Any], output_file: str | Path) -> str:
    """Write a JSON payload to disk and return the output path."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)
