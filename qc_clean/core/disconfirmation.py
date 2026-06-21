"""
Retrieval-first disconfirmation helpers.

This module surfaces source passages before negative-case interpretation. The
retriever is deliberately deterministic and local: it scores char-anchored
segments against claim/code terms and contradiction cues, then formats bounded
candidates for the LLM to assess.
"""

from __future__ import annotations

import re
from collections import Counter
from math import log, sqrt
from typing import Iterable, Mapping, Protocol

from pydantic import BaseModel, Field

from qc_clean.core.grounding import quote_hash
from qc_clean.core.prompting import format_untrusted_data_block
from qc_clean.core.segmentation import segment_corpus
from qc_clean.schemas.domain import AnalyticClaim, ClaimAnchor, ProjectState, Segment

_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'-]*")

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "in", "into", "is", "it", "its", "of", "on", "or",
    "that", "the", "their", "this", "to", "was", "were", "with",
}

_CONTRARY_CUES = {
    "abandon", "abandoned", "avoid", "barrier", "but", "challenge",
    "concern", "concerns", "contradict", "contradicted", "difficult",
    "error", "errors", "except", "fail", "failed", "fails", "however",
    "issue", "issues", "never", "not", "problem", "problems", "risk",
    "risks", "slow", "stopped", "unable", "unreliable", "worse",
}

_DEFAULT_QUERY_EXPANSIONS: dict[str, list[str]] = {
    "adopt": ["abandon", "avoid", "refuse", "stopped"],
    "adopted": ["abandoned", "avoided", "refused", "stopped"],
    "adoption": ["abandon", "avoid", "refuse", "stopped"],
    "automation": ["manual", "paperwork", "handoff", "handoffs"],
    "benefit": ["problem", "problems", "risk", "risks"],
    "benefits": ["problem", "problems", "risk", "risks"],
    "efficient": ["delay", "delays", "slow", "slower"],
    "efficiency": ["delay", "delays", "slow", "slower"],
    "faster": ["delay", "delays", "slow", "slower"],
    "improve": ["delay", "delays", "fail", "failed", "problem", "slow", "slower", "worse"],
    "improved": ["delay", "delays", "fail", "failed", "problem", "slow", "slower", "worse"],
    "improvement": ["delay", "delays", "fail", "failed", "problem", "slow", "slower", "worse"],
    "improves": ["delay", "delays", "fail", "failed", "problem", "slow", "slower", "worse"],
    "reliable": ["error", "errors", "failed", "unreliable"],
    "reliability": ["error", "errors", "failed", "unreliable"],
    "service": ["delays", "handoffs", "slow", "slower"],
    "trust": ["concern", "concerns", "distrust", "risk", "risks", "skeptical"],
    "trusted": ["concern", "concerns", "distrust", "risk", "risks", "skeptical"],
    "use": ["abandon", "avoid", "never", "stopped"],
    "used": ["abandoned", "avoided", "never", "stopped"],
}

_LEXICAL_RETRIEVAL_MODE = "lexical_bm25"
_EMBEDDING_HYBRID_RETRIEVAL_MODE = "embedding_hybrid"
_RETRIEVAL_MODES = {
    _LEXICAL_RETRIEVAL_MODE,
    _EMBEDDING_HYBRID_RETRIEVAL_MODE,
}


class EmbeddingProvider(Protocol):
    """Callable that returns one embedding vector for each input text."""

    def __call__(
        self,
        texts: list[str],
        *,
        model: str,
        task: str,
        trace_id: str,
        max_budget: float,
        dimensions: int | None = None,
    ) -> list[list[float]]:
        """Embed texts for disconfirmation retrieval."""
        ...


