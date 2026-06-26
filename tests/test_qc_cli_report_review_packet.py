"""Tests for top-level qc_cli report review packet command."""

import sys

import qc_cli
from scripts import write_report_review_packet


def test_qc_cli_write_report_review_packet_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(write_report_review_packet, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "write-report-review-packet",
            "reviewer_report.md",
            "report_baselines.json",
            "--output",
            "report_review_packet.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "reviewer_report.md",
        "report_baselines.json",
        "--output",
        "report_review_packet.json",
    ]
