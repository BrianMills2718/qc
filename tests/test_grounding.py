"""Tests for span-anchored quote grounding (INV-1, Phase 1)."""

from dataclasses import dataclass

from qc_clean.core.grounding import (
    MatchStatus,
    quote_hash,
    resolve_against_docs,
    resolve_span,
    verify_anchor,
)


@dataclass
class _Doc:
    id: str
    content: str


# --- single-doc resolution: offsets must index the ORIGINAL content ----------

def test_unique_match_returns_exact_offsets():
    content = "Alex: I do my best work when no one is hovering. It matters."
    m = resolve_span("I do my best work when no one is hovering", content)
    assert m.status == MatchStatus.UNIQUE
    assert content[m.start_char:m.end_char] == "I do my best work when no one is hovering"
    assert m.quote_hash == quote_hash(content, m.start_char, m.end_char)


def test_smart_quotes_and_whitespace_tolerated_but_original_returned():
    # Document uses straight quotes + double spaces; quote uses smart quotes.
    content = "She said  'trust  is everything' to the team."
    m = resolve_span("‘trust is everything’", content)
    assert m.status == MatchStatus.UNIQUE
    # Offsets recover the ORIGINAL substring (with its double space + straight quotes).
    assert content[m.start_char:m.end_char] == "'trust  is everything'"


def test_case_insensitive_match():
    content = "Autonomy VERSUS oversight was the core tension."
    m = resolve_span("autonomy versus oversight", content)
    assert m.status == MatchStatus.UNIQUE
    assert content[m.start_char:m.end_char] == "Autonomy VERSUS oversight"


def test_no_match_is_none():
    content = "Nothing relevant here."
    assert resolve_span("a paraphrase the model invented", content).status == MatchStatus.NONE


def test_repeated_phrase_in_one_doc_is_ambiguous():
    content = "I felt ignored. Later, I felt ignored again."
    m = resolve_span("I felt ignored", content)
    assert m.status == MatchStatus.AMBIGUOUS
    assert m.occurrences == 2


# --- corpus-level resolution: unique only if exactly one occurrence total -----

def test_unique_across_corpus():
    docs = [_Doc("d1", "Alex values autonomy above all."),
            _Doc("d2", "Sam prefers structure and check-ins.")]
    m = resolve_against_docs("values autonomy", docs)
    assert m.status == MatchStatus.UNIQUE
    assert m.doc_id == "d1"
    assert docs[0].content[m.start_char:m.end_char] == "values autonomy"


def test_same_phrase_in_two_docs_is_ambiguous_not_misattributed():
    # The reviewer's case: three people say the same thing -> cannot anchor.
    docs = [_Doc("d1", "I felt ignored by management."),
            _Doc("d2", "Honestly, I felt ignored too."),
            _Doc("d3", "I felt ignored in every meeting.")]
    m = resolve_against_docs("I felt ignored", docs)
    assert m.status == MatchStatus.AMBIGUOUS
    assert m.total_occurrences == 3
    assert m.doc_id is None  # never guesses a document


def test_zero_occurrence_is_none():
    docs = [_Doc("d1", "content one"), _Doc("d2", "content two")]
    assert resolve_against_docs("not present anywhere", docs).status == MatchStatus.NONE


# --- anchor verification ------------------------------------------------------

def test_verify_anchor_roundtrip():
    content = "The quote lives right here in the document."
    m = resolve_span("right here", content)
    assert verify_anchor(content, m.start_char, m.end_char, m.quote_hash)
    # Tampered content fails verification.
    assert not verify_anchor(content.replace("right here", "somewhere else"),
                             m.start_char, m.end_char, m.quote_hash)


def test_verify_anchor_rejects_missing_or_out_of_range():
    assert not verify_anchor("abc", None, 2, "x")
    assert not verify_anchor("abc", 0, 99, "x")
    assert not verify_anchor("abc", 2, 1, "x")
