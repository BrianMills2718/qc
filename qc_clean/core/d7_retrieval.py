"""Export disconfirmation retrieval candidates as D7 baseline predictions."""

from __future__ import annotations

import re
from typing import Any, Iterable, Literal, Mapping

from pydantic import BaseModel, Field

from qc_clean.core.bench import phase0_scorecard
from qc_clean.core.claims import disconfirmation_targets
from qc_clean.core.d7_gold import DisconfirmationGoldAnchor, d7_gold_payload_for_scorecard
from qc_clean.core.disconfirmation import EmbeddingProvider, retrieve_disconfirmation_candidates
from qc_clean.schemas.domain import ProjectState


_PACKAGE_TYPE = "qualitative_coding.d7_retrieval_predictions"
_COMPARISON_REPORT_TYPE = "qualitative_coding.d7_retrieval_comparison"


class D7RetrievalBaselineRecord(BaseModel):
    """One D7 baseline prediction set derived from retrieval candidates."""

    name: str = Field(description="Stable baseline name for scorecard output")
    description: str = Field(description="Human-readable retrieval run description")
    contrary_evidence: list[DisconfirmationGoldAnchor] = Field(
        description="Retrieved candidate anchors formatted for D7 baseline scoring"
    )


class D7RetrievalRunMetadata(BaseModel):
    """Metadata for one retrieval-candidate export run."""

    schema_version: Literal[1] = Field(default=1, description="Retrieval export metadata schema")
    retrieval_mode: str = Field(description="Retrieval mode used for candidate generation")
    embedding_model: str | None = Field(
        default=None,
        description="Embedding model used when retrieval_mode is embedding_hybrid",
    )
    embedding_dimensions: int | None = Field(
        default=None,
        description="Embedding dimensions requested when configured",
    )
    max_targets: int = Field(description="Maximum claim-ledger targets considered")
    target_claim_count: int = Field(description="Number of claim targets selected for retrieval")
    candidates_per_claim: int = Field(description="Maximum candidates retrieved per target claim")
    candidate_count: int = Field(description="Number of candidate anchors exported")
    bm25_k1: float = Field(description="BM25 k1 value used during retrieval")
    bm25_b: float = Field(description="BM25 b value used during retrieval")
    contrary_cue_weight: float = Field(description="Contrary-cue score weight used during retrieval")
    expanded_term_weight: float = Field(description="Query-expansion score weight used during retrieval")
    semantic_weight: float = Field(description="Embedding cosine similarity weight used during retrieval")
    min_semantic_similarity: float = Field(
        description="Minimum cosine similarity for semantic-only candidates"
    )
    note: str = Field(description="Claim-discipline note for consumers")


class D7RetrievalBaselinePackage(BaseModel):
    """D7 baseline-compatible package produced by retrieval-mode export."""

    schema_version: Literal[1] = Field(default=1, description="Package schema version")
    package_type: Literal["qualitative_coding.d7_retrieval_predictions"] = Field(
        default=_PACKAGE_TYPE,
        description="Stable package type identifier",
    )
    retrieval_run: D7RetrievalRunMetadata = Field(description="Retrieval run metadata")
    disconfirmation_baselines: list[D7RetrievalBaselineRecord] = Field(
        description="Baseline records accepted by Phase 0 D7 scoring"
    )


class D7RetrievalComparisonReport(BaseModel):
    """Exact D7 comparison report for retrieval prediction packages."""

    schema_version: Literal[1] = Field(default=1, description="Comparison report schema version")
    report_type: Literal["qualitative_coding.d7_retrieval_comparison"] = Field(
        default=_COMPARISON_REPORT_TYPE,
        description="Stable report type identifier",
    )
    project_id: str = Field(description="Project ID scored")
    project_name: str = Field(description="Project name scored")
    package_count: int = Field(description="Number of retrieval prediction packages compared")
    baseline_count: int = Field(description="Number of baseline records scored")
    disconfirmation_d7: dict[str, Any] = Field(description="D7 scorecard section from Phase 0")
    note: str = Field(description="Claim-discipline note for consumers")