class DisconfirmationCandidate(BaseModel):
    """A retrieved source passage for disconfirmation interpretation."""

    id: str = Field(description="Prompt-local deterministic candidate identifier")
    target_claim_id: str = Field(description="Analytic claim this candidate may challenge")
    claim_text: str = Field(description="Human-readable target claim text")
    doc_id: str = Field(description="Document containing the candidate passage")
    segment_id: str | None = Field(default=None, description="Segment ID for the candidate passage")
    start_char: int = Field(description="Start offset in the source document")
    end_char: int = Field(description="End offset in the source document")
    quote_text: str = Field(description="Candidate passage text")
    quote_hash: str | None = Field(default=None, description="Hash of the exact source span")
    matched_terms: list[str] = Field(description="Claim/code terms found in the passage")
    expanded_terms: list[str] = Field(
        default_factory=list,
        description="Configured query-expansion terms found in the passage",
    )
    contrary_cues: list[str] = Field(description="Contradiction/exception cue terms found in the passage")
    retrieval_mode: str = Field(
        default=_LEXICAL_RETRIEVAL_MODE,
        description="Retrieval mode that produced this candidate",
    )
    semantic_score: float | None = Field(
        default=None,
        description="Cosine similarity score when embedding-hybrid retrieval is used",
    )
    score: float = Field(description="Deterministic retrieval score used for ranking")


