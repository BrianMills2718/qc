"""Tests for top-level qc_cli governance lint wrappers."""

import sys

import pytest

import qc_cli
from scripts import check_prompt_override_registry, lint_scope_phrasing


@pytest.mark.parametrize(
    ("script_module", "cli_argv", "expected_argv"),
    [
        (
            lint_scope_phrasing,
            [
                "lint-scope-phrasing",
                "project-alpha",
                "--input-file",
                "report.md",
                "--projects-dir",
                "projects",
            ],
            [
                "project-alpha",
                "--input-file",
                "report.md",
                "--projects-dir",
                "projects",
            ],
        ),
        (
            lint_scope_phrasing,
            [
                "lint-scope-phrasing",
                "project-alpha",
                "--text",
                "participants consistently prefer remote work",
            ],
            [
                "project-alpha",
                "--text",
                "participants consistently prefer remote work",
            ],
        ),
        (
            check_prompt_override_registry,
            ["lint-prompt-overrides", "--root", "qc_clean"],
            ["--root", "qc_clean"],
        ),
    ],
)
def test_qc_cli_governance_lint_surface_forwards_args(
    monkeypatch,
    script_module,
    cli_argv,
    expected_argv,
):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(script_module, "main", fake_main)
    monkeypatch.setattr(sys, "argv", ["qc_cli.py", *cli_argv])

    assert qc_cli.main() == 0
    assert captured["argv"] == expected_argv
