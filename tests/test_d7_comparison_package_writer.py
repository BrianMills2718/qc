"""Tests for writing D7 comparison package manifests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_d7_comparison_package, write_d7_comparison_package


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64


def test_writes_manifest_for_valid_d7_comparison_inputs(tmp_path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    gold_file = _write_json(package_dir / "gold.json", _d7_gold_package())
    lexical_file = _write_json(package_dir / "lexical.json", _prediction_package("lexical"))
    live_file = _write_json(package_dir / "live.json", _prediction_package("live"))
    output = package_dir / "d7_comparison_package.json"

    report = write_d7_comparison_package.write_d7_comparison_package(
        project_id="project-d7",
        output_file=output,
        gold_file=gold_file,
        prediction_files=[lexical_file, live_file],
        comparison_output=package_dir / "comparison.json",
        artifact_dir=package_dir / "artifacts",
        verify_artifact=True,
    )

    manifest = run_d7_comparison_package.load_d7_comparison_package(output)
    assert manifest.schema_version == 1
    assert manifest.project_id == "project-d7"
    assert manifest.gold_file == "gold.json"
    assert manifest.prediction_files == ["lexical.json", "live.json"]
    assert manifest.output == "comparison.json"
    assert manifest.artifact_dir == "artifacts"
    assert manifest.verify_artifact is True
    assert report.package_file == str(output)
    assert report.prediction_files == [str(lexical_file), str(live_file)]
    assert "not held-out D7 evidence" in report.caution


def test_rejects_non_versioned_d7_gold_file(tmp_path):
    gold_file = _write_json(
        tmp_path / "raw_gold.json",
        {
            "contrary_evidence": [
                {
                    "target_claim_id": "claim-1",
                    "doc_id": "doc-1",
                    "start_char": 0,
                    "end_char": 5,
                }
            ]
        },
    )
    prediction_file = _write_json(tmp_path / "predictions.json", _prediction_package("lexical"))

    with pytest.raises(ValueError, match="versioned D7 gold-set package"):
        write_d7_comparison_package.build_d7_comparison_package_manifest(
            project_id="project-d7",
            output_file=tmp_path / "d7_comparison_package.json",
            gold_file=gold_file,
            prediction_files=[prediction_file],
        )


def test_rejects_invalid_prediction_package(tmp_path):
    gold_file = _write_json(tmp_path / "gold.json", _d7_gold_package())
    prediction_file = _write_json(
        tmp_path / "raw_predictions.json",
        {"disconfirmation_baselines": []},
    )

    with pytest.raises(ValueError, match="versioned D7 prediction package"):
        write_d7_comparison_package.build_d7_comparison_package_manifest(
            project_id="project-d7",
            output_file=tmp_path / "d7_comparison_package.json",
            gold_file=gold_file,
            prediction_files=[prediction_file],
        )


def test_protocol_runs_preflight_before_write(tmp_path, monkeypatch):
    captured = {}
    gold_file = _write_json(tmp_path / "gold.json", _d7_gold_package())
    prediction_file = _write_json(tmp_path / "predictions.json", _prediction_package("lexical"))
    protocol_file = _write_json(tmp_path / "protocol.json", {"schema_version": 1})
    output = tmp_path / "d7_comparison_package.json"

    def fake_preflight(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(
        write_d7_comparison_package.preflight_d7_comparison,
        "main",
        fake_preflight,
    )

    write_d7_comparison_package.write_d7_comparison_package(
        project_id="project-d7",
        output_file=output,
        gold_file=gold_file,
        prediction_files=[prediction_file],
        protocol_package=protocol_file,
    )

    manifest = run_d7_comparison_package.load_d7_comparison_package(output)
    assert captured["argv"] == [str(protocol_file), str(gold_file), str(prediction_file)]
    assert manifest.protocol_package == "protocol.json"


def test_script_outputs_machine_readable_report(tmp_path, capsys):
    gold_file = _write_json(tmp_path / "gold.json", _d7_gold_package())
    prediction_file = _write_json(tmp_path / "predictions.json", _prediction_package("lexical"))
    output = tmp_path / "d7_comparison_package.json"

    exit_code = write_d7_comparison_package.main([
        "project-d7",
        "--output",
        str(output),
        "--gold-file",
        str(gold_file),
        "--predictions-file",
        str(prediction_file),
        "--comparison-output",
        str(tmp_path / "comparison.json"),
        "--artifact-dir",
        str(tmp_path / "artifacts"),
        "--verify-artifact",
    ])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "complete"
    assert report["package_file"] == str(output)
    assert report["gold_file"] == str(gold_file)
    assert report["prediction_files"] == [str(prediction_file)]
    manifest = run_d7_comparison_package.load_d7_comparison_package(output)
    assert manifest.output == "comparison.json"
    assert manifest.artifact_dir == "artifacts"
    assert manifest.verify_artifact is True


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _d7_gold_package() -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "d7-heldout-v1",
        "dataset_name": "Held-out D7 comparison v1",
        "split": "held_out",
        "corpus_sha256": _CORPUS_HASH,
        "project_state_sha256": _STATE_HASH,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "expert-panel",
            "protocol": "Independent coding followed by adjudication.",
        },
        "contrary_evidence": [
            {
                "target_claim_id": "claim-1",
                "doc_id": "doc-1",
                "start_char": 0,
                "end_char": 5,
                "quote_text": "alpha",
            }
        ],
    }


def _prediction_package(name: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d7_retrieval_predictions",
        "retrieval_run": {
            "schema_version": 1,
            "project_id": "project-d7",
            "project_state_sha256": _STATE_HASH,
            "corpus_sha256": _CORPUS_HASH,
            "retrieval_mode": "lexical_bm25",
            "embedding_model": None,
            "embedding_dimensions": None,
            "max_targets": 10,
            "target_claim_count": 1,
            "candidates_per_claim": 1,
            "candidate_count": 1,
            "bm25_k1": 1.2,
            "bm25_b": 0.75,
            "contrary_cue_weight": 1.25,
            "expanded_term_weight": 0.5,
            "semantic_weight": 1.0,
            "min_semantic_similarity": 0.0,
            "trace_id": f"qualitative_coding/d7-retrieval/{name}",
            "max_budget": 1.0,
            "note": "Synthetic package for writer tests.",
        },
        "disconfirmation_baselines": [
            {
                "name": name,
                "description": f"{name} retrieval baseline",
                "contrary_evidence": [
                    {
                        "target_claim_id": "claim-1",
                        "doc_id": "doc-1",
                        "start_char": 0,
                        "end_char": 5,
                        "quote_text": "alpha",
                    }
                ],
            }
        ],
    }
