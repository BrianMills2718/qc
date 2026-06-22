"""Tests for top-level qc_cli adjudication validation/preflight wrappers."""

import sys

import qc_cli
from scripts import (
    preflight_adjudication_protocol_sample,
    preflight_adjudication_responses,
    validate_adjudication_protocol,
    validate_adjudication_responses,
)


def test_qc_cli_validate_adjudication_protocol_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(validate_adjudication_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["qc_cli.py", "validate-adjudication-protocol", "protocol.json"],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["protocol.json"]


def test_qc_cli_adjudication_protocol_preflight_forwards_paths(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(preflight_adjudication_protocol_sample, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "adjudication-protocol-preflight",
            "protocol.json",
            "sample.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["protocol.json", "sample.json"]


def test_qc_cli_validate_adjudication_responses_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(validate_adjudication_responses, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["qc_cli.py", "validate-adjudication-responses", "responses.json"],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["responses.json"]


def test_qc_cli_adjudication_response_preflight_forwards_paths(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(preflight_adjudication_responses, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "adjudication-response-preflight",
            "protocol.json",
            "sample.json",
            "responses.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["protocol.json", "sample.json", "responses.json"]
