"""Tests for top-level qc_cli sampling-frame adequacy wrappers."""

import sys

import qc_cli
from scripts import (
    preflight_sampling_frame_adequacy_protocol,
    validate_sampling_frame_adequacy_protocol,
)


def test_qc_cli_validate_sampling_frame_adequacy_protocol_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(validate_sampling_frame_adequacy_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["qc_cli.py", "validate-sampling-frame-adequacy-protocol", "protocol.json"],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["protocol.json"]


def test_qc_cli_sampling_frame_adequacy_preflight_forwards_args(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(preflight_sampling_frame_adequacy_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "sampling-frame-adequacy-preflight",
            "protocol.json",
            "--adequacy-file",
            "adequacy.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "protocol.json",
        "--adequacy-file",
        "adequacy.json",
    ]
