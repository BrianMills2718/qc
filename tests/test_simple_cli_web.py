"""
Smoke tests for the legacy Flask CLI wrapper.
"""

from unittest.mock import Mock, patch

import pytest

import simple_cli_web


def test_run_cli_command_uses_argv_without_shell():
    """CLI arguments should be passed as argv, not concatenated into a shell string."""
    completed = Mock(returncode=0, stdout="ok", stderr="")

    with patch("simple_cli_web.subprocess.run", return_value=completed) as mock_run:
        result = simple_cli_web.run_cli_command(["--help; touch /tmp/should-not-run"])

    assert result == {"returncode": 0, "stdout": "ok", "stderr": ""}
    args, kwargs = mock_run.call_args
    assert args[0] == [
        simple_cli_web.sys.executable,
        "qc_cli.py",
        "--help; touch /tmp/should-not-run",
    ]
    assert kwargs["cwd"] == simple_cli_web.PROJECT_ROOT
    assert "shell" not in kwargs


def test_resolve_uploaded_file_rejects_path_traversal(tmp_path, monkeypatch):
    """Client-supplied upload names must stay inside the upload directory."""
    monkeypatch.setattr(simple_cli_web, "UPLOAD_FOLDER", str(tmp_path))
    (tmp_path / "interview.txt").write_text("ok", encoding="utf-8")

    resolved = simple_cli_web.resolve_uploaded_file("interview.txt")
    assert resolved == (tmp_path / "interview.txt").resolve()

    for filename in ("../interview.txt", "/tmp/interview.txt", "nested/interview.txt"):
        with pytest.raises(ValueError):
            simple_cli_web.resolve_uploaded_file(filename)


def test_start_analysis_rejects_untrusted_file_paths(monkeypatch, tmp_path):
    """The JSON start endpoint should not read arbitrary filesystem paths."""
    monkeypatch.setattr(simple_cli_web, "UPLOAD_FOLDER", str(tmp_path))
    client = simple_cli_web.app.test_client()

    response = client.post(
        "/start_analysis",
        json={"files": ["../secret.txt"], "format": "json", "session_id": "test"},
    )

    assert response.status_code == 200
    assert "Invalid uploaded filename" in response.get_json()["error"]
