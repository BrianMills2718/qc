"""Tests for span-anchored quote grounding (INV-1, Phase 1)."""

from dataclasses import dataclass

from qc_clean.core.grounding import (
    MatchStatus,
    quote_hash,
    resolve_against_docs,
    resolve_span,
    verify_anchor,
    verify_grounding,
)
from qc_clean.schemas.domain import (
    CodeApplication,
    Corpus,
    Document,
    ProjectState,
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


def test_fuzzy_match_recovers_near_verbatim_elision():
    content = (
        "Alex: I do my best work when no one is hovering nearby during planning. "
        "It matters."
    )

    m = resolve_span("I do best work when no one hovering nearby during planning", content)

    assert m.status == MatchStatus.UNIQUE
    assert content[m.start_char:m.end_char] == (
        "I do my best work when no one is hovering nearby during planning"
    )
    assert verify_anchor(content, m.start_char, m.end_char, m.quote_hash)


def test_fuzzy_match_does_not_override_exact_ambiguity():
    content = "I felt ignored. Later, I felt ignored again."

    m = resolve_span("I felt ignored", content)

    assert m.status == MatchStatus.AMBIGUOUS
    assert m.occurrences == 2


def test_fuzzy_match_repeated_near_matches_are_ambiguous():
    content = (
        "I do my best work when no one is hovering. "
        "Later, I do my best work when no one is hovering again."
    )

    m = resolve_span("I do best work when no one hovering", content)

    assert m.status == MatchStatus.AMBIGUOUS
    assert m.occurrences == 2


def test_fuzzy_match_rejects_short_vague_quote():
    content = "Trust matters a lot in this process."

    m = resolve_span("trst", content)

    assert m.status == MatchStatus.NONE


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


# --- verify_grounding report --------------------------------------------------

def _state_with_apps(content: str, apps):
    doc = Document(name="d.txt", content=content)
    for a in apps:
        a.doc_id = a.doc_id or doc.id
    return ProjectState(
        name="t",
        corpus=Corpus(documents=[doc]),
        code_applications=apps,
    ), doc


def test_grounding_report_counts_verified_unhashed_mismatch_and_missing():
    content = "The quote lives right here in the document, clearly."
    m = resolve_span("right here", content)
    apps = [
        # verified: correct offsets + hash
        CodeApplication(code_id="c", doc_id="", quote_text="right here",
                        start_char=m.start_char, end_char=m.end_char, quote_hash=m.quote_hash),
        # no hash: doc_id only
        CodeApplication(code_id="c", doc_id="", quote_text="clearly"),
        # hash mismatch: wrong hash for the span
        CodeApplication(code_id="c", doc_id="", quote_text="the quote",
                        start_char=0, end_char=9, quote_hash="deadbeef"),
        # missing doc
        CodeApplication(code_id="c", doc_id="no-such-doc", quote_text="x",
                        start_char=0, end_char=1, quote_hash="z"),
    ]
    state, _ = _state_with_apps(content, apps)
    r = verify_grounding(state)
    assert r.total_applications == 4
    assert r.anchored_verified == 1
    assert r.anchored_no_hash == 1
    assert r.hash_mismatch == 1
    assert r.missing_doc == 1
    assert abs(r.grounding_rate - 0.25) < 1e-9


def test_grounding_rate_is_one_when_no_applications():
    state = ProjectState(name="t", corpus=Corpus(documents=[]))
    assert verify_grounding(state).grounding_rate == 1.0


def test_resolve_and_anchor_builds_app_or_returns_status():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor
    docs = [_Doc("d1", "Alex values autonomy."), _Doc("d2", "Sam felt rushed. Sam felt rushed.")]
    # unique -> anchored application
    app, status = resolve_and_anchor("values autonomy", docs, code_id="C1",
                                     codebook_version=1, confidence=0.8)
    assert status is MatchStatus.UNIQUE
    assert app is not None and app.code_id == "C1" and app.doc_id == "d1"
    assert app.quote_hash is not None and app.confidence == 0.8
    # ambiguous (twice in d2) -> no app
    app2, status2 = resolve_and_anchor("Sam felt rushed", docs, code_id="C1",
                                       codebook_version=1, confidence=0.5)
    assert app2 is None and status2 is MatchStatus.AMBIGUOUS
    # none -> no app
    app3, status3 = resolve_and_anchor("not present", docs, code_id="C1",
                                       codebook_version=1, confidence=0.5)
    assert app3 is None and status3 is MatchStatus.NONE


def test_resolve_and_anchor_derives_speaker_from_containing_segment():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor
    from qc_clean.schemas.domain import Segment

    content = "Alex: values autonomy.\nSam: felt rushed."
    docs = [_Doc("d1", content)]
    start = content.index("values autonomy")
    end = start + len("values autonomy")
    segments = [
        Segment(
            doc_id="d1",
            index=0,
            start_char=content.index("values autonomy"),
            end_char=end,
            speaker="Alex",
            text="values autonomy",
        )
    ]

    app, status = resolve_and_anchor(
        "values autonomy",
        docs,
        code_id="C1",
        codebook_version=1,
        confidence=0.8,
        segments=segments,
    )

    assert status is MatchStatus.UNIQUE
    assert app is not None
    assert app.speaker == "Alex"


def test_resolve_and_anchor_derives_speaker_from_source_prefix_without_segments():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor

    content = "Alex: values autonomy.\nSam: felt rushed."
    docs = [_Doc("d1", content)]

    app, status = resolve_and_anchor(
        "values autonomy",
        docs,
        code_id="C1",
        codebook_version=1,
        confidence=0.8,
    )

    assert status is MatchStatus.UNIQUE
    assert app is not None
    assert app.speaker == "Alex"


def test_resolve_and_anchor_prefers_containing_segment_speaker_over_prefix():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor
    from qc_clean.schemas.domain import Segment

    content = "Source Label: values autonomy."
    docs = [_Doc("d1", content)]
    start = content.index("values autonomy")
    end = start + len("values autonomy")
    segments = [
        Segment(
            doc_id="d1",
            index=0,
            start_char=start,
            end_char=end,
            speaker="Segment Speaker",
            text="values autonomy",
        )
    ]

    app, status = resolve_and_anchor(
        "values autonomy",
        docs,
        code_id="C1",
        codebook_version=1,
        confidence=0.8,
        segments=segments,
    )

    assert status is MatchStatus.UNIQUE
    assert app is not None
    assert app.speaker == "Segment Speaker"


def test_resolve_and_anchor_does_not_infer_speaker_from_plain_prefix_text():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor

    content = "The interviewer notes values autonomy as important."
    docs = [_Doc("d1", content)]

    app, status = resolve_and_anchor(
        "values autonomy",
        docs,
        code_id="C1",
        codebook_version=1,
        confidence=0.8,
    )

    assert status is MatchStatus.UNIQUE
    assert app is not None
    assert app.speaker is None


def test_resolve_and_anchor_leaves_speaker_empty_without_containing_segment():
    from qc_clean.core.grounding import MatchStatus, resolve_and_anchor
    from qc_clean.schemas.domain import Segment

    content = "Speakerless values autonomy."
    docs = [_Doc("d1", content)]
    segments = [
        Segment(
            doc_id="d1",
            index=0,
            start_char=0,
            end_char=5,
            speaker="Alex",
            text="Alex:",
        )
    ]

    app, status = resolve_and_anchor(
        "values autonomy",
        docs,
        code_id="C1",
        codebook_version=1,
        confidence=0.8,
        segments=segments,
    )

    assert status is MatchStatus.UNIQUE
    assert app is not None
    assert app.speaker is None
