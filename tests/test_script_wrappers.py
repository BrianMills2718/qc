"""Regression tests for public maintenance script wrappers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_doc_coupling_wrapper_delegates_to_canonical_script() -> None:
    """The public wrapper should keep the documented entrypoint working."""
    result = _run_script("scripts/check_doc_coupling.py", "--validate-config")

    assert result.returncode == 0, result.stderr
    assert "Config validation passed." in result.stdout


def test_plan_status_wrapper_delegates_to_canonical_script() -> None:
    """The public wrapper should keep the documented entrypoint working."""
    result = _run_script("scripts/sync_plan_status.py", "--check")

    assert result.returncode == 0, result.stderr
    assert "All plan statuses are consistent." in result.stdout
