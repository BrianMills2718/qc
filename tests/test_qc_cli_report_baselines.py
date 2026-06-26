"""Tests for top-level qc_cli report baseline command."""

import sys

import qc_cli
from scripts import run_report_baselines


def test_qc_cli_run_report_baselines_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_report_baselines, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-report-baselines",
            "project-123",
            "--projects-dir",
            "portable_projects",
            "--output",
            "report_baselines.json",
            "--mode",
            "direct_report",
            "--mode",
            "qa_report",
            "--model",
            "fair-baseline-model",
            "--max-chars-per-doc",
            "1800",
            "--trace-id",
            "trace-report",
            "--max-budget",
            "1.25",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-123",
        "--projects-dir",
        "portable_projects",
        "--output",
        "report_baselines.json",
        "--model",
        "fair-baseline-model",
        "--max-chars-per-doc",
        "1800",
        "--trace-id",
        "trace-report",
        "--max-budget",
        "1.25",
        "--mode",
        "direct_report",
        "--mode",
        "qa_report",
    ]
