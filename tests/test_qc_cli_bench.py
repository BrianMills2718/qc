"""Tests for the top-level qc_cli bench command."""

import hashlib
import json
import sys

import qc_cli
from scripts import (
    bench_phase0,
    run_phase0_benchmark_package,
    verify_phase0_benchmark_artifact,
)
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import Corpus, Document, ProjectState


def test_qc_cli_bench_emits_phase0_scorecard(tmp_path, monkeypatch, capsys):
    state = ProjectState(
        id="cli_bench",
        name="CLI Bench",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(sys, "argv", ["qc_cli.py", "bench", state.id])

    exit_code = qc_cli.main()

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["project"] == "CLI Bench"
    assert output["_meta"]["phase"] == 0
    assert output["_meta"]["input_hashes"]["project_id"] == state.id


def test_qc_cli_bench_forwards_all_phase0_flags(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(bench_phase0, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench",
            "cli_project",
            "--d3-gold-file",
            "d3_gold.json",
            "--d3-baselines-file",
            "d3_baselines.json",
            "--d3-comparison-protocol-file",
            "d3_protocol.json",
            "--gold-file",
            "d7_gold.json",
            "--d7-baselines-file",
            "d7_baselines.json",
            "--prompt-injection-file",
            "inv7.json",
            "--inv7-live-protocol-file",
            "inv7_protocol.json",
            "--d6-bias-protocol-file",
            "d6_protocol.json",
            "--bias-counterfactual-file",
            "bias_counterfactual.json",
            "--bias-stratified-file",
            "bias_stratified.json",
            "--d4-codebook-quality-protocol-file",
            "d4_protocol.json",
            "--codebook-quality-file",
            "codebook_quality.json",
            "--d8-gt-fidelity-protocol-file",
            "d8_protocol.json",
            "--gt-fidelity-file",
            "gt_fidelity.json",
            "--interpretive-preference-file",
            "preference.json",
            "--d9-interpretive-preference-protocol-file",
            "d9_protocol.json",
            "--confidence-calibration-file",
            "calibration.json",
            "--confidence-calibration-protocol-file",
            "confidence_protocol.json",
            "--observability-db",
            "observability.db",
            "--trace-id",
            "trace-123",
            "--output",
            "scorecard.json",
            "--artifact-dir",
            "artifacts",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == [
        "cli_project",
        "--d3-gold-file",
        "d3_gold.json",
        "--d3-baselines-file",
        "d3_baselines.json",
        "--d3-comparison-protocol-file",
        "d3_protocol.json",
        "--gold-file",
        "d7_gold.json",
        "--d7-baselines-file",
        "d7_baselines.json",
        "--prompt-injection-file",
        "inv7.json",
        "--inv7-live-protocol-file",
        "inv7_protocol.json",
        "--d6-bias-protocol-file",
        "d6_protocol.json",
        "--bias-counterfactual-file",
        "bias_counterfactual.json",
        "--bias-stratified-file",
        "bias_stratified.json",
        "--d4-codebook-quality-protocol-file",
        "d4_protocol.json",
        "--codebook-quality-file",
        "codebook_quality.json",
        "--d8-gt-fidelity-protocol-file",
        "d8_protocol.json",
        "--gt-fidelity-file",
        "gt_fidelity.json",
        "--interpretive-preference-file",
        "preference.json",
        "--d9-interpretive-preference-protocol-file",
        "d9_protocol.json",
        "--confidence-calibration-file",
        "calibration.json",
        "--confidence-calibration-protocol-file",
        "confidence_protocol.json",
        "--observability-db",
        "observability.db",
        "--trace-id",
        "trace-123",
        "--output",
        "scorecard.json",
        "--artifact-dir",
        "artifacts",
    ]


def test_qc_cli_bench_package_forwards_manifest_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(run_phase0_benchmark_package, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench-package",
            "phase0_package.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["phase0_package.json"]


def test_qc_cli_verify_phase0_benchmark_artifact_forwards_path(monkeypatch):
    captured = {}

    def fake_main(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(verify_phase0_benchmark_artifact, "main", fake_main)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "verify-phase0-benchmark-artifact",
            "benchmark_results/run/manifest.json",
        ],
    )

    assert qc_cli.main() == 0
    assert captured["argv"] == ["benchmark_results/run/manifest.json"]


def test_qc_cli_bench_forwards_files_and_output(tmp_path, monkeypatch, capsys):
    content = "AI failed here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(id="cli_bench_files", name="CLI Bench Files", corpus=Corpus(documents=[doc]))
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps({
            "application_gold": [
                {
                    "code_id": "AI_USE",
                    "doc_id": doc.id,
                    "start_char": 0,
                    "end_char": len(content),
                }
            ],
        }),
        encoding="utf-8",
    )
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(
        json.dumps({
            "contrary_evidence": [
                {
                    "target_claim_id": "claim-ai",
                    "doc_id": doc.id,
                    "start_char": 0,
                    "end_char": len(content),
                }
            ],
        }),
        encoding="utf-8",
    )
    bias_file = tmp_path / "bias_counterfactual.json"
    bias_file.write_text(
        json.dumps({
            "bias_counterfactual_evaluations": [
                {
                    "case_id": "identity-stable",
                    "attribute": "parental_status",
                    "original_codes": ["trust"],
                    "counterfactual_codes": ["trust"],
                }
            ]
        }),
        encoding="utf-8",
    )
    quality_file = tmp_path / "codebook_quality.json"
    quality_file.write_text(
        json.dumps({
            "codebook_quality_evaluations": [
                {
                    "evaluator": "judge-a",
                    "evaluator_type": "llm_judge",
                    "clarity": 0.8,
                    "specificity": 0.7,
                    "usefulness": 0.9,
                    "grounding": 1.0,
                }
            ]
        }),
        encoding="utf-8",
    )
    gt_fidelity_file = tmp_path / "gt_fidelity.json"
    gt_fidelity_file.write_text(
        json.dumps({
            "gt_fidelity_evaluations": [
                {
                    "evaluator": "judge-a",
                    "evaluator_type": "llm_judge",
                    "constant_comparison": 0.8,
                    "category_development": 0.7,
                    "memo_quality": 0.9,
                    "saturation_justification": 0.6,
                }
            ]
        }),
        encoding="utf-8",
    )
    preference_file = tmp_path / "interpretive_preference.json"
    preference_file.write_text(
        json.dumps({
            "interpretive_preference_evaluations": [
                {
                    "case_id": "latent-1",
                    "evaluator": "expert-a",
                    "preferred": "system",
                }
            ]
        }),
        encoding="utf-8",
    )
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(
        json.dumps({
            "confidence_calibration_evaluations": [
                {
                    "item_id": "theme-correct",
                    "surface": "thematic_coding",
                    "confidence": 0.9,
                    "correct": True,
                }
            ]
        }),
        encoding="utf-8",
    )
    output_file = tmp_path / "scorecard.json"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench",
            state.id,
            "--d3-gold-file",
            str(d3_gold_file),
            "--gold-file",
            str(gold_file),
            "--bias-counterfactual-file",
            str(bias_file),
            "--codebook-quality-file",
            str(quality_file),
            "--gt-fidelity-file",
            str(gt_fidelity_file),
            "--interpretive-preference-file",
            str(preference_file),
            "--confidence-calibration-file",
            str(calibration_file),
            "--output",
            str(output_file),
        ],
    )

    exit_code = qc_cli.main()

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    file_scorecard = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_scorecard == file_scorecard
    assert stdout_scorecard["application_validity_d3"]["status"] == "scored"
    assert stdout_scorecard["disconfirmation_d7"]["status"] == "scored"
    assert stdout_scorecard["bias_counterfactual_d6"]["status"] == "scored"
    assert stdout_scorecard["codebook_quality_d4"]["status"] == "scored"
    assert stdout_scorecard["gt_fidelity_d8"]["status"] == "scored"
    assert stdout_scorecard["interpretive_preference_d9"]["status"] == "scored"
    assert stdout_scorecard["confidence_calibration"]["status"] == "scored"
    expected_d3_hash = hashlib.sha256(d3_gold_file.read_bytes()).hexdigest()
    expected_hash = hashlib.sha256(gold_file.read_bytes()).hexdigest()
    expected_bias_hash = hashlib.sha256(bias_file.read_bytes()).hexdigest()
    expected_quality_hash = hashlib.sha256(quality_file.read_bytes()).hexdigest()
    expected_gt_fidelity_hash = hashlib.sha256(gt_fidelity_file.read_bytes()).hexdigest()
    expected_preference_hash = hashlib.sha256(preference_file.read_bytes()).hexdigest()
    expected_calibration_hash = hashlib.sha256(calibration_file.read_bytes()).hexdigest()
    assert stdout_scorecard["_meta"]["input_hashes"]["d3_gold_file_sha256"] == expected_d3_hash
    assert stdout_scorecard["_meta"]["input_hashes"]["gold_file_sha256"] == expected_hash
    assert stdout_scorecard["_meta"]["input_hashes"]["bias_counterfactual_file_sha256"] == expected_bias_hash
    assert stdout_scorecard["_meta"]["input_hashes"]["codebook_quality_file_sha256"] == expected_quality_hash
    assert stdout_scorecard["_meta"]["input_hashes"][
        "gt_fidelity_file_sha256"
    ] == expected_gt_fidelity_hash
    assert stdout_scorecard["_meta"]["input_hashes"][
        "interpretive_preference_file_sha256"
    ] == expected_preference_hash
    assert stdout_scorecard["_meta"]["input_hashes"][
        "confidence_calibration_file_sha256"
    ] == expected_calibration_hash


def test_qc_cli_bench_forwards_artifact_dir(tmp_path, monkeypatch, capsys):
    state = ProjectState(
        id="cli_bench_artifacts",
        name="CLI Bench Artifacts",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_cli.py",
            "bench",
            state.id,
            "--artifact-dir",
            str(artifact_root),
        ],
    )

    exit_code = qc_cli.main()

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    run_dirs = [path for path in artifact_root.iterdir() if path.is_dir()]
    assert len(run_dirs) == 1
    scorecard = json.loads((run_dirs[0] / "scorecard.json").read_text(encoding="utf-8"))
    assert scorecard == stdout_scorecard
    assert (run_dirs[0] / "manifest.json").exists()
