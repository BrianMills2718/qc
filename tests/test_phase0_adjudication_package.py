"""Tests for writing Phase 0 packages from imported adjudication gold."""

import json
from pathlib import Path

import pytest

from scripts import run_phase0_benchmark_package, write_phase0_adjudication_package


_CORPUS_HASH = "a" * 64
_STATE_HASH = "b" * 64


def test_writes_manifest_for_valid_d3_d7_gold_packages(tmp_path):
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    d3_gold = _write_json(package_dir / "d3_gold.json", _d3_package())
    d7_gold = _write_json(package_dir / "d7_gold.json", _d7_package())
    output = package_dir / "phase0_package.json"

    report = write_phase0_adjudication_package.write_phase0_adjudication_package(
        project_id="project-alpha",
        output_file=output,
        d3_gold_file=d3_gold,
        d7_gold_file=d7_gold,
        scorecard_output=package_dir / "scorecard.json",
        artifact_dir=package_dir / "benchmark_results",
    )

    manifest = run_phase0_benchmark_package.load_phase0_benchmark_package(output)
    assert manifest.project_id == "project-alpha"
    assert manifest.d3_gold_file == "d3_gold.json"
    assert manifest.gold_file == "d7_gold.json"
    assert manifest.output == "scorecard.json"
    assert manifest.artifact_dir == "benchmark_results"
    assert report.package_file == str(output)
    assert "not methodological validity evidence" in report.caution


def test_rejects_non_versioned_d3_gold_file(tmp_path):
    d3_gold = _write_json(
        tmp_path / "raw_d3_gold.json",
        {
            "application_gold": [
                {"code_id": "AI_USE", "doc_id": "doc-1", "start_char": 0, "end_char": 5}
            ]
        },
    )

    with pytest.raises(ValueError, match="versioned D3 gold-set package"):
        write_phase0_adjudication_package.build_phase0_adjudication_package_manifest(
            project_id="project-alpha",
            output_file=tmp_path / "phase0_package.json",
            d3_gold_file=d3_gold,
        )


def test_rejects_mismatched_d3_d7_provenance(tmp_path):
    d3_gold = _write_json(tmp_path / "d3_gold.json", _d3_package(corpus_sha256="c" * 64))
    d7_gold = _write_json(tmp_path / "d7_gold.json", _d7_package(corpus_sha256="d" * 64))

    with pytest.raises(ValueError, match="corpus_sha256"):
        write_phase0_adjudication_package.build_phase0_adjudication_package_manifest(
            project_id="project-alpha",
            output_file=tmp_path / "phase0_package.json",
            d3_gold_file=d3_gold,
            d7_gold_file=d7_gold,
        )


def test_script_outputs_machine_readable_report(tmp_path, capsys):
    d3_gold = _write_json(tmp_path / "d3_gold.json", _d3_package())
    output = tmp_path / "phase0_package.json"

    exit_code = write_phase0_adjudication_package.main([
        "project-alpha",
        "--output",
        str(output),
        "--d3-gold-file",
        str(d3_gold),
    ])

    assert exit_code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "complete"
    assert report["package_file"] == str(output)
    assert report["d3_gold_file"] == str(d3_gold)
    assert report["d7_gold_file"] is None
    loaded = run_phase0_benchmark_package.load_phase0_benchmark_package(output)
    assert loaded.d3_gold_file == "d3_gold.json"
    assert loaded.gold_file is None


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _d3_package(
    *,
    corpus_sha256: str = _CORPUS_HASH,
    project_state_sha256: str = _STATE_HASH,
) -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "adjudication-gold-v1",
        "dataset_name": "Adjudication gold v1",
        "split": "dev",
        "corpus_sha256": corpus_sha256,
        "project_state_sha256": project_state_sha256,
        "prompt_frozen": False,
        "contamination_checked": False,
        "adjudication": {
            "coder_count": 1,
            "adjudicator": "expert-a",
            "protocol": "Validated adjudication import.",
            "human_human_agreement": None,
            "notes": "",
        },
        "application_gold": [
            {
                "code_id": "AI_USE",
                "doc_id": "doc-1",
                "start_char": 0,
                "end_char": 5,
                "quote_text": "AI use",
            }
        ],
    }


def _d7_package(
    *,
    corpus_sha256: str = _CORPUS_HASH,
    project_state_sha256: str = _STATE_HASH,
) -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "adjudication-gold-v1",
        "dataset_name": "Adjudication gold v1",
        "split": "dev",
        "corpus_sha256": corpus_sha256,
        "project_state_sha256": project_state_sha256,
        "prompt_frozen": False,
        "contamination_checked": False,
        "adjudication": {
            "coder_count": 1,
            "adjudicator": "expert-a",
            "protocol": "Validated adjudication import.",
            "human_human_agreement": None,
            "notes": "",
        },
        "contrary_evidence": [
            {
                "target_claim_id": "claim-1",
                "doc_id": "doc-1",
                "start_char": 10,
                "end_char": 20,
                "quote_text": "contrary",
            }
        ],
    }
