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


def test_plan_status_check_is_green_and_meaningful() -> None:
    """The repo-local validator must pass on the real (consistent) plan index.

    This replaces the old delegation to the shared meta checker, which globbed
    numbered ``NN_*.md`` plans this repo doesn't use and so reported a vacuous
    green (the F1 false-green finding). The validator now checks the actual
    Active/Completed tables in ``docs/plans/CLAUDE.md``.
    """
    result = _run_script("scripts/sync_plan_status.py", "--check")

    assert result.returncode == 0, result.stderr
    assert "consistent with the Completed Plans table" in result.stdout


def test_meta_plan_status_wrapper_delegates_to_repo_local_checker() -> None:
    """The legacy meta entrypoint must not return the old vacuous empty list."""
    result = _run_script("scripts/meta/sync_plan_status.py", "--list")

    assert result.returncode == 0, result.stderr
    assert "completed/INV1_OVERNIGHT_SPRINT.md" in result.stdout
    assert "completed/INV8_SEGMENT_UNIVERSE.md" in result.stdout
    assert "completed/IRR_APPLICATION_LEVEL.md" in result.stdout
    assert "Plan Statuses:" not in result.stdout


def test_plan_status_check_fails_on_orphan_record() -> None:
    """An unlisted record file under completed/ must turn the check red.

    Proves the green is non-vacuous: a record on disk with no Completed-table
    row is an inconsistency the validator catches.
    """
    orphan = REPO_ROOT / "docs/plans/completed/_orphan_wrapper_test.md"
    orphan.write_text("# orphan\n", encoding="utf-8")
    try:
        result = _run_script("scripts/sync_plan_status.py", "--check")
    finally:
        orphan.unlink()

    assert result.returncode == 1, result.stdout
    assert "_orphan_wrapper_test.md" in result.stdout
