"""Tests for top-level qc_cli D7 retrieval commands."""

import sys

import qc_cli
from scripts import (
    compare_d7_retrieval,
    run_d7_comparison_package,
    run_d7_retrieval,
    validate_d3_baseline_package,
    validate_d3_gold_set,
    validate_d7_baseline_package,
    validate_d7_gold_set,
    verify_d7_comparison_artifact,
    write_d7_comparison_package,
)


def test_qc_cli_run_d7_retrieval_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_d7_retrieval, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-d7-retrieval",
            "project-123",
            "--output",
            "predictions.json",
            "--name",
            "embedding_candidate",
            "--description",
            "Hybrid retrieval export",
            "--max-targets",
            "12",
            "--candidates-per-claim",
            "7",
            "--retrieval-mode",
            "embedding_hybrid",
            "--bm25-k1",
            "1.4",
            "--bm25-b",
            "0.6",
            "--contrary-cue-weight",
            "1.8",
            "--expanded-term-weight",
            "0.7",
            "--embedding-model",
            "text-embedding-3-small",
            "--embedding-dimensions",
            "256",
            "--semantic-weight",
            "1.2",
            "--min-semantic-similarity",
            "0.15",
            "--trace-id",
            "trace-xyz",
            "--max-budget",
            "2.5",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-123",
        "--output",
        "predictions.json",
        "--name",
        "embedding_candidate",
        "--description",
        "Hybrid retrieval export",
        "--max-targets",
        "12",
        "--candidates-per-claim",
        "7",
        "--retrieval-mode",
        "embedding_hybrid",
        "--bm25-k1",
        "1.4",
        "--bm25-b",
        "0.6",
        "--contrary-cue-weight",
        "1.8",
        "--expanded-term-weight",
        "0.7",
        "--embedding-model",
        "text-embedding-3-small",
        "--embedding-dimensions",
        "256",
        "--semantic-weight",
        "1.2",
        "--min-semantic-similarity",
        "0.15",
        "--trace-id",
        "trace-xyz",
        "--max-budget",
        "2.5",
    ]


def test_qc_cli_compare_d7_retrieval_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(compare_d7_retrieval, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "compare-d7-retrieval",
            "project-123",
            "--gold-file",
            "d7_gold.json",
            "--predictions-file",
            "lexical.json",
            "--predictions-file",
            "embedding.json",
            "--output",
            "comparison.json",
            "--protocol-package",
            "protocol.json",
            "--artifact-dir",
            "benchmark_results",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-123",
        "--gold-file",
        "d7_gold.json",
        "--predictions-file",
        "lexical.json",
        "--predictions-file",
        "embedding.json",
        "--output",
        "comparison.json",
        "--protocol-package",
        "protocol.json",
        "--artifact-dir",
        "benchmark_results",
    ]


def test_qc_cli_verify_d7_comparison_artifact_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(verify_d7_comparison_artifact, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "verify-d7-comparison-artifact",
            "benchmark_results/run/manifest.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["benchmark_results/run/manifest.json"]


def test_qc_cli_compare_d7_package_forwards_manifest_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_d7_comparison_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "compare-d7-package",
            "d7_comparison_package.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["d7_comparison_package.json"]


def test_qc_cli_write_d7_comparison_package_forwards_args(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(write_d7_comparison_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "write-d7-comparison-package",
            "project-d7",
            "--output",
            "d7_comparison_package.json",
            "--gold-file",
            "gold.json",
            "--predictions-file",
            "lexical.json",
            "--predictions-file",
            "live.json",
            "--protocol-package",
            "protocol.json",
            "--comparison-output",
            "comparison.json",
            "--artifact-dir",
            "benchmark_results",
            "--verify-artifact",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "project-d7",
        "--output",
        "d7_comparison_package.json",
        "--gold-file",
        "gold.json",
        "--predictions-file",
        "lexical.json",
        "--predictions-file",
        "live.json",
        "--protocol-package",
        "protocol.json",
        "--comparison-output",
        "comparison.json",
        "--artifact-dir",
        "benchmark_results",
        "--verify-artifact",
    ]


def test_qc_cli_validate_d7_baseline_package_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 7

    monkeypatch.setattr(validate_d7_baseline_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-d7-baseline-package",
            "baseline.json",
        ],
    )

    assert qc_cli.main() == 7
    assert captured["argv"] == ["baseline.json"]


def test_qc_cli_validate_d3_baseline_package_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 8

    monkeypatch.setattr(validate_d3_baseline_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-d3-baseline-package",
            "d3_baseline.json",
        ],
    )

    assert qc_cli.main() == 8
    assert captured["argv"] == ["d3_baseline.json"]


def test_qc_cli_validate_d3_gold_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 3

    monkeypatch.setattr(validate_d3_gold_set, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-d3-gold",
            "d3_gold.json",
        ],
    )

    assert qc_cli.main() == 3
    assert captured["argv"] == ["d3_gold.json"]


def test_qc_cli_validate_d7_gold_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 4

    monkeypatch.setattr(validate_d7_gold_set, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "validate-d7-gold",
            "d7_gold.json",
        ],
    )

    assert qc_cli.main() == 4
    assert captured["argv"] == ["d7_gold.json"]
