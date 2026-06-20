"""Span-anchored quote grounding (INV-1).

Resolves an LLM-produced quote to an exact, verifiable location in the source
documents: original-document character offsets plus a content hash of the
resolved span. Matching is robust to smart quotes, whitespace, and case, but the
offsets and hash always index the *original* ``Document.content`` so the evidence
link can be re-verified.

Uniqueness rule (the "three people said 'I felt ignored'" problem): a quote is
only anchorable when it occurs **exactly once across the whole corpus**. Zero
occurrences = unresolvable; more than one = ambiguous. In both non-unique cases
the caller must drop the application rather than fabricate provenance — a false
evidence link is worse than a missing one.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence

# Smart quotes / dashes / ellipsis that LLMs and transcript tools introduce.
_CHAR_FOLD = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"',
    "–": "-", "—": "-", "―": "-",
    " ": " ", "…": "...",
}


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


def resolve_span(quote: str, content: str) -> SpanMatch:
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
        return SpanMatch(status=MatchStatus.NONE, occurrences=0)
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


def resolve_against_docs(quote: str, documents: Sequence) -> DocSpanMatch:
    """Resolve ``quote`` across a corpus. UNIQUE only if it occurs exactly once
    in the entire corpus; otherwise AMBIGUOUS (>1) or NONE (0)."""
    total = 0
    unique_hit: Optional[tuple] = None
    for doc in documents:
        m = resolve_span(quote, doc.content)
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


def resolve_and_anchor(quote, documents, *, code_id, codebook_version, confidence):
    """Resolve ``quote`` across ``documents`` and build an anchored application.

    Returns ``(CodeApplication | None, MatchStatus)``. UNIQUE → a fully anchored
    application (doc_id + offsets + hash); AMBIGUOUS / NONE → ``(None, status)`` so
    the caller can drop it and count the reason. Shared by the thematic and both
    incremental coding paths (was duplicated three times).
    """
    from qc_clean.schemas.domain import CodeApplication, Provenance
    m = resolve_against_docs(quote, documents)
    if m.status is not MatchStatus.UNIQUE:
        return None, m.status
    return CodeApplication(
        code_id=code_id,
        doc_id=m.doc_id,
        quote_text=quote,
        start_char=m.start_char,
        end_char=m.end_char,
        quote_hash=m.quote_hash,
        confidence=confidence,
        applied_by=Provenance.LLM,
        codebook_version=codebook_version,
    ), m.status


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
