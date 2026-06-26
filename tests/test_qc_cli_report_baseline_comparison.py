"""Tests for top-level qc_cli report-baseline comparison command."""

import sys

import qc_cli
from scripts import compare_report_baselines


def test_qc_cli_compare_report_baselines_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(compare_report_baselines, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "compare-report-baselines",
            "report.md",
            "report_baselines.json",
            "--output",
            "comparison.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "report.md",
        "report_baselines.json",
        "--output",
        "comparison.json",
    ]
