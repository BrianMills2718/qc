"""Security regression tests for the MCP export surface.

The agent-driven MCP export tools accept a caller-supplied ``output_file``.
Without confinement, a caller could write project JSON to an arbitrary path
(e.g. "/home/brian/.bashrc" or "../../etc/cron.d/x"). ``_confine_export_path``
discards directory components and sanitizes the basename into a dedicated
EXPORTS_DIR. These tests verify the confinement holds for traversal payloads.
"""

from pathlib import Path

import pytest

import qc_mcp_server as mcp_server


@pytest.fixture
def exports_dir(tmp_path, monkeypatch):
    """Point the module-level EXPORTS_DIR at a temp directory."""
    sandbox = (tmp_path / "exports").resolve()
    monkeypatch.setattr(mcp_server, "EXPORTS_DIR", sandbox)
    return sandbox


@pytest.mark.parametrize(
    "payload, expected_name",
    [
        ("../../etc/passwd", "passwd"),
        ("/home/brian/.bashrc", "bashrc"),
        ("../../../etc/cron.d/x", "x"),
        ("normal_report.md", "normal_report.md"),
        ("weird;name|with*chars.json", "weird_name_with_chars.json"),
    ],
)
def test_confine_export_strips_directories_and_sanitizes(exports_dir, payload, expected_name):
    result = Path(mcp_server._confine_export_path(payload, "default.json"))
    assert result.parent == exports_dir, f"{payload!r} escaped the exports sandbox"
    assert result.name == expected_name


def test_confine_export_uses_default_when_none(exports_dir):
    result = Path(mcp_server._confine_export_path(None, "project.json"))
    assert result.parent == exports_dir
    assert result.name == "project.json"


def test_confine_export_blank_name_falls_back_to_default(exports_dir):
    # A name that sanitizes/strips to empty must fall back, not produce the dir itself.
    result = Path(mcp_server._confine_export_path("...", "fallback.json"))
    assert result.parent == exports_dir
    assert result.name == "fallback.json"


def test_confine_export_manifest_stays_in_exports_dir(exports_dir):
    result = Path(mcp_server._manifest_path_for_export("/tmp/unsafe/report.md"))
    assert result.parent == exports_dir
    assert result.name == "report.manifest.json"
