"""
Smoke tests for the legacy Flask CLI wrapper.
"""

from unittest.mock import Mock, patch

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
