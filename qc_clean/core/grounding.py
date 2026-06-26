"""Span-anchored quote grounding (INV-1).

Resolves an LLM-produced quote to an exact, verifiable location in the source
documents: original-document character offsets plus a content hash of the
resolved span. Matching first uses normalized exact substrings robust to smart
quotes, whitespace, and case. If exact matching finds no occurrences, a
conservative token-window fuzzy fallback may recover one long near-verbatim span.
Offsets and hashes always index the *original* ``Document.content`` so the
evidence link can be re-verified.

Uniqueness rule (the "three people said 'I felt ignored'" problem): a quote is
only anchorable when it occurs **exactly once across the whole corpus**. Zero
occurrences = unresolvable; more than one = ambiguous. In both non-unique cases
the caller must drop the application rather than fabricate provenance — a false
evidence link is worse than a missing one.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import List, Optional, Sequence

# Smart quotes / dashes / ellipsis that LLMs and transcript tools introduce.
_CHAR_FOLD = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "―": "-",
    " ": " ", "…": "...",
}

DEFAULT_FUZZY_MIN_RATIO = 0.9
DEFAULT_FUZZY_MIN_TOKENS = 4
DEFAULT_FUZZY_MIN_TOKEN_RATIO = 0.75
DEFAULT_FUZZY_MAX_TOKEN_RATIO = 1.35
DEFAULT_FUZZY_MAX_QUOTE_TOKENS = 40
DEFAULT_FUZZY_MAX_QUOTE_CHARS = 280
_SOURCE_PREFIX_SPEAKER_RE = re.compile(r"\s*([A-Z][A-Za-z0-9 ._'\-]{0,60}?):\s*")


class MatchStatus(str, Enum):
    UNIQUE = "unique"
    AMBIGUOUS = "ambiguous"
    NONE = "none"


@dataclass
class SpanMatch:
    """Result of resolving a quote within a single document's content."""
    status: MatchStatus
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    matched_text: Optional[str] = None
    quote_hash: Optional[str] = None
    occurrences: int = 0


@dataclass
class DocSpanMatch:
    """Result of resolving a quote across a corpus of documents."""
    status: MatchStatus
    doc_id: Optional[str] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    matched_text: Optional[str] = None
    quote_hash: Optional[str] = None
    total_occurrences: int = 0


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def quote_hash(content: str, start: int, end: int) -> str:
    """Hash of the exact source span ``content[start:end]`` (for re-verification)."""
    return _sha256(content[start:end])


def _normalize_with_map(text: str) -> tuple[str, List[int]]:
    """Normalize ``text`` for matching and return (normalized, index_map).

    ``index_map[i]`` is the index in the *original* ``text`` of the original
    character that produced normalized character ``i``. Normalization: per-char
    NFKC + smart-char folding + casefold, with runs of whitespace collapsed to a
    single space. Casefold may expand one char into several; each maps back to
    the same original index, which keeps offset recovery correct.
    """
    norm_chars: List[str] = []
    index_map: List[int] = []
    prev_space = False
    for i, ch in enumerate(text):
        ch = _CHAR_FOLD.get(ch, ch)
        if ch.isspace():
            if not prev_space:
                norm_chars.append(" ")
                index_map.append(i)
                prev_space = True
            continue
        prev_space = False
        folded = unicodedata.normalize("NFKC", ch).casefold()
        for c in folded:
            norm_chars.append(c)
            index_map.append(i)
    return "".join(norm_chars), index_map


