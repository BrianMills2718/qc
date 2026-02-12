"""
Tests for the QDPX (REFI-QDA) export.
"""

import zipfile
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest

from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.schemas.domain import (
    AnalysisMemo,
    Code,
    CodeApplication,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)

NS = "urn:QDA-XML:project:1.0"


@pytest.fixture
def sample_state():
    """A minimal ProjectState for export testing."""
    doc = Document(id="d1", name="interview1.txt", content="The sky is blue and the grass is green.")
    codes = [
        Code(id="C1", name="Colour", description="References to colour", mention_count=2, confidence=0.9),
        Code(id="C1a", name="Blue", description="Blue things", parent_id="C1", level=1, mention_count=1, confidence=0.85),
        Code(id="C2", name="Nature", description="Nature references", mention_count=1, confidence=0.7),
    ]
    apps = [
        CodeApplication(id="A1", code_id="C1a", doc_id="d1", quote_text="The sky is blue", confidence=0.85),
        CodeApplication(id="A2", code_id="C2", doc_id="d1", quote_text="the grass is green", confidence=0.7),
    ]
    return ProjectState(
        name="Test Export",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=codes),
        code_applications=apps,
        memos=[
            AnalysisMemo(id="M1", title="Observation", memo_type="theoretical", content="Colours are recurring."),
        ],
    )


class TestQdpxExport:
    def test_creates_valid_zip(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        assert out.exists()
        assert zipfile.is_zipfile(out)

    def test_contains_project_qde_and_sources(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            assert "project.qde" in names
            assert any(n.startswith("sources/") and n.endswith(".txt") for n in names)

    def test_source_content_matches(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        with zipfile.ZipFile(out) as zf:
            txt = zf.read("sources/d1.txt").decode("utf-8")
            assert txt == "The sky is blue and the grass is green."

    def test_xml_root_element(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        assert root.tag == f"{{{NS}}}Project"
        assert root.get("name") == "Test Export"

    def test_codebook_hierarchy(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        codes_el = root.find(f".//{{{NS}}}Codes")
        top_codes = codes_el.findall(f"{{{NS}}}Code")
        # C1 (top-level) and C2 (top-level); C1a is child of C1
        top_names = {c.get("name") for c in top_codes}
        assert "Colour" in top_names
        assert "Nature" in top_names
        assert "Blue" not in top_names  # should be nested under Colour

        # Find child
        colour_code = [c for c in top_codes if c.get("name") == "Colour"][0]
        children = colour_code.findall(f"{{{NS}}}Code")
        assert len(children) == 1
        assert children[0].get("name") == "Blue"

    def test_code_applications_as_selections(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        source = root.find(f".//{{{NS}}}TextSource")
        selections = source.findall(f"{{{NS}}}PlainTextSelection")
        assert len(selections) == 2

        # Check positions
        s1 = [s for s in selections if s.get("guid") == "A1"][0]
        assert s1.get("startPosition") == "0"
        assert s1.get("endPosition") == "15"  # len("The sky is blue")

        # Check CodeRef
        code_ref = s1.find(f".//{{{NS}}}CodeRef")
        assert code_ref.get("targetGUID") == "C1a"

    def test_memos_exported_as_notes(self, sample_state, tmp_path):
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        notes = root.findall(f".//{{{NS}}}Note")
        assert len(notes) == 1
        assert notes[0].get("name") == "Observation"

    def test_no_memos_no_notes_element(self, sample_state, tmp_path):
        sample_state.memos = []
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        notes = root.find(f"{{{NS}}}Notes")
        assert notes is None

    def test_missing_quote_in_doc_skipped(self, sample_state, tmp_path):
        """Applications whose quote_text isn't found in the doc are skipped."""
        sample_state.code_applications.append(
            CodeApplication(id="A3", code_id="C1", doc_id="d1", quote_text="NOT IN DOCUMENT")
        )
        out = tmp_path / "test.qdpx"
        ProjectExporter().export_qdpx(sample_state, str(out))
        root = _parse_qde(out)
        source = root.find(f".//{{{NS}}}TextSource")
        selections = source.findall(f"{{{NS}}}PlainTextSelection")
        assert len(selections) == 2  # A3 skipped

    def test_empty_project_exports(self, tmp_path):
        """Even a project with no codes/docs should produce a valid QDPX."""
        state = ProjectState(name="Empty")
        out = tmp_path / "empty.qdpx"
        ProjectExporter().export_qdpx(state, str(out))
        assert zipfile.is_zipfile(out)
        root = _parse_qde(out)
        assert root.get("name") == "Empty"

    def test_default_output_filename(self, sample_state, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        path = ProjectExporter().export_qdpx(sample_state)
        assert Path(path).name == "Test Export.qdpx"
        assert zipfile.is_zipfile(path)

    def test_multi_document(self, tmp_path):
        docs = [
            Document(id="d1", name="int1.txt", content="Alpha bravo charlie"),
            Document(id="d2", name="int2.txt", content="Delta echo foxtrot"),
        ]
        apps = [
            CodeApplication(id="A1", code_id="C1", doc_id="d1", quote_text="Alpha bravo"),
            CodeApplication(id="A2", code_id="C1", doc_id="d2", quote_text="echo foxtrot"),
        ]
        state = ProjectState(
            name="Multi",
            corpus=Corpus(documents=docs),
            codebook=Codebook(codes=[Code(id="C1", name="Theme")]),
            code_applications=apps,
        )
        out = tmp_path / "multi.qdpx"
        ProjectExporter().export_qdpx(state, str(out))
        with zipfile.ZipFile(out) as zf:
            assert "sources/d1.txt" in zf.namelist()
            assert "sources/d2.txt" in zf.namelist()
        root = _parse_qde(out)
        sources = root.findall(f".//{{{NS}}}TextSource")
        assert len(sources) == 2


def _parse_qde(qdpx_path):
    """Extract and parse project.qde from a QDPX file."""
    with zipfile.ZipFile(qdpx_path) as zf:
        xml_bytes = zf.read("project.qde")
    return fromstring(xml_bytes)
