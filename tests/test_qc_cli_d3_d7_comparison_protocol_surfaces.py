"""Tests for top-level qc_cli D3/D7 comparison protocol wrappers."""

import sys

import pytest

import qc_cli
from scripts import (
    preflight_d3_comparison,
    preflight_d7_comparison,
    validate_d3_comparison_protocol,
    validate_d7_comparison_protocol,
)


@pytest.mark.parametrize(
    ("script_module", "cli_argv", "expected_argv"),
    [
        (
            validate_d3_comparison_protocol,
            ["validate-d3-comparison-protocol", "d3_protocol.json"],
            ["d3_protocol.json"],
        ),
        (
            preflight_d3_comparison,
            [
                "d3-comparison-preflight",
                "d3_protocol.json",
                "d3_gold.json",
                "baseline_a.json",
                "baseline_b.json",
            ],
            [
                "d3_protocol.json",
                "d3_gold.json",
                "baseline_a.json",
                "baseline_b.json",
            ],
        ),
        (
            validate_d7_comparison_protocol,
            ["validate-d7-comparison-protocol", "d7_protocol.json"],
            ["d7_protocol.json"],
        ),
        (
            preflight_d7_comparison,
            [
                "d7-comparison-preflight",
                "d7_protocol.json",
                "d7_gold.json",
                "lexical.json",
                "embedding.json",
            ],
            [
                "d7_protocol.json",
                "d7_gold.json",
                "lexical.json",
                "embedding.json",
            ],
        ),
    ],
)
def test_qc_cli_comparison_protocol_surface_forwards_args(
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