def export_d7_retrieval_baseline(
    state: ProjectState,
    *,
    name: str | None = None,
    description: str = "",
    max_targets: int = 50,
    candidates_per_claim: int = 5,
    retrieval_mode: str = "lexical_bm25",
    bm25_k1: float = 1.2,
    bm25_b: float = 0.75,
    contrary_cue_weight: float = 1.25,
    query_expansions: Mapping[str, Iterable[str]] | None = None,
    expanded_term_weight: float = 0.5,
    embedding_model: str | None = None,
    embedding_dimensions: int | None = None,
    semantic_weight: float = 1.0,
    min_semantic_similarity: float = 0.0,
    embedding_provider: EmbeddingProvider | None = None,
    task: str = "qualitative_coding.d7_retrieval_export",
    trace_id: str = "qualitative_coding/d7-retrieval/manual",
    max_budget: float = 0.0,
) -> dict[str, Any]:
    """Return retrieval candidates as a D7 baseline-compatible JSON package."""
    working_state = state.model_copy(deep=True)
    target_claims = disconfirmation_targets(working_state, limit=max_targets)
    candidates = retrieve_disconfirmation_candidates(
        working_state,
        target_claims,
        candidates_per_claim=candidates_per_claim,
        bm25_k1=bm25_k1,
        bm25_b=bm25_b,
        contrary_cue_weight=contrary_cue_weight,
        query_expansions=query_expansions,
        expanded_term_weight=expanded_term_weight,
        retrieval_mode=retrieval_mode,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        semantic_weight=semantic_weight,
        min_semantic_similarity=min_semantic_similarity,
        embedding_provider=embedding_provider,
        task=task,
        trace_id=trace_id,
        max_budget=max_budget,
    )

    baseline_name = name or default_d7_retrieval_baseline_name(
        retrieval_mode,
        candidates_per_claim=candidates_per_claim,
        embedding_model=embedding_model,
    )
    baseline_description = description or (
        f"Retrieval-mode candidate export: mode={retrieval_mode}, "
        f"candidates_per_claim={candidates_per_claim}."
    )
    baseline = D7RetrievalBaselineRecord(
        name=baseline_name,
        description=baseline_description,
        contrary_evidence=[
            DisconfirmationGoldAnchor(
                target_claim_id=candidate.target_claim_id,
                doc_id=candidate.doc_id,
                start_char=candidate.start_char,
                end_char=candidate.end_char,
                segment_id=candidate.segment_id,
                quote_text=candidate.quote_text,
            )
            for candidate in candidates
        ],
    )
    metadata = D7RetrievalRunMetadata(
        retrieval_mode=retrieval_mode,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        max_targets=max_targets,
        target_claim_count=len(target_claims),
        candidates_per_claim=candidates_per_claim,
        candidate_count=len(candidates),
        bm25_k1=bm25_k1,
        bm25_b=bm25_b,
        contrary_cue_weight=contrary_cue_weight,
        expanded_term_weight=expanded_term_weight,
        semantic_weight=semantic_weight,
        min_semantic_similarity=min_semantic_similarity,
        note=(
            "Retrieval predictions are candidate passages for D7 scoring; they are "
            "not human-adjudicated negative-case findings or methodological validity evidence."
        ),
    )
    package = D7RetrievalBaselinePackage(
        retrieval_run=metadata,
        disconfirmation_baselines=[baseline],
    )
    return package.model_dump(mode="json")


def compare_d7_retrieval_predictions(
    state: ProjectState,
    *,
    gold_payload: Any,
    prediction_packages: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Score retrieval prediction packages against one D7 gold payload."""
    packages = list(prediction_packages)
    if not packages:
        raise ValueError("At least one D7 retrieval prediction package is required")

    baselines: list[Any] = []
    for index, package in enumerate(packages, start=1):
        raw_baselines = package.get("disconfirmation_baselines")
        if not isinstance(raw_baselines, list):
            raise ValueError(
                f"D7 retrieval prediction package #{index} must include a "
                "'disconfirmation_baselines' list"
            )
        baselines.extend(raw_baselines)
    if not baselines:
        raise ValueError("D7 retrieval comparison requires at least one baseline record")

    working_state = state.model_copy(deep=True)
    working_state.config.extra = dict(working_state.config.extra)
    working_state.config.extra["disconfirmation_gold"] = d7_gold_payload_for_scorecard(gold_payload)
    working_state.config.extra["disconfirmation_baselines"] = baselines
    d7_scorecard = phase0_scorecard(working_state)["disconfirmation_d7"]

    report = D7RetrievalComparisonReport(
        project_id=state.id,
        project_name=state.name,
        package_count=len(packages),
        baseline_count=len(baselines),
        disconfirmation_d7=d7_scorecard,
        note=(
            "D7 retrieval comparison reports exact-span point estimates from exported "
            "candidate predictions. This is not a held-out result or superiority claim "
            "without frozen data, live baselines, and interval-tested deltas."
        ),
    )
    return report.model_dump(mode="json")


def default_d7_retrieval_baseline_name(
    retrieval_mode: str,
    *,
    candidates_per_claim: int,
    embedding_model: str | None = None,
) -> str:
    """Return a stable baseline name for one retrieval export configuration."""
    parts = ["retrieval", retrieval_mode, f"top{candidates_per_claim}"]
    if embedding_model:
        parts.append(_slug(embedding_model))
    return "_".join(parts)


def _slug(value: str) -> str:
    """Normalize a model/config value for use in a baseline name."""
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return slug or "model"