def retrieve_disconfirmation_candidates(
    state: ProjectState,
    targets: Iterable[AnalyticClaim],
    *,
    candidates_per_claim: int = 5,
    bm25_k1: float = 1.2,
    bm25_b: float = 0.75,
    contrary_cue_weight: float = 1.25,
    query_expansions: Mapping[str, Iterable[str]] | None = None,
    expanded_term_weight: float = 0.5,
    retrieval_mode: str = _LEXICAL_RETRIEVAL_MODE,
    embedding_model: str | None = None,
    embedding_dimensions: int | None = None,
    semantic_weight: float = 1.0,
    min_semantic_similarity: float = 0.0,
    embedding_provider: EmbeddingProvider | None = None,
    task: str = "qualitative_coding.disconfirmation_retrieval",
    trace_id: str = "qualitative_coding/manual",
    max_budget: float = 0.0,
) -> list[DisconfirmationCandidate]:
    """Return bounded retrieved source candidates for each target claim."""
    if retrieval_mode not in _RETRIEVAL_MODES:
        allowed = ", ".join(sorted(_RETRIEVAL_MODES))
        raise ValueError(f"retrieval_mode must be one of {allowed}; got {retrieval_mode!r}")
    if bm25_k1 <= 0:
        raise ValueError("bm25_k1 must be greater than 0")
    if not 0 <= bm25_b <= 1:
        raise ValueError("bm25_b must be between 0 and 1")
    if contrary_cue_weight < 0:
        raise ValueError("contrary_cue_weight must be non-negative")
    if expanded_term_weight < 0:
        raise ValueError("expanded_term_weight must be non-negative")
    if semantic_weight < 0:
        raise ValueError("semantic_weight must be non-negative")
    if not -1 <= min_semantic_similarity <= 1:
        raise ValueError("min_semantic_similarity must be between -1 and 1")
    if embedding_dimensions is not None and embedding_dimensions <= 0:
        raise ValueError("embedding_dimensions must be greater than 0 when set")
    if retrieval_mode == _EMBEDDING_HYBRID_RETRIEVAL_MODE and not embedding_model:
        raise ValueError("embedding_model is required when retrieval_mode='embedding_hybrid'")

    if not state.segments:
        state.segments = segment_corpus(state.corpus.documents)

    docs_by_id = {doc.id: doc for doc in state.corpus.documents}
    candidates: list[DisconfirmationCandidate] = []
    per_claim = max(0, candidates_per_claim)
    if per_claim == 0:
        return candidates

    target_claims = list(targets)
    segments = list(state.segments)
    term_counts_by_segment, document_frequency, segment_lengths, average_segment_len = _bm25_index(
        segments
    )
    segment_count = len(segments)
    semantic_claim_vectors: dict[int, list[float]] = {}
    semantic_segment_vectors: dict[str, list[float]] = {}
    if retrieval_mode == _EMBEDDING_HYBRID_RETRIEVAL_MODE:
        semantic_claim_vectors, semantic_segment_vectors = _embedding_vectors_for_retrieval(
            state,
            target_claims,
            segments,
            embedding_model=embedding_model,
            embedding_dimensions=embedding_dimensions,
            embedding_provider=embedding_provider,
            task=task,
            trace_id=trace_id,
            max_budget=max_budget,
        )

    for target_index, claim in enumerate(target_claims):
        claim_terms = _claim_terms(state, claim)
        if not claim_terms:
            continue
        expanded_terms = (
            _query_expansion_terms(claim_terms, query_expansions)
            if expanded_term_weight > 0
            else set()
        )
        scored: list[tuple[
            float,
            int,
            int,
            float | None,
            Segment,
            list[str],
            list[str],
            list[str],
        ]] = []
        claim_vector = semantic_claim_vectors.get(target_index)
        for segment in segments:
            term_counts = term_counts_by_segment.get(segment.id, Counter())
            segment_terms = set(term_counts)
            matched = sorted(claim_terms & segment_terms)
            expanded = sorted(expanded_terms & segment_terms)
            semantic_score = (
                _cosine_similarity(claim_vector, semantic_segment_vectors[segment.id])
                if claim_vector is not None and segment.id in semantic_segment_vectors
                else None
            )
            semantic_hit = (
                semantic_score is not None
                and semantic_score >= min_semantic_similarity
            )
            if not matched and not expanded and not semantic_hit:
                continue
            cues = sorted(segment_terms & _CONTRARY_CUES)
            lexical_score = _bm25_score(
                matched,
                term_counts,
                segment_len=segment_lengths.get(segment.id, 0),
                average_segment_len=average_segment_len,
                segment_count=segment_count,
                document_frequency=document_frequency,
                k1=bm25_k1,
                b=bm25_b,
            ) + (
                expanded_term_weight * _bm25_score(
                    expanded,
                    term_counts,
                    segment_len=segment_lengths.get(segment.id, 0),
                    average_segment_len=average_segment_len,
                    segment_count=segment_count,
                    document_frequency=document_frequency,
                    k1=bm25_k1,
                    b=bm25_b,
                )
            ) + (contrary_cue_weight * len(cues))
            score = lexical_score
            if semantic_score is not None and semantic_hit:
                score += semantic_weight * semantic_score
            scored.append((
                score,
                len(cues),
                len(matched) + len(expanded),
                semantic_score,
                segment,
                matched,
                expanded,
                cues,
            ))

        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                -item[2],
                -(item[3] if item[3] is not None else -1.0),
                item[4].doc_id,
                item[4].start_char,
            )
        )
        for rank, (score, _cue_count, _match_count, semantic_score, segment, matched, expanded, cues) in enumerate(
            scored[:per_claim],
            start=1,
        ):
            doc = docs_by_id.get(segment.doc_id)
            span_hash = (
                quote_hash(doc.content, segment.start_char, segment.end_char)
                if doc is not None
                else None
            )
            candidates.append(DisconfirmationCandidate(
                id=f"dc-{target_index}-{rank}",
                target_claim_id=claim.id,
                claim_text=claim.claim_text,
                doc_id=segment.doc_id,
                segment_id=segment.id,
                start_char=segment.start_char,
                end_char=segment.end_char,
                quote_text=segment.text,
                quote_hash=span_hash,
                matched_terms=matched,
                expanded_terms=expanded,
                contrary_cues=cues,
                retrieval_mode=retrieval_mode,
                semantic_score=semantic_score,
                score=score,
            ))
    return candidates


def format_disconfirmation_candidates(candidates: Iterable[DisconfirmationCandidate]) -> str:
    """Format retrieved candidates for a negative-case prompt."""
    candidates = list(candidates)
    if not candidates:
        return (
            "RETRIEVED CANDIDATE PASSAGES: none. "
            "No lexical candidate passages were retrieved; do not treat this as evidence "
            "that no contrary evidence exists."
        )

    lines = [f"RETRIEVED CANDIDATE PASSAGES ({len(candidates)} total):"]
    for candidate in candidates:
        lines.append(
            f"- candidate_id={candidate.id} claim_id={candidate.target_claim_id} "
            f"doc_id={candidate.doc_id} segment_id={candidate.segment_id or ''} "
            f"span={candidate.start_char}:{candidate.end_char} "
            f"mode={candidate.retrieval_mode} "
            f"score={candidate.score:.2f} "
            f"semantic_score={_format_optional_score(candidate.semantic_score)} "
            f"matched_terms={','.join(candidate.matched_terms)} "
            f"expanded_terms={','.join(candidate.expanded_terms)} "
            f"contrary_cues={','.join(candidate.contrary_cues)}"
        )
        lines.append(format_untrusted_data_block(f"Disconfirmation candidate {candidate.id}", candidate.quote_text))
    return "\n".join(lines)


