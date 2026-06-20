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
