"""Tests for top-level qc_cli INV-7 fixture commands."""

import sys

import qc_cli
from scripts import run_inv7_fixtures, run_inv7_live_fixtures


def test_qc_cli_run_inv7_fixtures_forwards_output(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_inv7_fixtures, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-inv7-fixtures",
            "--output",
            "inv7.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["--output", "inv7.json"]


def test_qc_cli_run_inv7_live_fixtures_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_inv7_live_fixtures, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-inv7-live-fixtures",
            "--output",
            "inv7_live.json",
            "--model",
            "fake-live-model",
            "--trace-id",
            "trace-live",
            "--max-budget",
            "0.5",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "--output",
        "inv7_live.json",
        "--model",
        "fake-live-model",
        "--trace-id",
        "trace-live",
        "--max-budget",
        "0.5",
    ]
