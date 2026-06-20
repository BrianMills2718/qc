"""Tests for char-anchored corpus segmentation (INV-8 Phase 1)."""

from qc_clean.core.segmentation import segment_corpus, segment_document
from qc_clean.schemas.domain import Document


def _roundtrips(doc, segments):
    """Every segment's offsets must recover its text from the original content."""
    return all(doc.content[s.start_char:s.end_char] == s.text for s in segments)


def test_speaker_turns_are_char_anchored():
    content = "Alex: I value autonomy.\nSam: I prefer structure and check-ins."
    doc = Document(id="d1", name="d.txt", content=content,
                   detected_speakers=["Alex", "Sam"])
    segs = segment_document(doc)
    assert len(segs) == 2
    assert _roundtrips(doc, segs)
    assert segs[0].speaker == "Alex" and "autonomy" in segs[0].text
    assert segs[1].speaker == "Sam" and "structure" in segs[1].text
    # stable, ordered ids
    assert [s.index for s in segs] == [0, 1]
    assert all(s.doc_id == "d1" for s in segs)


def test_paragraphs_when_no_speakers():
    content = "First paragraph here.\n\nSecond paragraph here.\n\nThird one."
    doc = Document(id="d2", name="d.txt", content=content)
    segs = segment_document(doc)
    assert len(segs) == 3
    assert _roundtrips(doc, segs)
    assert segs[0].text == "First paragraph here."
    assert segs[2].text == "Third one."


def test_offsets_are_into_original_with_messy_whitespace():
    content = "Alex:   leading and trailing spaces here.   \nSam: ok."
    doc = Document(id="d3", name="d.txt", content=content,
                   detected_speakers=["Alex", "Sam"])
    segs = segment_document(doc)
    assert _roundtrips(doc, segs)
    # trimmed: no leading/trailing whitespace in the segment text
    assert segs[0].text == segs[0].text.strip()
    assert segs[0].text.startswith("leading")


def test_empty_or_whitespace_doc_yields_no_segments():
    assert segment_document(Document(id="e", name="e.txt", content="   \n\n  ")) == []


def test_no_speaker_match_falls_back_to_whole_doc():
    # detected_speakers set but none appear as line-start labels -> single segment
    content = "just a blob of text with no speaker labels at line start"
    doc = Document(id="d4", name="d.txt", content=content, detected_speakers=["Zoe"])
    segs = segment_document(doc)
    assert len(segs) == 1
    assert _roundtrips(doc, segs)


def test_segment_corpus_spans_all_docs():
    docs = [
        Document(id="a", name="a.txt", content="Para one.\n\nPara two."),
        Document(id="b", name="b.txt", content="Single para."),
    ]
    segs = segment_corpus(docs)
    assert {s.doc_id for s in segs} == {"a", "b"}
    assert len(segs) == 3


# --- coverage against the segment universe (INV-8) ---------------------------

def test_compute_coverage_counts_overlapping_anchored_apps():
    from qc_clean.core.grounding import resolve_span
    from qc_clean.core.segmentation import compute_coverage
    from qc_clean.schemas.domain import (
        CodeApplication, Corpus, ProjectState,
    )

    content = "Alex: autonomy matters here.\nSam: structure matters too."
    doc = Document(id="d1", name="d.txt", content=content,
                   detected_speakers=["Alex", "Sam"])
    state = ProjectState(name="t", corpus=Corpus(documents=[doc]))
    state.segments = segment_corpus([doc])
    assert len(state.segments) == 2

    # One anchored application in Alex's segment -> 1/2 covered.
    m = resolve_span("autonomy matters", content)
    state.code_applications = [
        CodeApplication(code_id="c", doc_id="d1", quote_text="autonomy matters",
                        start_char=m.start_char, end_char=m.end_char, quote_hash=m.quote_hash),
        # an UNANCHORED app cannot contribute to coverage
        CodeApplication(code_id="c", doc_id="d1", quote_text="structure matters too"),
    ]
    rep = compute_coverage(state)
    assert rep.total_segments == 2
    assert rep.covered_segments == 1
    assert abs(rep.coverage_rate - 0.5) < 1e-9


def test_compute_coverage_zero_segments():
    from qc_clean.core.segmentation import compute_coverage
    from qc_clean.schemas.domain import Corpus, ProjectState
    state = ProjectState(name="t", corpus=Corpus(documents=[]))
    assert compute_coverage(state).coverage_rate == 0.0


def test_ingest_populates_segment_universe():
    import asyncio
    from qc_clean.core.pipeline.pipeline_engine import PipelineContext
    from qc_clean.core.pipeline.stages.ingest import IngestStage
    from qc_clean.schemas.domain import ProjectState

    state = ProjectState(name="t")
    ctx = PipelineContext(interviews=[
        {"name": "i1.txt", "content": "Alex: one.\nSam: two."},
        {"name": "i2.txt", "content": "Para A.\n\nPara B."},
    ])
    result = asyncio.run(IngestStage().execute(state, ctx))
    assert len(result.segments) == 4  # 2 turns + 2 paragraphs
    # round-trip holds against the ingested docs
    docs = {d.id: d for d in result.corpus.documents}
    assert all(docs[s.doc_id].content[s.start_char:s.end_char] == s.text
               for s in result.segments)


def test_coverage_examined_rate_from_decisions():
    """Exhaustive-mode coverage reports examined/coded from Segment.decision."""
    from qc_clean.core.segmentation import compute_coverage
    from qc_clean.schemas.domain import Corpus, ProjectState
    content = "Alex: one.\nSam: two.\nSam: three."
    doc = Document(id="d1", name="d.txt", content=content, detected_speakers=["Alex", "Sam"])
    state = ProjectState(name="t", corpus=Corpus(documents=[doc]))
    state.segments = segment_corpus([doc])
    assert len(state.segments) == 3
    state.segments[0].decision = "no_code"
    state.segments[1].decision = "coded"
    state.segments[2].decision = "coded"
    rep = compute_coverage(state)
    assert rep.examined_segments == 3
    assert rep.coded_segments == 2
    assert rep.examined_rate == 1.0
    assert rep.mode == "examined"
