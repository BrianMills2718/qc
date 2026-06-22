"""Tests for top-level qc_cli export-audit wrappers."""

import sys

import pytest

import qc_cli
from scripts import (
    export_publish_preflight,
    mirror_export_audit_event_log_db,
    verify_export_audit_event_db,
    verify_export_audit_event_log,
    verify_export_audit_manifest,
    write_export_audit_manifest,
)


@pytest.mark.parametrize(
    ("script_module", "cli_argv", "expected_argv"),
    [
        (
            write_export_audit_manifest,
            [
                "export-audit-manifest",
                "project-alpha",
                "--format",
                "markdown",
                "--artifact",
                "report.md",
                "--artifact",
                "claims.csv",
                "--output",
                "manifest.json",
                "--base-dir",
                "exports",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
            [
                "project-alpha",
                "--format",
                "markdown",
                "--artifact",
                "report.md",
                "--artifact",
                "claims.csv",
                "--output",
                "manifest.json",
                "--base-dir",
                "exports",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
        ),
        (
            verify_export_audit_manifest,
            [
                "verify-export-audit-manifest",
                "manifest.json",
                "--base-dir",
                "exports",
                "--project-id",
                "project-alpha",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
            [
                "manifest.json",
                "--base-dir",
                "exports",
                "--project-id",
                "project-alpha",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
        ),
        (
            export_publish_preflight,
            [
                "export-publish-preflight",
                "--manifest",
                "manifest.json",
                "--base-dir",
                "exports",
                "--project-id",
                "project-alpha",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
            [
                "--manifest",
                "manifest.json",
                "--base-dir",
                "exports",
                "--project-id",
                "project-alpha",
                "--projects-dir",
                "projects",
                "--audit-log",
                "events.jsonl",
                "--audit-db",
                "events.sqlite",
            ],
        ),
        (
            verify_export_audit_event_log,
            ["verify-export-audit-log", "events.jsonl"],
            ["events.jsonl"],
        ),
        (
            mirror_export_audit_event_log_db,
            ["mirror-export-audit-db", "events.jsonl", "--db", "events.sqlite"],
            ["events.jsonl", "--db", "events.sqlite"],
        ),
        (
            verify_export_audit_event_db,
            ["verify-export-audit-db", "events.sqlite"],
            ["events.sqlite"],
        ),
    ],
)
def test_qc_cli_export_audit_surface_forwards_args(
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
