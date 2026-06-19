"""Ingestion tests against real binary document fixtures.

The advertised .docx/.pdf/.rtf support was previously only smoke-tested by
importing the parser libraries; no test parsed an actual binary file, so a
broken extraction path (e.g. the divergent PyPDF2 vs pypdf code paths) could
ship undetected. These tests build real fixtures on the fly and run them
through the single canonical reader, ``read_file_content``.
"""

import pytest

from qc_clean.core.cli.utils.file_handler import read_file_content


def test_read_txt(tmp_path):
    f = tmp_path / "interview.txt"
    f.write_text("Speaker A: I trust the process.\n", encoding="utf-8")
    assert "trust the process" in read_file_content(str(f))


def test_read_docx(tmp_path):
    docx = pytest.importorskip("docx")
    path = tmp_path / "interview.docx"
    doc = docx.Document()
    doc.add_paragraph("Speaker A: The team collaborated well.")
    doc.add_paragraph("Speaker B: I felt supported throughout.")
    doc.save(str(path))

    content = read_file_content(str(path))
    assert "collaborated well" in content
    assert "felt supported" in content


def test_read_pdf(tmp_path):
    # Build a minimal real PDF with pypdf (no external fixture needed).
    pytest.importorskip("pypdf")
    reportlab = pytest.importorskip("reportlab.pdfgen.canvas", reason="reportlab not installed")

    path = tmp_path / "interview.pdf"
    c = reportlab.Canvas(str(path))
    c.drawString(72, 720, "Speaker A: Coding fidelity matters.")
    c.save()

    content = read_file_content(str(path))
    assert "Coding fidelity" in content


def test_read_rtf(tmp_path):
    pytest.importorskip("striprtf")
    path = tmp_path / "interview.rtf"
    path.write_text(
        r"{\rtf1\ansi Speaker A: Saturation was reached early.\par}",
        encoding="utf-8",
    )
    content = read_file_content(str(path))
    assert "Saturation was reached" in content
