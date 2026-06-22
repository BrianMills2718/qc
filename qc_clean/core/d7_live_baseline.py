"""Opt-in live D7 candidate-selection baseline exporter."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Awaitable, Iterable, Mapping
from importlib import resources
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, model_validator

from qc_clean.core.claims import disconfirmation_targets
from qc_clean.core.d7_gold import DisconfirmationGoldAnchor
from qc_clean.core.d7_retrieval import D7RetrievalBaselineRecord
from qc_clean.core.disconfirmation import (
    DisconfirmationCandidate,
    EmbeddingProvider,
    format_disconfirmation_candidates,
    retrieve_disconfirmation_candidates,
)
from qc_clean.core.prompting import format_untrusted_data_block
from qc_clean.schemas.domain import AnalyticClaim, ProjectState


_PACKAGE_TYPE = "qualitative_coding.d7_live_baseline_predictions"
_BASELINE_MODE = "live_candidate_selector"
_PROMPT_TEMPLATE = "d7_live_candidate_selection.txt"


class D7LiveCandidateSelection(BaseModel):
    """Structured live-model decision for one D7 target claim."""

    selected_candidate_ids: list[str] = Field(
        default_factory=list,
        description=(
            "Candidate IDs from the supplied list judged to directly contradict, "
            "qualify, or substantially complicate the target claim"
        ),
    )
    rationale: str = Field(description="Concise explanation of the candidate-selection decision")

    @model_validator(mode="after")
    def require_known_id_shape(self) -> "D7LiveCandidateSelection":
        """Normalize candidate IDs and reject blank or duplicated selections."""
        normalized: list[str] = []
        for raw_id in self.selected_candidate_ids:
            candidate_id = raw_id.strip()
            if not candidate_id:
                raise ValueError("D7 live baseline selected_candidate_ids cannot contain blank IDs")
            normalized.append(candidate_id)
        duplicates = sorted(candidate_id for candidate_id in set(normalized) if normalized.count(candidate_id) > 1)
        if duplicates:
            raise ValueError("Duplicate D7 live baseline candidate_id(s): " + ", ".join(duplicates))
        if not self.rationale.strip():
            raise ValueError("D7 live baseline rationale must be non-empty")
        self.selected_candidate_ids = normalized
        self.rationale = self.rationale.strip()
        return self


class D7LiveSelectionRecord(BaseModel):
    """Auditable model decision for one target claim."""

    target_claim_id: str = Field(description="Claim ID evaluated by the live baseline")
    candidate_count: int = Field(description="Number of retrieved candidates shown to the model")
    selected_candidate_ids: list[str] = Field(description="Candidate IDs selected by the model")
    rationale: str = Field(description="Model-provided rationale for the selection")
    prompt_sha256: str | None = Field(
        default=None,
        description="SHA-256 hash of the exact prompt sent for this target claim",
    )


class D7LiveBaselineRunMetadata(BaseModel):
    """Metadata for one opt-in live D7 baseline export run."""

    schema_version: Literal[1] = Field(default=1, description="Live baseline metadata schema")
    project_id: str = Field(description="Project ID used for live baseline export")
    project_state_sha256: str = Field(description="SHA-256 hash of the exported ProjectState JSON")
    corpus_sha256: str = Field(description="SHA-256 hash of the exported corpus JSON")
    baseline_mode: Literal["live_candidate_selector"] = Field(
        default=_BASELINE_MODE,
        description="Live baseline mode used for prediction generation",
    )
    model: str = Field(description="Live model asked to select contrary-evidence candidates")
    retrieval_mode: str = Field(description="Retrieval mode used to build the candidate set")
    embedding_model: str | None = Field(
        default=None,
        description="Embedding model used when retrieval_mode is embedding_hybrid",
    )
    embedding_dimensions: int | None = Field(
        default=None,
        description="Embedding dimensions requested when configured",
    )
    max_targets: int = Field(description="Maximum claim-ledger targets considered")
    target_claim_count: int = Field(description="Number of target claims considered")
    candidates_per_claim: int = Field(description="Maximum retrieved candidates shown per target claim")
    candidate_count: int = Field(description="Total retrieved candidate passages")
    selected_candidate_count: int = Field(description="Total candidates selected by the live model")
    bm25_k1: float = Field(description="BM25 k1 value used during candidate retrieval")
    bm25_b: float = Field(description="BM25 b value used during candidate retrieval")
    contrary_cue_weight: float = Field(description="Contrary-cue score weight used during retrieval")
    expanded_term_weight: float = Field(description="Query-expansion score weight used during retrieval")
    semantic_weight: float = Field(description="Embedding cosine similarity weight used during retrieval")
    min_semantic_similarity: float = Field(
        description="Minimum cosine similarity for semantic-only candidates"
    )
    trace_id: str = Field(description="Base observability trace ID used for live baseline export")
    max_budget: float = Field(description="Maximum budget supplied to live baseline export")
    prompt_hashes: dict[str, str] = Field(
        description="Per-target-claim SHA-256 hashes for live baseline prompts"
    )
    note: str = Field(description="Claim-discipline note for consumers")


class D7LiveBaselinePackage(BaseModel):
    """Scorecard-compatible package produced by live D7 candidate selection."""

    schema_version: Literal[1] = Field(default=1, description="Package schema version")
    package_type: Literal["qualitative_coding.d7_live_baseline_predictions"] = Field(
        default=_PACKAGE_TYPE,
        description="Stable package type identifier",
    )
    live_baseline_run: D7LiveBaselineRunMetadata = Field(description="Live baseline run metadata")
    selection_records: list[D7LiveSelectionRecord] = Field(
        description="Per-target live model candidate-selection records"
    )
    disconfirmation_baselines: list[D7RetrievalBaselineRecord] = Field(
        description="Baseline records accepted by Phase 0 D7 scoring"
    )


class D7LiveCandidateSelector(Protocol):
    """Callable interface for one live D7 candidate-selection decision."""

    def __call__(
        self,
        *,
        target_claim: AnalyticClaim,
        candidates: list[DisconfirmationCandidate],
        prompt: str,
        model_name: str,
        trace_id: str,
        max_budget: float,
    ) -> Awaitable[D7LiveCandidateSelection]:
        """Return selected candidate IDs for one target claim."""
        ...


async def export_d7_live_candidate_baseline_async(
    state: ProjectState,
    *,
    model_name: str,
    name: str | None = None,
    description: str = "",
    max_targets: int = 20,
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
    trace_id: str = "qualitative_coding/d7-live-baseline/manual",
    max_budget: float = 1.0,
    candidate_selector: D7LiveCandidateSelector | None = None,
) -> dict[str, Any]:
    """Return live candidate-selection predictions as a D7 baseline package."""
    if not model_name.strip():
        raise ValueError("D7 live baseline model_name must be non-empty")
    if max_targets < 1:
        raise ValueError("D7 live baseline max_targets must be at least 1")
    if candidates_per_claim < 1:
        raise ValueError("D7 live baseline candidates_per_claim must be at least 1")
    if max_budget < 0:
        raise ValueError("D7 live baseline max_budget must be non-negative")

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
        task="qualitative_coding.d7_live_baseline.retrieval",
        trace_id=trace_id,
        max_budget=max_budget,
    )

    selector = candidate_selector or _call_live_candidate_selector
    candidates_by_claim = _group_candidates_by_claim(candidates)
    selected_candidates: list[DisconfirmationCandidate] = []
    selection_records: list[D7LiveSelectionRecord] = []
    prompt_hashes: dict[str, str] = {}

    for target_claim in target_claims:
        target_candidates = candidates_by_claim.get(target_claim.id, [])
        if not target_candidates:
            selection_records.append(D7LiveSelectionRecord(
                target_claim_id=target_claim.id,
                candidate_count=0,
                selected_candidate_ids=[],
                rationale="No retrieved candidates were available for this target claim.",
                prompt_sha256=None,
            ))
            continue

        prompt = build_d7_live_candidate_selection_prompt(target_claim, target_candidates)
        prompt_hash = _sha256_text(prompt)
        prompt_hashes[target_claim.id] = prompt_hash
        selection = await selector(
            target_claim=target_claim,
            candidates=target_candidates,
            prompt=prompt,
            model_name=model_name.strip(),
            trace_id=f"{trace_id}/{target_claim.id}",
            max_budget=max_budget,
        )
        selected_ids = _validate_selected_candidate_ids(
            selection.selected_candidate_ids,
            target_claim=target_claim,
            candidates=target_candidates,
        )
        selected_candidates.extend(_candidate_by_id(target_candidates)[candidate_id] for candidate_id in selected_ids)
        selection_records.append(D7LiveSelectionRecord(
            target_claim_id=target_claim.id,
            candidate_count=len(target_candidates),
            selected_candidate_ids=selected_ids,
            rationale=selection.rationale,
            prompt_sha256=prompt_hash,
        ))

    baseline = D7RetrievalBaselineRecord(
        name=name or default_d7_live_baseline_name(
            model_name,
            retrieval_mode=retrieval_mode,
            candidates_per_claim=candidates_per_claim,
        ),
        description=description or (
            f"Live D7 candidate-selection baseline: model={model_name}, "
            f"retrieval_mode={retrieval_mode}, candidates_per_claim={candidates_per_claim}."
        ),
        contrary_evidence=[
            DisconfirmationGoldAnchor(
                target_claim_id=candidate.target_claim_id,
                doc_id=candidate.doc_id,
                start_char=candidate.start_char,
                end_char=candidate.end_char,
                segment_id=candidate.segment_id,
                quote_text=candidate.quote_text,
            )
            for candidate in selected_candidates
        ],
    )
    package = D7LiveBaselinePackage(
        live_baseline_run=D7LiveBaselineRunMetadata(
            project_id=state.id,
            project_state_sha256=_sha256_jsonable(state.model_dump(mode="json")),
            corpus_sha256=_sha256_jsonable(state.corpus.model_dump(mode="json")),
            model=model_name.strip(),
            retrieval_mode=retrieval_mode,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            max_targets=max_targets,
            target_claim_count=len(target_claims),
            candidates_per_claim=candidates_per_claim,
            candidate_count=len(candidates),
            selected_candidate_count=len(selected_candidates),
            bm25_k1=bm25_k1,
            bm25_b=bm25_b,
            contrary_cue_weight=contrary_cue_weight,
            expanded_term_weight=expanded_term_weight,
            semantic_weight=semantic_weight,
            min_semantic_similarity=min_semantic_similarity,
            trace_id=trace_id,
            max_budget=max_budget,
            prompt_hashes=prompt_hashes,
            note=(
                "Live D7 candidate-selection baselines are model predictions over bounded "
                "retrieved candidates. They are not human-adjudicated D7 evidence, not a "
                "held-out benchmark result, and not a superiority claim."
            ),
        ),
        selection_records=selection_records,
        disconfirmation_baselines=[baseline],
    )
    return package.model_dump(mode="json")


def build_d7_live_candidate_selection_prompt(
    target_claim: AnalyticClaim,
    candidates: list[DisconfirmationCandidate],
) -> str:
    """Render the prompt for one live D7 candidate-selection decision."""
    claim_block = format_untrusted_data_block(
        "Target claim",
        f"claim_id={target_claim.id}\nclaim_text={target_claim.claim_text}",
    )
    candidate_block = format_disconfirmation_candidates(candidates)
    template = resources.files("qc_clean.prompts").joinpath(_PROMPT_TEMPLATE).read_text(
        encoding="utf-8"
    )
    return template.format(
        claim_block=claim_block,
        candidate_block=candidate_block,
    )


async def _call_live_candidate_selector(
    *,
    target_claim: AnalyticClaim,
    candidates: list[DisconfirmationCandidate],
    prompt: str,
    model_name: str,
    trace_id: str,
    max_budget: float,
) -> D7LiveCandidateSelection:
    """Call the configured model for one target-claim candidate-selection decision."""
    from qc_clean.core.llm.llm_handler import LLMHandler

    llm = LLMHandler(model_name=model_name)
    response = await llm.extract_structured(
        prompt,
        D7LiveCandidateSelection,
        task="qualitative_coding.d7_live_candidate_baseline",
        trace_id=trace_id,
        max_budget=max_budget,
    )
    return D7LiveCandidateSelection.model_validate(response.model_dump(mode="json"))


def default_d7_live_baseline_name(
    model_name: str,
    *,
    retrieval_mode: str,
    candidates_per_claim: int,
) -> str:
    """Return a stable baseline name for one live D7 candidate selector."""
    return "_".join([
        _BASELINE_MODE,
        _slug(model_name),
        _slug(retrieval_mode),
        f"top{candidates_per_claim}",
    ])


def _validate_selected_candidate_ids(
    selected_ids: list[str],
    *,
    target_claim: AnalyticClaim,
    candidates: list[DisconfirmationCandidate],
) -> list[str]:
    """Fail loudly if the model selected IDs outside the supplied candidate list."""
    known = _candidate_by_id(candidates)
    unknown = sorted(set(selected_ids) - set(known))
    if unknown:
        raise ValueError(
            "D7 live baseline model selected unknown candidate_id(s) "
            f"for claim {target_claim.id}: {', '.join(unknown)}"
        )
    return selected_ids


def _group_candidates_by_claim(
    candidates: list[DisconfirmationCandidate],
) -> dict[str, list[DisconfirmationCandidate]]:
    grouped: dict[str, list[DisconfirmationCandidate]] = defaultdict(list)
    for candidate in candidates:
        grouped[candidate.target_claim_id].append(candidate)
    return dict(grouped)


def _candidate_by_id(
    candidates: list[DisconfirmationCandidate],
) -> dict[str, DisconfirmationCandidate]:
    return {candidate.id: candidate for candidate in candidates}


def _slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_").lower()
    return slug or "model"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_jsonable(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
