"""Tests for top-level qc_cli report review runner command."""

import sys

import qc_cli
from scripts import run_report_review


def test_qc_cli_run_report_review_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_report_review, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-report-review",
            "report_review_packet.json",
            "--output",
            "report_review_response.json",
            "--model",
            "fake-model",
            "--reviewer-id",
            "reviewer-1",
            "--trace-id",
            "trace-review",
            "--max-budget",
            "0.5",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "report_review_packet.json",
        "--output",
        "report_review_response.json",
        "--model",
        "fake-model",
        "--reviewer-id",
        "reviewer-1",
        "--trace-id",
        "trace-review",
        "--max-budget",
        "0.5",
    ]
