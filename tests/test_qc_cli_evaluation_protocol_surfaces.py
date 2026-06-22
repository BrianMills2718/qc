"""Tests for top-level qc_cli evaluation protocol/preflight wrappers."""

import sys

import pytest

import qc_cli
from scripts import (
    preflight_confidence_calibration_protocol,
    preflight_d4_codebook_quality_protocol,
    preflight_d6_bias_protocol,
    preflight_d8_gt_fidelity_protocol,
    preflight_d9_interpretive_preference_protocol,
    validate_confidence_calibration_protocol,
    validate_d4_codebook_quality_protocol,
    validate_d6_bias_protocol,
    validate_d8_gt_fidelity_protocol,
    validate_d9_interpretive_preference_protocol,
)


@pytest.mark.parametrize(
    ("script_module", "cli_argv", "expected_argv"),
    [
        (
            validate_d4_codebook_quality_protocol,
            ["validate-d4-codebook-quality-protocol", "d4_protocol.json"],
            ["d4_protocol.json"],
        ),
        (
            preflight_d4_codebook_quality_protocol,
            [
                "d4-codebook-quality-preflight",
                "d4_protocol.json",
                "--quality-file",
                "quality.json",
            ],
            ["d4_protocol.json", "--quality-file", "quality.json"],
        ),
        (
            validate_d6_bias_protocol,
            ["validate-d6-bias-protocol", "d6_protocol.json"],
            ["d6_protocol.json"],
        ),
        (
            preflight_d6_bias_protocol,
            [
                "d6-bias-preflight",
                "d6_protocol.json",
                "--stratified-file",
                "stratified.json",
                "--counterfactual-file",
                "counterfactual.json",
            ],
            [
                "d6_protocol.json",
                "--stratified-file",
                "stratified.json",
                "--counterfactual-file",
                "counterfactual.json",
            ],
        ),
        (
            validate_d8_gt_fidelity_protocol,
            ["validate-d8-gt-fidelity-protocol", "d8_protocol.json"],
            ["d8_protocol.json"],
        ),
        (
            preflight_d8_gt_fidelity_protocol,
            [
                "d8-gt-fidelity-preflight",
                "d8_protocol.json",
                "--gt-fidelity-file",
                "gt_fidelity.json",
            ],
            ["d8_protocol.json", "--gt-fidelity-file", "gt_fidelity.json"],
        ),
        (
            validate_d9_interpretive_preference_protocol,
            ["validate-d9-interpretive-preference-protocol", "d9_protocol.json"],
            ["d9_protocol.json"],
        ),
        (
            preflight_d9_interpretive_preference_protocol,
            [
                "d9-interpretive-preference-preflight",
                "d9_protocol.json",
                "--preference-file",
                "preference.json",
            ],
            ["d9_protocol.json", "--preference-file", "preference.json"],
        ),
        (
            validate_confidence_calibration_protocol,
            ["validate-confidence-calibration-protocol", "confidence_protocol.json"],
            ["confidence_protocol.json"],
        ),
        (
            preflight_confidence_calibration_protocol,
            [
                "confidence-calibration-preflight",
                "confidence_protocol.json",
                "--calibration-file",
                "calibration.json",
            ],
            ["confidence_protocol.json", "--calibration-file", "calibration.json"],
        ),
    ],
)
def test_qc_cli_evaluation_protocol_surface_forwards_args(
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