def anchor_for_candidate(candidate: DisconfirmationCandidate) -> ClaimAnchor:
    """Convert a retrieved candidate into a claim contrary anchor."""
    return ClaimAnchor(
        doc_id=candidate.doc_id,
        start_char=candidate.start_char,
        end_char=candidate.end_char,
        quote_text=candidate.quote_text,
        quote_hash=candidate.quote_hash,
        segment_id=candidate.segment_id,
    )


def _claim_terms(state: ProjectState, claim: AnalyticClaim) -> set[str]:
    """Terms from claim text plus scoped code names/descriptions."""
    return _terms(" ".join(_claim_parts(state, claim)))


def _claim_query_text(state: ProjectState, claim: AnalyticClaim) -> str:
    """Text used to embed one target claim for semantic retrieval."""
    return "\n".join(_claim_parts(state, claim))


def _claim_parts(state: ProjectState, claim: AnalyticClaim) -> list[str]:
    """Return claim text plus scoped code metadata for retrieval."""
    parts = [claim.claim_text, *claim.scope.participant_names]
    for code_id in claim.scope.code_ids:
        code = state.codebook.get_code(code_id)
        if code is None:
            continue
        parts.extend([code.name, code.description, code.definition])
    return [part for part in parts if part]


def _query_expansion_terms(
    claim_terms: set[str],
    query_expansions: Mapping[str, Iterable[str]] | None,
) -> set[str]:
    """Return configured expansion terms triggered by normalized claim terms."""
    source = _DEFAULT_QUERY_EXPANSIONS if query_expansions is None else query_expansions
    expanded: set[str] = set()
    for raw_trigger, raw_terms in source.items():
        trigger_terms = _terms(raw_trigger)
        if not trigger_terms or not (trigger_terms & claim_terms):
            continue
        if isinstance(raw_terms, str):
            values = [raw_terms]
        else:
            values = list(raw_terms)
        for raw in values:
            expanded.update(_terms(raw))
    return expanded - claim_terms


def _bm25_index(
    segments: Iterable[Segment],
) -> tuple[dict[str, Counter[str]], Counter[str], dict[str, int], float]:
    """Build term statistics for BM25-style segment scoring."""
    term_counts_by_segment: dict[str, Counter[str]] = {}
    document_frequency: Counter[str] = Counter()
    segment_lengths: dict[str, int] = {}
    total_terms = 0
    segment_count = 0
    for segment in segments:
        terms = _term_sequence(segment.text)
        counts: Counter[str] = Counter(terms)
        term_counts_by_segment[segment.id] = counts
        segment_lengths[segment.id] = len(terms)
        total_terms += len(terms)
        segment_count += 1
        for term in counts:
            document_frequency[term] += 1
    average_segment_len = total_terms / segment_count if segment_count else 0.0
    return term_counts_by_segment, document_frequency, segment_lengths, average_segment_len


def _bm25_score(
    query_terms: Iterable[str],
    term_counts: Counter[str],
    *,
    segment_len: int,
    average_segment_len: float,
    segment_count: int,
    document_frequency: Counter[str],
    k1: float,
    b: float,
) -> float:
    """Score one segment against query terms using the BM25 formula."""
    if segment_count == 0 or segment_len == 0 or average_segment_len == 0:
        return 0.0

    score = 0.0
    length_norm = 1 - b + (b * (segment_len / average_segment_len))
    for term in query_terms:
        tf = term_counts.get(term, 0)
        if tf == 0:
            continue
        df = document_frequency.get(term, 0)
        idf = log(1 + ((segment_count - df + 0.5) / (df + 0.5)))
        score += idf * ((tf * (k1 + 1)) / (tf + (k1 * length_norm)))
    return score


