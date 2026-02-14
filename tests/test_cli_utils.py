"""
Tests for CLI utility modules.

Covers:
- file_handler: discover_files, validate_file_formats, read_file_content,
  get_file_info, format_file_size
- formatters: json_formatter, table_formatter, human_formatter
- progress: SimpleProgressBar, print_status, print_separator
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from qc_clean.core.cli.utils.file_handler import (
    SUPPORTED_EXTENSIONS,
    discover_files,
    format_file_size,
    get_file_info,
    read_file_content,
    validate_file_formats,
)
from qc_clean.core.cli.formatters.json_formatter import (
    format_compact_json,
    format_json_output,
)
from qc_clean.core.cli.formatters.table_formatter import (
    format_simple_table,
    format_table_output,
)
from qc_clean.core.cli.formatters.human_formatter import (
    format_analysis_results,
    format_status_info,
)
from qc_clean.core.cli.utils.progress import (
    SimpleProgressBar,
    print_separator,
    print_status,
)


# ---------------------------------------------------------------------------
# file_handler tests
# ---------------------------------------------------------------------------

class TestDiscoverFiles:
    def test_discovers_txt_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        (tmp_path / "c.py").write_text("not supported")
        result = discover_files(str(tmp_path))
        assert len(result) == 2
        assert all(f.endswith(".txt") for f in result)

    def test_discovers_nested_files(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "interview.txt").write_text("content")
        result = discover_files(str(tmp_path))
        assert len(result) == 1

    def test_discovers_docx_extension(self, tmp_path):
        (tmp_path / "doc.docx").write_bytes(b"fake docx")
        result = discover_files(str(tmp_path))
        assert len(result) == 1

    def test_empty_directory(self, tmp_path):
        result = discover_files(str(tmp_path))
        assert result == []

    def test_nonexistent_directory_raises(self):
        with pytest.raises(Exception, match="does not exist"):
            discover_files("/nonexistent/path/xyz")

    def test_file_path_raises(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("text")
        with pytest.raises(Exception, match="not a directory"):
            discover_files(str(f))

    def test_results_sorted(self, tmp_path):
        (tmp_path / "z.txt").write_text("z")
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "m.txt").write_text("m")
        result = discover_files(str(tmp_path))
        assert result == sorted(result)


class TestValidateFileFormats:
    def test_validates_txt_files(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("content")
        result = validate_file_formats([str(f)])
        assert len(result) == 1

    def test_empty_list_raises(self):
        with pytest.raises(Exception, match="No files provided"):
            validate_file_formats([])

    def test_nonexistent_file_raises(self):
        with pytest.raises(Exception, match="does not exist"):
            validate_file_formats(["/nonexistent/file.txt"])

    def test_empty_file_raises(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        with pytest.raises(Exception, match="empty"):
            validate_file_formats([str(f)])

    def test_unsupported_extension_raises(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c")
        with pytest.raises(Exception, match="Unsupported"):
            validate_file_formats([str(f)])

    def test_multiple_valid_files(self, tmp_path):
        files = []
        for name in ["a.txt", "b.txt"]:
            f = tmp_path / name
            f.write_text("content")
            files.append(str(f))
        result = validate_file_formats(files)
        assert len(result) == 2


class TestReadFileContent:
    def test_reads_utf8_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello, world!")
        assert read_file_content(str(f)) == "Hello, world!"

    def test_reads_unicode_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Héllo wörld")
        assert "Héllo" in read_file_content(str(f))

    def test_reads_latin1_fallback(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"caf\xe9")  # latin-1 encoded
        content = read_file_content(str(f))
        assert "caf" in content


class TestGetFileInfo:
    def test_returns_info_dict(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        info = get_file_info(str(f))
        assert info["name"] == "test.txt"
        assert info["extension"] == ".txt"
        assert info["size"] == 5
        assert info["readable"] is True

    def test_nonexistent_file(self):
        info = get_file_info("/nonexistent/file.txt")
        assert "error" in info


class TestFormatFileSize:
    def test_bytes(self):
        assert format_file_size(500) == "500 B"

    def test_kilobytes(self):
        assert "KB" in format_file_size(2048)

    def test_megabytes(self):
        assert "MB" in format_file_size(5 * 1024 * 1024)

    def test_gigabytes(self):
        assert "GB" in format_file_size(2 * 1024 * 1024 * 1024)

    def test_zero(self):
        assert format_file_size(0) == "0 B"


class TestSupportedExtensions:
    def test_txt_supported(self):
        assert ".txt" in SUPPORTED_EXTENSIONS

    def test_docx_supported(self):
        assert ".docx" in SUPPORTED_EXTENSIONS

    def test_pdf_supported(self):
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_rtf_supported(self):
        assert ".rtf" in SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# json_formatter tests
# ---------------------------------------------------------------------------

class TestJsonFormatter:
    def test_format_json_output(self):
        data = {"key": "value", "count": 42}
        result = format_json_output(data)
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["count"] == 42

    def test_format_json_sorted_keys(self):
        data = {"z": 1, "a": 2}
        result = format_json_output(data)
        # 'a' should come before 'z' in sorted output
        assert result.index('"a"') < result.index('"z"')

    def test_format_json_non_serializable(self):
        data = {"func": set([1, 2, 3])}
        result = format_json_output(data)
        parsed = json.loads(result)
        assert "error" in parsed

    def test_format_compact_json(self):
        data = {"key": "value"}
        result = format_compact_json(data)
        assert " " not in result  # compact, no spaces
        assert json.loads(result)["key"] == "value"

    def test_format_compact_non_serializable(self):
        data = {"func": object()}
        result = format_compact_json(data)
        parsed = json.loads(result)
        assert "error" in parsed


# ---------------------------------------------------------------------------
# table_formatter tests
# ---------------------------------------------------------------------------

class TestTableFormatter:
    def test_format_table_with_codes(self):
        data = {
            "results": {
                "codes_identified": [
                    {"code": "AI Usage", "mention_count": 5, "confidence": 0.8},
                    {"code": "Privacy", "mention_count": 3, "confidence": 0.6},
                ],
            }
        }
        result = format_table_output(data)
        assert "AI Usage" in result
        assert "Privacy" in result
        assert "CODES" in result

    def test_format_table_empty(self):
        result = format_table_output({})
        assert "No data" in result

    def test_format_table_none(self):
        result = format_table_output(None)
        assert "No data" in result

    def test_format_table_with_themes(self):
        data = {
            "results": {
                "key_themes": ["Innovation", "Trust"],
            }
        }
        result = format_table_output(data)
        assert "Innovation" in result
        assert "KEY THEMES" in result

    def test_format_table_with_recommendations(self):
        data = {
            "results": {
                "recommendations": [
                    {"title": "Invest more", "priority": "high"},
                ],
            }
        }
        result = format_table_output(data)
        assert "Invest more" in result
        assert "RECOMMENDATIONS" in result

    def test_format_simple_table(self):
        result = format_simple_table(
            headers=["Name", "Count"],
            rows=[["Alice", "10"], ["Bob", "5"]],
        )
        assert "Name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_format_simple_table_empty(self):
        result = format_simple_table([], [])
        assert "No data" in result


# ---------------------------------------------------------------------------
# human_formatter tests
# ---------------------------------------------------------------------------

class TestHumanFormatter:
    def test_format_analysis_results_basic(self):
        data = {
            "job_id": "test-123",
            "status": "completed",
            "results": {
                "codes_identified": [
                    {"code": "Theme A", "mention_count": 5, "confidence": 0.8},
                ],
                "key_themes": ["Innovation"],
                "recommendations": [
                    {"title": "Do X", "priority": "high", "description": "Details"},
                ],
            },
        }
        result = format_analysis_results(data)
        assert "test-123" in result
        assert "COMPLETED" in result
        assert "Theme A" in result
        assert "Innovation" in result
        assert "Do X" in result

    def test_format_analysis_results_empty(self):
        result = format_analysis_results({})
        assert "No results" in result

    def test_format_analysis_results_none(self):
        result = format_analysis_results(None)
        assert "No results" in result

    def test_format_analysis_results_with_speakers(self):
        data = {
            "job_id": "j1",
            "status": "done",
            "results": {
                "speakers_identified": [
                    {"name": "Alice", "role": "Manager", "perspective": "Positive outlook"},
                ],
            },
        }
        result = format_analysis_results(data)
        assert "Alice" in result
        assert "Manager" in result

    def test_format_analysis_results_with_warnings(self):
        data = {
            "job_id": "j1",
            "status": "done",
            "results": {
                "data_warnings": ["Document truncated"],
            },
        }
        result = format_analysis_results(data)
        assert "Document truncated" in result
        assert "DATA WARNINGS" in result

    def test_format_status_info(self):
        data = {
            "server_status": "running",
            "available_endpoints": ["/analyze", "/status"],
        }
        result = format_status_info(data)
        assert "Running" in result
        assert "/analyze" in result

    def test_format_status_info_not_running(self):
        result = format_status_info({"server_status": "stopped"})
        assert "Not Running" in result

    def test_format_status_info_with_job(self):
        data = {
            "server_status": "running",
            "job_status": {"job_id": "abc", "status": "running", "progress": 50},
        }
        result = format_status_info(data)
        assert "abc" in result
        assert "50%" in result


# ---------------------------------------------------------------------------
# progress tests
# ---------------------------------------------------------------------------

class TestSimpleProgressBar:
    def test_initial_state(self):
        bar = SimpleProgressBar(total=10)
        assert bar.current == 0
        assert bar.total == 10

    def test_update(self):
        bar = SimpleProgressBar(total=10)
        bar.update(3)
        assert bar.current == 3

    def test_update_clamps_to_total(self):
        bar = SimpleProgressBar(total=5)
        bar.update(10)
        assert bar.current == 5

    def test_set_progress(self):
        bar = SimpleProgressBar(total=10)
        bar.set_progress(7)
        assert bar.current == 7

    def test_set_progress_clamps(self):
        bar = SimpleProgressBar(total=10)
        bar.set_progress(-5)
        assert bar.current == 0
        bar.set_progress(100)
        assert bar.current == 10

    def test_zero_total(self):
        bar = SimpleProgressBar(total=0)
        bar.display()  # should not crash


class TestPrintHelpers:
    def test_print_status(self, capsys):
        print_status("All good", "SUCCESS")
        captured = capsys.readouterr()
        assert "All good" in captured.out

    def test_print_status_error(self, capsys):
        print_status("Something failed", "ERROR")
        captured = capsys.readouterr()
        assert "Something failed" in captured.out

    def test_print_separator(self, capsys):
        print_separator("=", 20)
        captured = capsys.readouterr()
        assert "====================" in captured.out

    def test_print_separator_default(self, capsys):
        print_separator()
        captured = capsys.readouterr()
        assert len(captured.out.strip()) == 50
