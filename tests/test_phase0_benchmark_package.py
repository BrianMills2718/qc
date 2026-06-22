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
                    "evaluator_type": "unspecified",
                    "clarity": 0.8,
                    "specificity": 0.7,
                    "usefulness": 0.9,
                    "grounding": 1.0,
                }
            ]
        }),
        encoding="utf-8",
    )
    d4_protocol = package_dir / "d4_protocol.json"
    d4_protocol.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d4_codebook_quality_protocol",
            "protocol_id": "d4-package-protocol-v1",
            "project_id": state.id,
            "dataset_name": "D4 package protocol v1",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": "b" * 64,
            "codebook_artifact_sha256": "c" * 64,
            "prompt_frozen": True,
            "contamination_checked": True,
            "registered_before_evaluation": True,
            "blinding": {
                "raters_blinded_to_origin": True,
                "source_labels_masked": True,
                "blinding_method": "Package fixture masks codebook origin.",
            },
            "evaluator_plan": {
                "evaluator_types": ["unspecified"],
                "planned_evaluator_count": 1,
                "qualification": "Package fixture evaluator.",
            },
            "rubric_metrics": ["clarity", "specificity", "usefulness", "grounding"],
            "target_scopes": ["codebook"],
            "outcome_file": "quality.json",
            "outcome_file_sha256": bench_phase0.sha256_file(quality),
            "success_criteria": [
                {
                    "metric": "clarity",
                    "pass_condition": "Report clarity before any claim.",
                },
                {
                    "metric": "specificity",
                    "pass_condition": "Report specificity before any claim.",
                },
                {
                    "metric": "usefulness",
                    "pass_condition": "Report usefulness before any claim.",
                },
                {
                    "metric": "grounding",
                    "pass_condition": "Report grounding before any claim.",
                },
            ],
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
    d6_protocol = package_dir / "d6_protocol.json"
    d6_protocol.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d6_bias_protocol",
            "protocol_id": "d6-package-protocol-v1",
            "project_id": state.id,
            "dataset_name": "D6 package protocol v1",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": "b" * 64,
            "prompt_frozen": True,
            "contamination_checked": True,
            "registered_before_run": True,
            "dimensions": ["bias_stratified_d6"],
            "attribute_policy": {
                "attributes": ["gender"],
                "attribute_source": "Study metadata.",
                "ethical_review": "Approved aggregate diagnostic use.",
                "use_permitted": True,
                "privacy_protection": "Aggregate reporting only.",
            },
            "case_set": {
                "case_set_id": "d6-package-cases-v1",
                "case_set_version": "1",
                "planned_case_count": 2,
            },
            "stratified_strategy": {
                "attributes": ["gender"],
                "surfaces": ["application_validity"],
                "correctness_label_source": "Package test labels.",
                "outcome_file": "bias_stratified.json",
                "outcome_file_sha256": bench_phase0.sha256_file(bias_stratified),
            },
            "success_criteria": [
                {
                    "dimension": "bias_stratified_d6",
                    "metric": "max_error_rate_gap",
                    "pass_condition": "Report gap before any claim.",
                }
            ],
        }),
        encoding="utf-8",
    )
    gt_fidelity = package_dir / "gt_fidelity.json"
    gt_fidelity.write_text(
        json.dumps({
            "gt_fidelity_evaluations": [
                {
                    "evaluator": "judge-a",
                    "evaluator_type": "llm_judge",
                    "constant_comparison": 0.8,
                    "category_development": 0.7,
                    "memo_quality": 0.9,
                    "saturation_justification": 0.6,
                    "scope": "grounded_theory_pipeline",
                }
            ]
        }),
        encoding="utf-8",
    )
    d8_protocol = package_dir / "d8_protocol.json"
    d8_protocol.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d8_gt_fidelity_protocol",
            "protocol_id": "d8-package-protocol-v1",
            "project_id": state.id,
            "dataset_name": "D8 package protocol v1",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": "b" * 64,
            "gt_artifact_sha256": "c" * 64,
            "prompt_frozen": True,
            "contamination_checked": True,
            "registered_before_evaluation": True,
            "evaluator_plan": {
                "evaluator_types": ["llm_judge"],
                "planned_evaluator_count": 1,
                "qualification": "Package fixture evaluator.",
            },
            "rubric_metrics": [
                "constant_comparison",
                "category_development",
                "memo_quality",
                "saturation_justification",
            ],
            "target_scopes": ["grounded_theory_pipeline"],
            "outcome_file": "gt_fidelity.json",
            "outcome_file_sha256": bench_phase0.sha256_file(gt_fidelity),
            "success_criteria": [
                {
                    "metric": "constant_comparison",
                    "pass_condition": "Report constant comparison before any claim.",
                },
                {
                    "metric": "category_development",
                    "pass_condition": "Report category development before any claim.",
                },
                {
                    "metric": "memo_quality",
                    "pass_condition": "Report memo quality before any claim.",
                },
                {
                    "metric": "saturation_justification",
                    "pass_condition": "Report saturation before any claim.",
                },
            ],
        }),
        encoding="utf-8",
    )
    preference = package_dir / "interpretive_preference.json"
    preference.write_text(
        json.dumps({
            "interpretive_preference_evaluations": [
                {
                    "case_id": "case-1",
                    "evaluator": "expert-1",
                    "evaluator_type": "human_expert",
                    "preferred": "system",
                    "criterion": "interpretive_depth",
                    "surface": "codebook",
                },
                {
                    "case_id": "case-2",
                    "evaluator": "expert-2",
                    "evaluator_type": "human_expert",
                    "preferred": "human",
                    "criterion": "latent_meaning",
                    "surface": "themes",
                },
            ]
        }),
        encoding="utf-8",
    )
    d9_protocol = package_dir / "d9_protocol.json"
    d9_protocol.write_text(
        json.dumps({
            "schema_version": 1,
            "package_type": "qualitative_coding.d9_interpretive_preference_protocol",
            "protocol_id": "d9-package-protocol-v1",
            "project_id": state.id,
            "dataset_name": "D9 package protocol v1",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": "b" * 64,
            "comparison_artifact_sha256": "c" * 64,
            "prompt_frozen": True,
            "contamination_checked": True,
            "registered_before_evaluation": True,
            "blinded": True,
            "evaluator_plan": {
                "evaluator_types": ["human_expert"],
                "planned_evaluator_count": 2,
                "qualification": "Package fixture expert panel.",
            },
            "target_criteria": ["interpretive_depth", "latent_meaning"],
            "target_surfaces": ["codebook", "themes"],
            "planned_case_count": 2,
            "non_inferiority_margin": 0.1,
            "outcome_metrics": [
                "system_minus_human_preference_rate",
                "system_preference_rate",
                "tie_rate",
            ],
            "outcome_file": "interpretive_preference.json",
            "outcome_file_sha256": bench_phase0.sha256_file(preference),
            "success_criteria": [
                {
                    "metric": "system_minus_human_preference_rate",
                    "pass_condition": "Lower CI bound must be above the margin.",
                },
                {
                    "metric": "system_preference_rate",
                    "pass_condition": "Report preference rate before any claim.",
                },
                {
                    "metric": "tie_rate",
                    "pass_condition": "Report tie rate before any claim.",
                },
            ],
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
            "d6_bias_protocol_file": "d6_protocol.json",
            "d4_codebook_quality_protocol_file": "d4_protocol.json",
            "codebook_quality_file": "quality.json",
            "d8_gt_fidelity_protocol_file": "d8_protocol.json",
            "gt_fidelity_file": "gt_fidelity.json",
            "d9_interpretive_preference_protocol_file": "d9_protocol.json",
            "interpretive_preference_file": "interpretive_preference.json",
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
    assert output["gt_fidelity_d8"]["status"] == "scored"
    assert output["interpretive_preference_d9"]["status"] == "scored"
    assert output["_meta"]["preflight_reports"]["d6_bias"]["status"] == "pass"
    assert output["_meta"]["preflight_reports"]["d4_codebook_quality"]["status"] == "pass"
    assert output["_meta"]["preflight_reports"]["d8_gt_fidelity"]["status"] == "pass"
    assert (
        output["_meta"]["preflight_reports"]["d9_interpretive_preference"]["status"]
        == "pass"
    )
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d3_gold_file_sha256"] == bench_phase0.sha256_file(d3_gold)
    assert hashes["d3_baselines_file_sha256"] == bench_phase0.sha256_file(d3_baselines)
    assert hashes["bias_stratified_file_sha256"] == bench_phase0.sha256_file(bias_stratified)
    assert hashes["d6_bias_protocol_file_sha256"] == bench_phase0.sha256_file(d6_protocol)
    assert hashes["d4_codebook_quality_protocol_file_sha256"] == (
        bench_phase0.sha256_file(d4_protocol)
    )
    assert hashes["codebook_quality_file_sha256"] == bench_phase0.sha256_file(quality)
    assert hashes["d8_gt_fidelity_protocol_file_sha256"] == (
        bench_phase0.sha256_file(d8_protocol)
    )
    assert hashes["gt_fidelity_file_sha256"] == bench_phase0.sha256_file(gt_fidelity)
    assert hashes["d9_interpretive_preference_protocol_file_sha256"] == (
        bench_phase0.sha256_file(d9_protocol)
    )
    assert hashes["interpretive_preference_file_sha256"] == (
        bench_phase0.sha256_file(preference)
    )
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra
    assert "application_baselines" not in reloaded.config.extra
    assert "bias_stratified_evaluations" not in reloaded.config.extra
    assert "codebook_quality_evaluations" not in reloaded.config.extra
    assert "gt_fidelity_evaluations" not in reloaded.config.extra
    assert "interpretive_preference_evaluations" not in reloaded.config.extra


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
        d8_gt_fidelity_protocol_file="protocols/d8.json",
        gt_fidelity_file="rubrics/d8.json",
        d9_interpretive_preference_protocol_file="protocols/d9.json",
        interpretive_preference_file="rubrics/d9.json",
        trace_id="trace-123",
    )

    argv = run_phase0_benchmark_package.phase0_package_to_bench_argv(package, tmp_path)

    assert argv == [
        "project",
        "--d3-gold-file",
        str(tmp_path / "gold" / "d3.json"),
        "--d3-baselines-file",
        str(tmp_path / "baselines" / "d3.json"),
        "--d8-gt-fidelity-protocol-file",
        str(tmp_path / "protocols" / "d8.json"),
        "--gt-fidelity-file",
        str(tmp_path / "rubrics" / "d8.json"),
        "--d9-interpretive-preference-protocol-file",
        str(tmp_path / "protocols" / "d9.json"),
        "--interpretive-preference-file",
        str(tmp_path / "rubrics" / "d9.json"),
        "--trace-id",
        "trace-123",
    ]