def _embedding_vectors_for_retrieval(
    state: ProjectState,
    claims: list[AnalyticClaim],
    segments: list[Segment],
    *,
    embedding_model: str | None,
    embedding_dimensions: int | None,
    embedding_provider: EmbeddingProvider | None,
    task: str,
    trace_id: str,
    max_budget: float,
) -> tuple[dict[int, list[float]], dict[str, list[float]]]:
    """Embed claim queries and segment texts for hybrid retrieval."""
    if not claims or not segments:
        return {}, {}
    if not embedding_model:
        raise ValueError("embedding_model is required when retrieval_mode='embedding_hybrid'")

    provider = embedding_provider or _llm_client_embedding_provider
    claim_texts = [_claim_query_text(state, claim) for claim in claims]
    segment_texts = [segment.text for segment in segments]
    texts = [*claim_texts, *segment_texts]
    raw_vectors = provider(
        texts,
        model=embedding_model,
        dimensions=embedding_dimensions,
        task=task,
        trace_id=trace_id,
        max_budget=max_budget,
    )
    vectors = _validated_embedding_vectors(raw_vectors, expected_count=len(texts))
    claim_vectors = {
        index: vectors[index]
        for index in range(len(claims))
    }
    offset = len(claims)
    segment_vectors = {
        segment.id: vectors[offset + index]
        for index, segment in enumerate(segments)
    }
    return claim_vectors, segment_vectors


def _llm_client_embedding_provider(
    texts: list[str],
    *,
    model: str,
    task: str,
    trace_id: str,
    max_budget: float,
    dimensions: int | None = None,
) -> list[list[float]]:
    """Embed texts through llm_client with pre-flight budget enforcement."""
    try:
        from llm_client import embed
        from llm_client.execution.call_contracts import check_budget
    except ImportError as exc:
        raise RuntimeError(
            "llm_client is required for embedding_hybrid disconfirmation retrieval"
        ) from exc

    check_budget(trace_id, max_budget)
    result = embed(
        model,
        texts,
        dimensions=dimensions,
        task=task,
        trace_id=trace_id,
    )
    return result.embeddings


def _validated_embedding_vectors(
    vectors: list[list[float]],
    *,
    expected_count: int,
) -> list[list[float]]:
    """Validate provider output before scoring candidates."""
    if len(vectors) != expected_count:
        raise RuntimeError(
            f"Embedding provider returned {len(vectors)} vector(s) for {expected_count} text(s)"
        )
    normalized: list[list[float]] = []
    width: int | None = None
    for index, raw_vector in enumerate(vectors):
        try:
            vector = [float(value) for value in raw_vector]
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"Embedding vector {index} contains a non-numeric value") from exc
        if not vector:
            raise RuntimeError(f"Embedding vector {index} is empty")
        if not any(value != 0.0 for value in vector):
            raise RuntimeError(f"Embedding vector {index} is all zeros")
        if width is None:
            width = len(vector)
        elif len(vector) != width:
            raise RuntimeError(
                f"Embedding vector {index} has dimension {len(vector)}; expected {width}"
            )
        normalized.append(vector)
    return normalized


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for validated non-zero vectors."""
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise RuntimeError("Embedding vectors must be non-zero for cosine similarity")
    return dot / (left_norm * right_norm)


def _format_optional_score(value: float | None) -> str:
    """Format an optional numeric candidate score for prompts."""
    return "none" if value is None else f"{value:.3f}"


def _terms(text: str) -> set[str]:
    """Normalize text to retrieval terms."""
    return set(_term_sequence(text))


def _term_sequence(text: str) -> list[str]:
    """Normalize text to an ordered retrieval term sequence."""
    sequence: list[str] = []
    for raw in _TOKEN_RE.findall(text.casefold()):
        term = raw.strip("'_-")
        if len(term) < 2 or term in _STOPWORDS:
            continue
        sequence.append(term)
    return sequence