def resolve_span(quote: str, content: str, *, allow_fuzzy: bool = True) -> SpanMatch:
    """Resolve ``quote`` to a unique char span in a single document's ``content``."""
    norm_doc, index_map = _normalize_with_map(content)
    norm_quote = _normalize_with_map(quote)[0].strip()
    if not norm_quote:
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)

    starts: List[int] = []
    pos = norm_doc.find(norm_quote)
    while pos != -1:
        starts.append(pos)
        pos = norm_doc.find(norm_quote, pos + 1)

    if not starts:
        if not allow_fuzzy:
            return SpanMatch(status=MatchStatus.NONE, occurrences=0)
        return _resolve_fuzzy_span(norm_quote, norm_doc, index_map, content)
    if len(starts) > 1:
        return SpanMatch(status=MatchStatus.AMBIGUOUS, occurrences=len(starts))

    ns = starts[0]
    ne = ns + len(norm_quote)
    start = index_map[ns]
    end = index_map[ne - 1] + 1
    matched = content[start:end]
    return SpanMatch(
        status=MatchStatus.UNIQUE,
        start_char=start,
        end_char=end,
        matched_text=matched,
        quote_hash=_sha256(matched),
        occurrences=1,
    )


@dataclass(frozen=True)
class _FuzzyCandidate:
    """One normalized token-window fuzzy candidate."""

    ratio: float
    token_start: int
    token_end: int
    norm_start: int
    norm_end: int


def _resolve_fuzzy_span(
    norm_quote: str,
    norm_doc: str,
    index_map: List[int],
    content: str,
    *,
    min_ratio: float = DEFAULT_FUZZY_MIN_RATIO,
    min_tokens: int = DEFAULT_FUZZY_MIN_TOKENS,
) -> SpanMatch:
    """Resolve a near-verbatim quote with conservative fuzzy token windows."""
    if len(norm_quote) > DEFAULT_FUZZY_MAX_QUOTE_CHARS:
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)

    quote_tokens = _token_spans(norm_quote)
    doc_tokens = _token_spans(norm_doc)
    if len(quote_tokens) > DEFAULT_FUZZY_MAX_QUOTE_TOKENS:
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)
    if len(quote_tokens) < min_tokens or not doc_tokens:
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)

    candidates = _fuzzy_candidates(norm_quote, quote_tokens, doc_tokens, min_ratio)
    selected = _select_non_overlapping_fuzzy_candidates(candidates)
    if not selected:
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)
    if len(selected) > 1:
        return SpanMatch(status=MatchStatus.AMBIGUOUS, occurrences=len(selected))

    candidate = selected[0]
    start = index_map[candidate.norm_start]
    end = index_map[candidate.norm_end - 1] + 1
    matched = content[start:end]
    return SpanMatch(
        status=MatchStatus.UNIQUE,
        start_char=start,
        end_char=end,
        matched_text=matched,
        quote_hash=_sha256(matched),
        occurrences=1,
    )


def _token_spans(text: str) -> list[tuple[str, int, int]]:
    """Return normalized word-like token spans."""
    return [(match.group(0), match.start(), match.end()) for match in re.finditer(r"[\w']+", text)]


def _fuzzy_candidates(
    norm_quote: str,
    quote_tokens: list[tuple[str, int, int]],
    doc_tokens: list[tuple[str, int, int]],
    min_ratio: float,
) -> list[_FuzzyCandidate]:
    """Return best fuzzy token window per start position above threshold."""
    min_len = max(1, int(len(quote_tokens) * DEFAULT_FUZZY_MIN_TOKEN_RATIO))
    max_len = max(min_len, int(len(quote_tokens) * DEFAULT_FUZZY_MAX_TOKEN_RATIO + 0.999))
    candidates: list[_FuzzyCandidate] = []
    for token_start in range(len(doc_tokens)):
        best: _FuzzyCandidate | None = None
        for window_len in range(min_len, max_len + 1):
            token_end = token_start + window_len
            if token_end > len(doc_tokens):
                continue
            candidate_text = " ".join(token for token, _, _ in doc_tokens[token_start:token_end])
            ratio = SequenceMatcher(None, norm_quote, candidate_text).ratio()
            if ratio < min_ratio:
                continue
            candidate = _FuzzyCandidate(
                ratio=ratio,
                token_start=token_start,
                token_end=token_end,
                norm_start=doc_tokens[token_start][1],
                norm_end=doc_tokens[token_end - 1][2],
            )
            if best is None or candidate.ratio > best.ratio:
                best = candidate
        if best is not None:
            candidates.append(best)
    return candidates


