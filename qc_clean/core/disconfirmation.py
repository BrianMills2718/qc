"""
Retrieval-first disconfirmation helpers.

This module surfaces source passages before negative-case interpretation. The
retriever is deliberately deterministic and local: it scores char-anchored
segments against claim/code terms and contradiction cues, then formats bounded
candidates for the LLM to assess.
"""

from __future__ import annotations

import re
from typing import Iterable

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
    contrary_cues: list[str] = Field(description="Contradiction/exception cue terms found in the passage")
    score: float = Field(description="Deterministic retrieval score used for ranking")


def retrieve_disconfirmation_candidates(
    state: ProjectState,
    targets: Iterable[AnalyticClaim],
    *,
    candidates_per_claim: int = 5,
) -> list[DisconfirmationCandidate]:
    """Return bounded retrieved source candidates for each target claim."""
    if not state.segments:
        state.segments = segment_corpus(state.corpus.documents)

    docs_by_id = {doc.id: doc for doc in state.corpus.documents}
    candidates: list[DisconfirmationCandidate] = []
    per_claim = max(0, candidates_per_claim)
    if per_claim == 0:
        return candidates

    for target_index, claim in enumerate(targets):
        claim_terms = _claim_terms(state, claim)
        if not claim_terms:
            continue
        scored: list[tuple[float, int, int, Segment, list[str], list[str]]] = []
        for segment in state.segments:
            segment_terms = _terms(segment.text)
            matched = sorted(claim_terms & segment_terms)
            if not matched:
                continue
            cues = sorted(segment_terms & _CONTRARY_CUES)
            score = float(len(matched)) + (1.25 * len(cues))
            scored.append((score, len(cues), len(matched), segment, matched, cues))

        scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3].doc_id, item[3].start_char))
        for rank, (score, _cue_count, _match_count, segment, matched, cues) in enumerate(
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
                contrary_cues=cues,
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
            f"score={candidate.score:.2f} "
            f"matched_terms={','.join(candidate.matched_terms)} "
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
    parts = [claim.claim_text, *claim.scope.participant_names]
    for code_id in claim.scope.code_ids:
        code = state.codebook.get_code(code_id)
        if code is None:
            continue
        parts.extend([code.name, code.description, code.definition])
    return _terms(" ".join(parts))


def _terms(text: str) -> set[str]:
    """Normalize text to retrieval terms."""
    terms: set[str] = set()
    for raw in _TOKEN_RE.findall(text.casefold()):
        term = raw.strip("'_-")
        if len(term) < 2 or term in _STOPWORDS:
            continue
        terms.add(term)
    return terms
