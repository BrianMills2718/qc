"""Tests for manifest-driven Phase 0 benchmark package execution."""

import json

import pytest

from scripts import bench_phase0, run_phase0_benchmark_package
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import CodeApplication, Corpus, Document, ProjectState


def test_phase0_benchmark_package_forwards_relative_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(
        id="package_project",
        name="Package project",
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content,
                start_char=0,
                end_char=len(content),
            )
        ],
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    d3_gold = package_dir / "d3_gold.json"
    d3_gold.write_text(
        json.dumps({
            "application_gold": [
                {
                    "code_id": "AI_USE",
                    "doc_id": doc.id,
                    "start_char": 0,
                    "end_char": len(content),
                }
            ]
        }),
        encoding="utf-8",
    )
    d3_baselines = package_dir / "d3_baselines.json"
    d3_baselines.write_text(
        json.dumps({
            "application_baselines": [
                {
                    "name": "empty_application_baseline",
                    "code_applications": [],
                }
            ]
        }),
        encoding="utf-8",
    )
    quality = package_dir / "quality.json"
    quality.write_text(
        json.dumps({
            "codebook_quality_evaluations": [
                {
                    "evaluator": "judge-a",
                    "clarity": 0.8,
                    "specificity": 0.7,
                    "usefulness": 0.9,
                    "grounding": 1.0,
                }
            ]
        }),
        encoding="utf-8",
    )
    bias_stratified = package_dir / "bias_stratified.json"
    bias_stratified.write_text(
        json.dumps({
            "bias_stratified_evaluations": [
                {
                    "case_id": "gender-woman-correct",
                    "attribute": "gender",
                    "group": "woman",
                    "surface": "application_validity",
                    "correct": True,
                },
                {
                    "case_id": "gender-man-error",
                    "attribute": "gender",
                    "group": "man",
                    "surface": "application_validity",
                    "correct": False,
                },
            ]
        }),
        encoding="utf-8",
    )
    package_file = package_dir / "phase0_package.json"
    package_file.write_text(
        json.dumps({
            "schema_version": 1,
            "project_id": state.id,
            "d3_gold_file": "d3_gold.json",
            "d3_baselines_file": "d3_baselines.json",
            "bias_stratified_file": "bias_stratified.json",
            "codebook_quality_file": "quality.json",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = run_phase0_benchmark_package.main([str(package_file)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["application_validity_d3"]["status"] == "scored"
    assert output["application_validity_d3"]["recall"] == 1.0
    baseline = output["application_validity_d3"]["baselines"]["empty_application_baseline"]
    assert baseline["false_negatives"] == 1
    assert baseline["system_minus_baseline"]["recall"] == 1.0
    assert output["codebook_quality_d4"]["status"] == "scored"
    assert output["bias_stratified_d6"]["status"] == "scored"
    assert output["bias_stratified_d6"]["incorrect_cases"] == 1
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d3_gold_file_sha256"] == bench_phase0.sha256_file(d3_gold)
    assert hashes["d3_baselines_file_sha256"] == bench_phase0.sha256_file(d3_baselines)
    assert hashes["bias_stratified_file_sha256"] == bench_phase0.sha256_file(bias_stratified)
    assert hashes["codebook_quality_file_sha256"] == bench_phase0.sha256_file(quality)
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra
    assert "application_baselines" not in reloaded.config.extra
    assert "bias_stratified_evaluations" not in reloaded.config.extra
    assert "codebook_quality_evaluations" not in reloaded.config.extra


def test_phase0_benchmark_package_rejects_unknown_keys(tmp_path, capsys):
    package_file = tmp_path / "phase0_package.json"
    package_file.write_text(
        json.dumps({
            "schema_version": 1,
            "project_id": "project",
            "unexpected": "nope",
        }),
        encoding="utf-8",
    )

    exit_code = run_phase0_benchmark_package.main([str(package_file)])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "extra_forbidden" in output["error"]


def test_phase0_benchmark_package_forwards_output_and_artifact_dir(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="package_artifacts",
        name="Package artifacts",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    package_dir = tmp_path / "package"
    package_dir.mkdir()
    package_file = package_dir / "phase0_package.json"
    output_file = package_dir / "scorecard.json"
    artifact_dir = package_dir / "benchmark_results"
    package_file.write_text(
        json.dumps({
            "schema_version": 1,
            "project_id": state.id,
            "output": "scorecard.json",
            "artifact_dir": "benchmark_results",
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = run_phase0_benchmark_package.main([str(package_file)])

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    file_scorecard = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_scorecard == file_scorecard
    run_dirs = [path for path in artifact_dir.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    manifest = json.loads((run_dirs[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["project_id"] == state.id
    assert manifest["command"]["output"] == str(output_file)
    assert manifest["command"]["artifact_dir"] == str(artifact_dir)


def test_phase0_package_to_bench_argv_resolves_relative_paths(tmp_path):
    package = run_phase0_benchmark_package.Phase0BenchmarkPackage(
        schema_version=1,
        project_id="project",
        d3_gold_file="gold/d3.json",
        d3_baselines_file="baselines/d3.json",
        trace_id="trace-123",
    )

    argv = run_phase0_benchmark_package.phase0_package_to_bench_argv(package, tmp_path)

    assert argv == [
        "project",
        "--d3-gold-file",
        str(tmp_path / "gold" / "d3.json"),
        "--d3-baselines-file",
        str(tmp_path / "baselines" / "d3.json"),
        "--trace-id",
        "trace-123",
    ]