def _select_non_overlapping_fuzzy_candidates(
    candidates: list[_FuzzyCandidate],
) -> list[_FuzzyCandidate]:
    """Keep the highest-ratio non-overlapping fuzzy candidate regions."""
    selected: list[_FuzzyCandidate] = []
    for candidate in sorted(candidates, key=lambda item: item.ratio, reverse=True):
        if any(_token_ranges_overlap(candidate, existing) for existing in selected):
            continue
        selected.append(candidate)
    return sorted(selected, key=lambda item: item.token_start)


def _token_ranges_overlap(left: _FuzzyCandidate, right: _FuzzyCandidate) -> bool:
    """Return whether two fuzzy token ranges overlap."""
    return left.token_start < right.token_end and right.token_start < left.token_end


def resolve_against_docs(
    quote: str,
    documents: Sequence,
    *,
    allow_fuzzy: bool = True,
) -> DocSpanMatch:
    """Resolve ``quote`` across a corpus. UNIQUE only if it occurs exactly once
    in the entire corpus; otherwise AMBIGUOUS (>1) or NONE (0)."""
    total = 0
    unique_hit: Optional[tuple] = None
    for doc in documents:
        m = resolve_span(quote, doc.content, allow_fuzzy=allow_fuzzy)
        total += m.occurrences
        if m.status == MatchStatus.UNIQUE:
            unique_hit = (doc, m)

    if total != 1 or unique_hit is None:
        status = MatchStatus.NONE if total == 0 else MatchStatus.AMBIGUOUS
        return DocSpanMatch(status=status, total_occurrences=total)

    doc, m = unique_hit  # exactly one occurrence -> exactly one unique hit
    return DocSpanMatch(
        status=MatchStatus.UNIQUE,
        doc_id=doc.id,
        start_char=m.start_char,
        end_char=m.end_char,
        matched_text=m.matched_text,
        quote_hash=m.quote_hash,
        total_occurrences=1,
    )


def _speaker_for_containing_segment(
    doc_id: str,
    start_char: int,
    end_char: int,
    segments: Optional[Sequence] = None,
) -> Optional[str]:
    """Return the speaker for the same-document segment containing a span."""
    if not segments:
        return None
    for segment in segments:
        if (
            segment.doc_id == doc_id
            and segment.start_char <= start_char
            and end_char <= segment.end_char
            and segment.speaker
        ):
            return segment.speaker
    return None


def _document_content(doc_id: str, documents: Sequence) -> Optional[str]:
    """Return document content for *doc_id* from a document-like sequence."""
    for doc in documents:
        if getattr(doc, "id", None) == doc_id:
            return getattr(doc, "content", None)
    return None


def _speaker_from_source_prefix(
    content: str | None,
    start_char: int,
) -> Optional[str]:
    """Return explicit same-line ``Speaker:`` prefix before an anchored span."""
    if content is None or start_char < 0 or start_char > len(content):
        return None
    line_start = content.rfind("\n", 0, start_char) + 1
    prefix = content[line_start:start_char]
    match = _SOURCE_PREFIX_SPEAKER_RE.fullmatch(prefix)
    if match is None:
        return None
    speaker = match.group(1).strip()
    return speaker or None


def resolve_and_anchor(
    quote,
    documents,
    *,
    code_id,
    codebook_version,
    confidence,
    segments: Optional[Sequence] = None,
    allow_fuzzy: bool = True,
):
    """Resolve ``quote`` across ``documents`` and build an anchored application.

    Returns ``(CodeApplication | None, DocSpanMatch)``. UNIQUE → a fully anchored
    application (doc_id + offsets + hash); AMBIGUOUS / NONE → ``(None, status)`` so
    the caller can drop it and count the reason. Shared by the thematic and both
    incremental coding paths (was duplicated three times). When ``segments`` are
    supplied, speaker is copied from the containing same-document segment.
    """
    from qc_clean.schemas.domain import CodeApplication, Provenance
    m = resolve_against_docs(quote, documents, allow_fuzzy=allow_fuzzy)
    if m.status is not MatchStatus.UNIQUE:
        return None, m
    segment_speaker = _speaker_for_containing_segment(
        m.doc_id,
        m.start_char,
        m.end_char,
        segments,
    )
    return CodeApplication(
        code_id=code_id,
        doc_id=m.doc_id,
        quote_text=quote,
        speaker=segment_speaker
        or _speaker_from_source_prefix(_document_content(m.doc_id, documents), m.start_char),
        start_char=m.start_char,
        end_char=m.end_char,
        quote_hash=m.quote_hash,
        confidence=confidence,
        applied_by=Provenance.LLM,
        codebook_version=codebook_version,
    ), m


