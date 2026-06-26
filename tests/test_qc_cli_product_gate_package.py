"""Tests for top-level qc_cli product-gate package command."""

import sys

import qc_cli
from scripts import write_product_gate_package


def test_qc_cli_write_product_gate_package_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(write_product_gate_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "write-product-gate-package",
            "project-1",
            "--reviewer-report",
            "reviewer_report.md",
            "--audit-report",
            "report.md",
            "--baseline-package",
            "report_baselines.json",
            "--baseline-comparison",
            "report_baseline_comparison.json",
            "--review-packet",
            "report_review_packet.json",
            "--review-response",
            "report_review_response.json",
            "--export-manifest",
            "manifest.json",
            "--output",
            "product_gate_package.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-1",
        "--reviewer-report",
        "reviewer_report.md",
        "--audit-report",
        "report.md",
        "--baseline-package",
        "report_baselines.json",
        "--baseline-comparison",
        "report_baseline_comparison.json",
        "--review-packet",
        "report_review_packet.json",
        "--review-response",
        "report_review_response.json",
        "--export-manifest",
        "manifest.json",
        "--output",
        "product_gate_package.json",
    ]
