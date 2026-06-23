"""Tests for top-level qc_cli theoretical-sampling wrappers."""

import sys

import qc_cli
from scripts import (
    export_theoretical_sampling_candidates,
    export_theoretical_sampling_results,
    preflight_theoretical_sampling_protocol,
    validate_theoretical_sampling_protocol,
)


def test_qc_cli_validate_theoretical_sampling_protocol_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(validate_theoretical_sampling_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        ["qc_cli.py", "validate-theoretical-sampling-protocol", "protocol.json"],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["protocol.json"]


def test_qc_cli_theoretical_sampling_preflight_forwards_args(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(preflight_theoretical_sampling_protocol, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "theoretical-sampling-preflight",
            "protocol.json",
            "--candidates-file",
            "candidates.json",
            "--results-file",
            "results.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "protocol.json",
        "--candidates-file",
        "candidates.json",
        "--results-file",
        "results.json",
    ]


def test_qc_cli_export_theoretical_sampling_candidates_forwards_args(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(export_theoretical_sampling_candidates, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "export-theoretical-sampling-candidates",
            "project-alpha",
            "--protocol",
            "protocol.json",
            "--output",
            "candidates.json",
            "--candidate-name",
            "doc-1",
            "--candidate-name",
            "doc-2",
            "--max-suggestions",
            "7",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-alpha",
        "--protocol",
        "protocol.json",
        "--output",
        "candidates.json",
        "--candidate-name",
        "doc-1",
        "--candidate-name",
        "doc-2",
        "--max-suggestions",
        "7",
    ]


def test_qc_cli_export_theoretical_sampling_candidates_forwards_projects_dir(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(export_theoretical_sampling_candidates, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "export-theoretical-sampling-candidates",
            "project-alpha",
            "--projects-dir",
            "projects",
            "--protocol",
            "protocol.json",
            "--output",
            "candidates.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-alpha",
        "--projects-dir",
        "projects",
        "--protocol",
        "protocol.json",
        "--output",
        "candidates.json",
    ]


def test_qc_cli_export_theoretical_sampling_results_forwards_args(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(export_theoretical_sampling_results, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "export-theoretical-sampling-results",
            "protocol.json",
            "--candidates-file",
            "candidates.json",
            "--selected-candidate-id",
            "candidate-1",
            "--selected-candidate-id",
            "candidate-2",
            "--success-criterion-met",
            "property coverage improved",
            "--success-criterion-met",
            "dimension coverage improved",
            "--stopped-by-rule",
            "--output",
            "results.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "protocol.json",
        "--candidates-file",
        "candidates.json",
        "--selected-candidate-id",
        "candidate-1",
        "--selected-candidate-id",
        "candidate-2",
        "--success-criterion-met",
        "property coverage improved",
        "--success-criterion-met",
        "dimension coverage improved",
        "--stopped-by-rule",
        "--output",
        "results.json",
    ]