def warn_unanchored(state, unresolvable: int, ambiguous: int, label: str = "") -> None:
    """Append INV-1 data_warnings for dropped (unresolvable / ambiguous) quotes."""
    prefix = f"{label}: " if label else ""
    if unresolvable:
        state.data_warnings.append(
            f"{prefix}{unresolvable} quote(s) matched no source document and were "
            f"dropped as unanchored (INV-1)."
        )
    if ambiguous:
        state.data_warnings.append(
            f"{prefix}{ambiguous} quote(s) occurred more than once in the corpus and "
            f"could not be uniquely anchored; dropped rather than misattributed (INV-1)."
        )


def grounding_issue(
    *,
    stage_name: str,
    code_id: str,
    quote: str,
    status,
    occurrence_count: int,
):
    """Build a remediation record for a dropped quote candidate."""
    from qc_clean.schemas.domain import GroundingIssue, GroundingIssueStatus

    remediation = {
        GroundingIssueStatus.NO_SOURCE_MATCH: (
            "Review the source transcript and either correct the quote text, "
            "replace it with an exact source span, or remove the evidence item."
        ),
        GroundingIssueStatus.AMBIGUOUS_MATCH: (
            "Review duplicate source occurrences and select the intended "
            "document/span before using this quote as evidence."
        ),
    }[status]
    return GroundingIssue(
        stage_name=stage_name,
        code_id=code_id,
        quote_text=quote,
        status=status,
        occurrence_count=occurrence_count,
        remediation_hint=remediation,
    )


def verify_anchor(content: str, start: Optional[int], end: Optional[int],
                  expected_hash: Optional[str]) -> bool:
    """True iff the span at [start:end] still hashes to ``expected_hash``."""
    if start is None or end is None or expected_hash is None:
        return False
    if start < 0 or end > len(content) or start >= end:
        return False
    return _sha256(content[start:end]) == expected_hash


@dataclass
class GroundingReport:
    """How well a project's code applications are anchored to source spans (D1)."""
    total_applications: int = 0
    anchored_verified: int = 0   # offsets + hash present AND re-verify against the doc
    anchored_no_hash: int = 0    # has a doc_id but missing/partial offsets+hash
    hash_mismatch: int = 0       # hash present but the span no longer matches (drift/tamper)
    missing_doc: int = 0         # references a doc_id not in the corpus
    grounding_rate: float = 1.0  # anchored_verified / total (1.0 when no applications)


def verify_grounding(state) -> GroundingReport:
    """Recompute anchors for every application and report grounding quality.

    This is the D1 metric: ``grounding_rate`` is the fraction of applications
    whose stored span (``start_char``/``end_char``/``quote_hash``) still resolves
    to the same source text. It re-derives from the corpus, so it catches drift,
    fabricated provenance, and unanchored applications.
    """
    docs = {d.id: d.content for d in state.corpus.documents}
    report = GroundingReport(total_applications=len(state.code_applications))
    for app in state.code_applications:
        content = docs.get(app.doc_id)
        if content is None:
            report.missing_doc += 1
            continue
        if app.quote_hash is None or app.start_char is None or app.end_char is None:
            report.anchored_no_hash += 1
            continue
        if verify_anchor(content, app.start_char, app.end_char, app.quote_hash):
            report.anchored_verified += 1
        else:
            report.hash_mismatch += 1
    total = report.total_applications
    report.grounding_rate = (report.anchored_verified / total) if total else 1.0
    return report
