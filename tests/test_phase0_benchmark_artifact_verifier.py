"""Tests for Phase 0 benchmark artifact verification."""

from __future__ import annotations

import hashlib
import json

from scripts import verify_phase0_benchmark_artifact


def test_verify_phase0_benchmark_artifact_accepts_matching_package(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "verified"
    assert output["artifact_type"] == "qualitative_coding.phase0_scorecard"
    assert output["project_id"] == "project-phase0"
    assert output["checked_scorecard_count"] == 1
    assert output["checked_timing_count"] == 1
    assert output["failure_count"] == 0
    assert output["failures"] == []
    assert "not methodological-validity evidence" in output["caveat"]


def test_verify_phase0_benchmark_artifact_accepts_manifest_path(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir / "manifest.json")])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["status"] == "verified"
    assert output["manifest_path"] == str(run_dir / "manifest.json")
    assert output["scorecard_path"] == str(run_dir / "scorecard.json")
    assert output["timing_path"] == str(run_dir / "timing_d10.json")


def test_verify_phase0_benchmark_artifact_detects_scorecard_hash_mismatch(
    tmp_path,
    capsys,
):
    run_dir = _artifact_package(tmp_path)
    scorecard_path = run_dir / "scorecard.json"
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    scorecard["project"] = "Tampered"
    scorecard_path.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    assert any(
        failure["code"] == "scorecard_sha256_mismatch"
        for failure in output["failures"]
    )


def test_verify_phase0_benchmark_artifact_detects_timing_hash_mismatch(
    tmp_path,
    capsys,
):
    run_dir = _artifact_package(tmp_path)
    timing_path = run_dir / "timing_d10.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    timing["note"] = "Tampered"
    timing_path.write_text(json.dumps(timing, indent=2), encoding="utf-8")

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    assert any(
        failure["code"] == "timing_sha256_mismatch"
        for failure in output["failures"]
    )


def test_verify_phase0_benchmark_artifact_detects_metadata_mismatch(
    tmp_path,
    capsys,
):
    run_dir = _artifact_package(tmp_path)
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["input_hashes"]["project_state_sha256"] = "0" * 64
    manifest["run_configuration_hashes"]["prompt_hashes"]["status"] = "run"
    manifest["claim_discipline"]["caveat"] = "Changed"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    failure_codes = {failure["code"] for failure in output["failures"]}
    assert "input_hashes_mismatch" in failure_codes
    assert "run_configuration_hashes_mismatch" in failure_codes
    assert "claim_discipline_mismatch" in failure_codes


def test_verify_phase0_benchmark_artifact_detects_missing_timing(tmp_path, capsys):
    run_dir = _artifact_package(tmp_path)
    (run_dir / "timing_d10.json").unlink()

    exit_code = verify_phase0_benchmark_artifact.main([str(run_dir)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["status"] == "invalid"
    assert output["checked_timing_count"] == 0
    assert any(failure["code"] == "timing_file_missing" for failure in output["failures"])


def _artifact_package(tmp_path):
    run_dir = tmp_path / "20260622T000000000000Z-project-phase0-phase0"
    run_dir.mkdir()
    scorecard = {
        "project": "Phase 0 test",
        "cost_latency_d10": {"status": "not_available"},
        "wall_clock_d10": {"status": "not_available"},
        "_meta": {
            "phase": 0,
            "input_hashes": {
                "hash_algorithm": "sha256",
                "project_id": "project-phase0",
                "project_state_sha256": "1" * 64,
                "corpus_sha256": "2" * 64,
            },
            "run_configuration_hashes": {
                "prompt_hashes": {"status": "not_run"},
                "model_configuration": {"status": "not_available"},
            },
            "claims": {
                "caveat": (
                    "Phase 0 scorecard is local structural/provenance metadata "
                    "only; it is not methodological-validity evidence or SOTA "
                    "evidence."
                )
            },
        },
    }
    scorecard_text = json.dumps(scorecard, indent=2)
    scorecard_path = run_dir / "scorecard.json"
    scorecard_path.write_text(scorecard_text, encoding="utf-8")
    timing = {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.phase0_d10_timing",
        "source_file": "scorecard.json",
        "cost_latency_d10": scorecard["cost_latency_d10"],
        "wall_clock_d10": scorecard["wall_clock_d10"],
        "runtime_environment": {"python": {"version": "3.12"}},
        "note": (
            "D10 timing artifact packages local Phase 0 timing metadata for "
            "review. It is not public benchmark timing evidence."
        ),
    }
    timing_text = json.dumps(timing, indent=2)
    timing_path = run_dir / "timing_d10.json"
    timing_path.write_text(timing_text, encoding="utf-8")
    manifest = {
        "schema_version": 1,
        "artifact_type": "qualitative_coding.phase0_scorecard",
        "generated_at": "2026-06-22T00:00:00Z",
        "project_id": "project-phase0",
        "project_name": "Phase 0 test",
        "phase": 0,
        "scorecard_file": "scorecard.json",
        "scorecard_sha256": hashlib.sha256(scorecard_text.encode("utf-8")).hexdigest(),
        "timing_file": "timing_d10.json",
        "timing_sha256": hashlib.sha256(timing_text.encode("utf-8")).hexdigest(),
        "input_hashes": scorecard["_meta"]["input_hashes"],
        "run_configuration_hashes": scorecard["_meta"]["run_configuration_hashes"],
        "claim_discipline": scorecard["_meta"]["claims"],
        "prompt_eval": {
            "status": "not_run",
            "owner": "prompt_eval",
        },
        "command": {
            "project_id": "project-phase0",
            "artifact_dir": "benchmark_results",
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    return run_dir
