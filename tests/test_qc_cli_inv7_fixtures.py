"""Tests for top-level qc_cli INV-7 fixture commands."""

import sys

import qc_cli
from scripts import (
    preflight_inv7_live_package,
    run_inv7_fixtures,
    run_inv7_live_fixtures,
    validate_inv7_live_protocol,
    validate_inv7_prompt_injection_package,
)


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


def test_qc_cli_validate_inv7_package_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 2

    monkeypatch.setattr(validate_inv7_prompt_injection_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-inv7-package",
            "inv7.json",
        ],
    )

    assert qc_cli.main() == 2
    assert captured["argv"] == ["inv7.json"]


def test_qc_cli_validate_inv7_live_protocol_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 3

    monkeypatch.setattr(validate_inv7_live_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-inv7-live-protocol",
            "inv7_protocol.json",
        ],
    )

    assert qc_cli.main() == 3
    assert captured["argv"] == ["inv7_protocol.json"]


def test_qc_cli_inv7_live_preflight_forwards_paths(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 4

    monkeypatch.setattr(preflight_inv7_live_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "inv7-live-preflight",
            "inv7_protocol.json",
            "inv7_live.json",
        ],
    )

    assert qc_cli.main() == 4
    assert captured["argv"] == ["inv7_protocol.json", "inv7_live.json"]
