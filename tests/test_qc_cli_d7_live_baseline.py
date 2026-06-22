"""Tests for top-level qc_cli D7 live baseline command."""

import sys

import qc_cli
from scripts import run_d7_live_baseline


def test_qc_cli_run_d7_live_baseline_forwards_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_d7_live_baseline, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "run-d7-live-baseline",
            "project-123",
            "--output",
            "live_baseline.json",
            "--name",
            "live_candidate",
            "--description",
            "Live candidate selector",
            "--model",
            "fake-live-model",
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
        "live_baseline.json",
        "--name",
        "live_candidate",
        "--description",
        "Live candidate selector",
        "--model",
        "fake-live-model",
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
