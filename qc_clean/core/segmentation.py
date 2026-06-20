"""Char-anchored corpus segmentation — the INV-8 segment universe.

Splits each document into a stable, identified set of textual units (segments)
whose char offsets index the *original* ``Document.content``. This is the
denominator the system was missing: coverage, application-level agreement,
prevalence, and "absence of evidence" can all be computed against this set.

Unlike the GT constant-comparison segmenter (which strips text and tracks no
offsets), every segment here round-trips: ``doc.content[seg.start_char:seg.end_char]
== seg.text``. Speaker transcripts split by speaker turn; otherwise by paragraph.

This module only builds the registry; it adds no LLM calls. Forcing a coding
decision on *every* segment (exhaustive coding) is the separate, cost-bearing
step that turns traversal coverage into examined-and-judged coverage — it now
ships behind `project run --exhaustive` (see `ThematicCodingStage._execute_exhaustive`
and `compute_coverage`, whose `mode` flips to "examined" once decisions exist).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from qc_clean.schemas.domain import Document, Segment


def _trim_span(content: str, start: int, end: int) -> Tuple[int, int]:
    """Shrink [start, end) to exclude leading/trailing whitespace."""
    while start < end and content[start].isspace():
        start += 1
    while end > start and content[end - 1].isspace():
        end -= 1
    return start, end


def speaker_turn_pattern(speakers: Sequence[str]):
    """Compiled regex matching any known speaker label at line start.

    Single source of truth for speaker-turn detection — used by both the
    char-anchored segmenter here and the GT constant-comparison segmenter.
    Returns None when there are no usable speaker names.
    """
    escaped = [re.escape(s) for s in speakers if s]
    if not escaped:
        return None
    return re.compile(
        r"^(" + "|".join(escaped) + r")(?::\s|\s{2,}\d+:\d{2})",
        re.MULTILINE,
    )


def _speaker_turn_spans(content: str, speakers: Sequence[str]) -> List[Tuple[int, int, str]]:
    """Return (start, end, speaker) raw spans for each speaker turn, or []."""
    pattern = speaker_turn_pattern(speakers)
    if pattern is None:
        return []
    matches = list(pattern.finditer(content))
    if not matches:
        return []
    spans: List[Tuple[int, int, str]] = []
    for i, m in enumerate(matches):
        text_start = m.end()
        text_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        spans.append((text_start, text_end, m.group(1)))
    return spans


def _paragraph_spans(content: str) -> List[Tuple[int, int, str]]:
    """Return (start, end, "") spans for blank-line-separated paragraphs."""
    spans: List[Tuple[int, int, str]] = []
    idx = 0
    for part in re.split(r"\n\s*\n", content):
        if not part:
            continue
        start = content.find(part, idx)
        if start == -1:
            start = idx
        end = start + len(part)
        idx = end
        spans.append((start, end, ""))
    return spans


def segment_document(doc: Document) -> List[Segment]:
    """Split one document into char-anchored segments."""
    raw = (
        _speaker_turn_spans(doc.content, doc.detected_speakers)
        if doc.detected_speakers
        else _paragraph_spans(doc.content)
    )
    if not raw:
        # Fall back to the whole document as a single segment.
        s, e = _trim_span(doc.content, 0, len(doc.content))
        raw = [(s, e, "")] if e > s else []

    segments: List[Segment] = []
    for start, end, speaker in raw:
        s, e = _trim_span(doc.content, start, end)
        if e <= s:
            continue
        segments.append(Segment(
            doc_id=doc.id,
            index=len(segments),
            start_char=s,
            end_char=e,
            speaker=speaker,
            text=doc.content[s:e],
        ))
    return segments


def segment_corpus(documents: Sequence[Document]) -> List[Segment]:
    """Char-anchored segments across all documents (the segment universe)."""
    out: List[Segment] = []
    for doc in documents:
        out.extend(segment_document(doc))
    return out


@dataclass
class CoverageReport:
    """Corpus coverage against the segment universe (INV-8 denominator).

    Two notions, both honest:
    - *traversal* coverage (`covered_*`): segments touched by an anchored
      application. Works in any mode.
    - *examined-and-judged* coverage (`examined_*`): segments that received an
      explicit decision (coded or no_code) under exhaustive coding. Only this
      distinguishes "not relevant" from "never examined".
    """
    total_segments: int = 0
    covered_segments: int = 0           # overlapped by >=1 anchored application
    coverage_rate: float = 0.0          # covered / total
    examined_segments: int = 0          # decision is not None (exhaustive coding)
    coded_segments: int = 0             # decision == "coded"
    examined_rate: float = 0.0          # examined / total
    mode: str = "traversal"             # "examined" once any segment has a decision


def compute_coverage(state) -> CoverageReport:
    """Coverage of the segment universe (INV-8).

    Traversal coverage = segments overlapped by an INV-1-anchored application
    (unanchored apps can't contribute). Examined coverage = segments with an
    explicit exhaustive-coding decision. When every segment is examined,
    `examined_rate == 1.0` and the denominator is fully defensible.
    """
    segments = state.segments
    total = len(segments)
    if total == 0:
        return CoverageReport()

    apps_by_doc: dict = {}
    for app in state.code_applications:
        if app.start_char is None or app.end_char is None:
            continue
        apps_by_doc.setdefault(app.doc_id, []).append((app.start_char, app.end_char))

    covered = examined = coded = 0
    for seg in segments:
        for a_start, a_end in apps_by_doc.get(seg.doc_id, ()):
            if a_start < seg.end_char and a_end > seg.start_char:
                covered += 1
                break
        if seg.decision is not None:
            examined += 1
            if seg.decision == "coded":
                coded += 1

    return CoverageReport(
        total_segments=total,
        covered_segments=covered,
        coverage_rate=covered / total,
        examined_segments=examined,
        coded_segments=coded,
        examined_rate=examined / total,
        mode="examined" if examined else "traversal",
    )
