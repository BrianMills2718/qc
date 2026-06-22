"""Tests for the Phase 0 bench CLI script."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

import pytest

from scripts import bench_phase0
from qc_clean.core.inv7_fixtures import run_inv7_structural_fixtures
from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimAnchor,
    ClaimKind,
    ClaimScope,
    CodeApplication,
    Corpus,
    Document,
    Methodology,
    ProjectConfig,
    ProjectState,
)


def test_bench_phase0_includes_input_hashes_without_external_files(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_hashes",
        name="Hash project",
        config=ProjectConfig(
            methodology=Methodology.THEMATIC_ANALYSIS,
            model_name="gpt-5-large",
            extra={"phase0_exact_bootstrap": {"samples": 11}},
        ),
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    hashes = output["_meta"]["input_hashes"]
    persisted = store.load(state.id)
    assert hashes["hash_algorithm"] == "sha256"
    assert hashes["project_id"] == state.id
    assert hashes["project_state_sha256"] == bench_phase0.sha256_jsonable(
        persisted.model_dump(mode="json")
    )
    assert hashes["corpus_sha256"] == bench_phase0.sha256_jsonable(
        bench_phase0.corpus_hash_payload(persisted)
    )
    assert hashes["d3_gold_file_sha256"] is None
    assert hashes["d3_baselines_file_sha256"] is None
    assert hashes["d3_comparison_protocol_file_sha256"] is None
    assert hashes["gold_file_sha256"] is None
    assert hashes["d7_baselines_file_sha256"] is None
    assert hashes["prompt_injection_file_sha256"] is None
    assert hashes["inv7_live_protocol_file_sha256"] is None
    assert hashes["d6_bias_protocol_file_sha256"] is None
    assert hashes["d4_codebook_quality_protocol_file_sha256"] is None
    assert hashes["d8_gt_fidelity_protocol_file_sha256"] is None
    assert hashes["d9_interpretive_preference_protocol_file_sha256"] is None
    assert hashes["confidence_calibration_protocol_file_sha256"] is None
    assert hashes["bias_counterfactual_file_sha256"] is None
    assert hashes["bias_stratified_file_sha256"] is None
    assert hashes["codebook_quality_file_sha256"] is None
    assert hashes["gt_fidelity_file_sha256"] is None
    assert hashes["interpretive_preference_file_sha256"] is None
    assert hashes["confidence_calibration_file_sha256"] is None
    assert hashes["observability_db_sha256"] is None
    run_config = output["_meta"]["run_configuration_hashes"]
    assert run_config["hash_algorithm"] == "sha256"
    assert run_config["project_id"] == state.id
    assert run_config["methodology"] == "thematic_analysis"
    assert run_config["model_name"] == "gpt-5-large"
    assert run_config["project_config_sha256"] == bench_phase0.sha256_jsonable(
        bench_phase0.run_configuration_hash_payload(persisted)
    )
    assert run_config["prompt_hashes"]["status"] == "not_run"
    assert "Phase 0 does not execute prompt templates" in run_config["prompt_hashes"]["reason"]


def test_bench_phase0_loads_project_from_projects_dir(tmp_path, capsys):
    state = ProjectState(
        id="project_store_arg",
        name="Project store arg",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    store.save(state)

    exit_code = bench_phase0.main([state.id, "--projects-dir", str(projects_dir)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["_meta"]["input_hashes"]["project_id"] == state.id


def test_bench_phase0_hashes_external_input_files(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI failed here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(id="project_external_hashes", name="External hashes", corpus=Corpus(documents=[doc]))
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
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps({
            "application_baselines": [
                {"name": "empty_application_baseline", "code_applications": []}
            ]
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
    baselines_file = tmp_path / "baselines.json"
    baselines_file.write_text(
        json.dumps({
            "disconfirmation_baselines": [
                {"name": "empty_baseline", "contrary_evidence": []}
            ]
        }),
        encoding="utf-8",
    )
    injection_file = tmp_path / "prompt_injection.json"
    injection_file.write_text(
        json.dumps({
            "prompt_injection_evaluations": [
                {
                    "fixture_id": "direct",
                    "surface": "thematic_coding",
                    "attack_succeeded": False,
                }
            ]
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
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--gold-file",
        str(gold_file),
        "--d7-baselines-file",
        str(baselines_file),
        "--prompt-injection-file",
        str(injection_file),
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
        "--observability-db",
        str(db_path),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d3_gold_file_sha256"] == _sha256_file(d3_gold_file)
    assert hashes["d3_baselines_file_sha256"] == _sha256_file(d3_baselines_file)
    assert hashes["d3_comparison_protocol_file_sha256"] is None
    assert hashes["gold_file_sha256"] == _sha256_file(gold_file)
    assert hashes["d7_baselines_file_sha256"] == _sha256_file(baselines_file)
    assert hashes["prompt_injection_file_sha256"] == _sha256_file(injection_file)
    assert hashes["d6_bias_protocol_file_sha256"] is None
    assert hashes["d8_gt_fidelity_protocol_file_sha256"] is None
    assert hashes["d9_interpretive_preference_protocol_file_sha256"] is None
    assert hashes["confidence_calibration_protocol_file_sha256"] is None
    assert hashes["bias_counterfactual_file_sha256"] == _sha256_file(bias_file)
    assert hashes["codebook_quality_file_sha256"] == _sha256_file(quality_file)
    assert hashes["gt_fidelity_file_sha256"] == _sha256_file(gt_fidelity_file)
    assert hashes["interpretive_preference_file_sha256"] == _sha256_file(preference_file)
    assert hashes["confidence_calibration_file_sha256"] == _sha256_file(calibration_file)
    assert hashes["observability_db_sha256"] == _sha256_file(db_path)
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra
    assert "application_baselines" not in reloaded.config.extra
    assert "disconfirmation_gold" not in reloaded.config.extra
    assert "disconfirmation_baselines" not in reloaded.config.extra
    assert "prompt_injection_evaluations" not in reloaded.config.extra
    assert "bias_counterfactual_evaluations" not in reloaded.config.extra
    assert "codebook_quality_evaluations" not in reloaded.config.extra
    assert "gt_fidelity_evaluations" not in reloaded.config.extra
    assert "interpretive_preference_evaluations" not in reloaded.config.extra
    assert "confidence_calibration_evaluations" not in reloaded.config.extra


def test_bench_phase0_scores_d3_from_gold_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(
        id="project_d3_gold",
        name="D3 gold project",
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
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id, "--d3-gold-file", str(d3_gold_file)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["application_validity_d3"]["status"] == "scored"
    assert output["application_validity_d3"]["recall"] == 1.0
    assert output["_meta"]["input_hashes"]["d3_gold_file_sha256"] == _sha256_file(d3_gold_file)
    assert "gold_provenance" not in output["application_validity_d3"]
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra


def test_bench_phase0_scores_d3_baselines_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery. AI failed in the pilot. AI only appeared later."
    doc = Document(id="d1", name="interview.txt", content=content)
    gold_start = content.index("AI helped")
    gold_end = gold_start + len("AI helped delivery.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
        id="project_d3_baseline",
        name="D3 baseline project",
        config=ProjectConfig(extra={}),
        corpus=Corpus(documents=[doc]),
        code_applications=[
            CodeApplication(
                code_id="AI_USE",
                doc_id=doc.id,
                quote_text=content[gold_start:gold_end],
                start_char=gold_start,
                end_char=gold_end,
            )
        ],
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps({
            "application_gold": [
                {
                    "code_id": "AI_USE",
                    "doc_id": doc.id,
                    "start_char": gold_start,
                    "end_char": gold_end,
                }
            ],
        }),
        encoding="utf-8",
    )
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps({
            "application_baselines": [
                {
                    "name": "single_prompt",
                    "code_applications": [
                        {
                            "code_id": "AI_USE",
                            "doc_id": doc.id,
                            "start_char": extra_start,
                            "end_char": extra_end,
                        }
                    ],
                }
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    baseline = output["application_validity_d3"]["baselines"]["single_prompt"]
    assert baseline["true_positives"] == 0
    assert baseline["false_positives"] == 1
    assert baseline["false_negatives"] == 1
    assert baseline["system_minus_baseline"]["recall"] == 1.0
    assert baseline["span_overlap"]["status"] == "scored"
    assert baseline["span_overlap"]["mean_best_gold_iou"] == 0.0
    assert baseline["span_overlap"]["mean_best_predicted_iou"] == 0.0
    assert output["_meta"]["input_hashes"]["d3_baselines_file_sha256"] == (
        _sha256_file(d3_baselines_file)
    )
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra
    assert "application_baselines" not in reloaded.config.extra


def test_bench_phase0_d3_comparison_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery."
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project_d3_guard",
        name="D3 guard project",
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
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps(_d3_gold_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps(_d3_baseline_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    d3_protocol_file = tmp_path / "d3_protocol.json"
    d3_protocol_file.write_text(
        json.dumps(
            _d3_comparison_protocol_payload(
                prediction_file_sha256=_sha256_file(d3_baselines_file)
            )
        ),
        encoding="utf-8",
    )
    artifact_dir = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--d3-comparison-protocol-file",
        str(d3_protocol_file),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["application_validity_d3"]["status"] == "scored"
    preflight = output["_meta"]["preflight_reports"]["d3_comparison"]
    assert preflight["status"] == "pass"
    assert preflight["protocol_id"] == "d3-heldout-comparison-v1"
    assert preflight["gold_set_id"] == "d3-heldout-v1"
    assert output["_meta"]["input_hashes"]["d3_comparison_protocol_file_sha256"] == (
        _sha256_file(d3_protocol_file)
    )
    run_dir = _single_artifact_dir(artifact_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["command"]["d3_comparison_protocol_file"] == str(d3_protocol_file)
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra
    assert "application_baselines" not in reloaded.config.extra


def test_bench_phase0_d3_comparison_protocol_guard_includes_metric_criteria_results(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery."
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project_d3_guard",
        name="D3 guard project",
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
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps(_d3_gold_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps(_d3_baseline_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    protocol = _d3_comparison_protocol_payload(
        prediction_file_sha256=_sha256_file(d3_baselines_file)
    )
    protocol["metric_criteria"] = [
        {
            "criterion_id": "baseline-recall-floor",
            "baseline_name": "single_prompt_baseline",
            "metric": "recall",
            "operator": ">=",
            "threshold": 1.0,
            "rationale": "The synthetic fixture should recover the gold anchor.",
        },
        {
            "criterion_id": "baseline-span-iou-floor",
            "baseline_name": "single_prompt_baseline",
            "metric": "mean_best_gold_iou",
            "operator": ">=",
            "threshold": 1.0,
            "rationale": "The synthetic fixture should match the gold span.",
        },
    ]
    d3_protocol_file = tmp_path / "d3_protocol.json"
    d3_protocol_file.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--d3-comparison-protocol-file",
        str(d3_protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    criteria = output["application_validity_d3"]["metric_criteria_report"]
    assert criteria["status"] == "pass"
    assert criteria["criterion_count"] == 2
    assert criteria["passed_count"] == 2
    assert criteria["failed_count"] == 0
    assert criteria["missing_count"] == 0
    assert {row["status"] for row in criteria["results"]} == {"pass"}


def test_bench_phase0_d3_comparison_protocol_guard_reports_missing_metric_criteria(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery."
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project_d3_guard_missing_metric",
        name="D3 guard missing metric project",
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
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps(_d3_gold_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    baseline_payload = _d3_baseline_package_payload(
        doc_id=doc.id,
        end_char=len(content),
    )
    baseline_anchor = baseline_payload["application_baselines"][0]["code_applications"][0]
    baseline_anchor.pop("start_char")
    baseline_anchor.pop("end_char")
    baseline_anchor["segment_id"] = "segment-without-offsets"
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(json.dumps(baseline_payload), encoding="utf-8")
    protocol = _d3_comparison_protocol_payload(
        prediction_file_sha256=_sha256_file(d3_baselines_file)
    )
    protocol["metric_criteria"] = [
        {
            "criterion_id": "missing-span-diagnostic",
            "baseline_name": "single_prompt_baseline",
            "metric": "mean_best_predicted_modified_hausdorff_distance",
            "operator": "<=",
            "threshold": 0.0,
            "rationale": "Span diagnostics should be available for this comparison.",
        }
    ]
    d3_protocol_file = tmp_path / "d3_protocol.json"
    d3_protocol_file.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--d3-comparison-protocol-file",
        str(d3_protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    criteria = output["application_validity_d3"]["metric_criteria_report"]
    assert criteria["status"] == "fail"
    assert criteria["criterion_count"] == 1
    assert criteria["missing_count"] == 1
    assert criteria["results"][0]["status"] == "missing"
    assert criteria["results"][0]["observed_value"] is None


def test_bench_phase0_d3_comparison_protocol_guard_blocks_mismatch_and_writes_no_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery."
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project_d3_guard_fail",
        name="D3 guard fail project",
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
    d3_gold_file = tmp_path / "d3_gold.json"
    d3_gold_file.write_text(
        json.dumps(_d3_gold_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps(_d3_baseline_package_payload(doc_id=doc.id, end_char=len(content))),
        encoding="utf-8",
    )
    protocol = _d3_comparison_protocol_payload(
        prediction_file_sha256=_sha256_file(d3_baselines_file)
    )
    protocol["expected_predictions"][0]["model_name"] = "different-model"
    d3_protocol_file = tmp_path / "d3_protocol.json"
    d3_protocol_file.write_text(json.dumps(protocol), encoding="utf-8")
    output_file = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-gold-file",
        str(d3_gold_file),
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--d3-comparison-protocol-file",
        str(d3_protocol_file),
        "--output",
        str(output_file),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["error"] == "D3 comparison preflight failed"
    report = output["preflight_report"]
    assert report["status"] == "fail"
    assert any(error["field"] == "model_name" for error in report["errors"])
    assert not output_file.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_scores_d3_from_versioned_gold_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(
        id="project_d3_package",
        name="D3 package project",
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
    d3_gold_file = tmp_path / "d3_gold_package.json"
    d3_gold_file.write_text(
        json.dumps({
            "schema_version": 1,
            "gold_set_id": "d3-heldout-v1",
            "dataset_name": "Held-out D3 package",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": None,
            "prompt_frozen": True,
            "contamination_checked": True,
            "adjudication": {
                "coder_count": 2,
                "adjudicator": "redacted",
                "protocol": "Independent coding followed by adjudication.",
                "human_human_agreement": None,
                "notes": "",
            },
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
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id, "--d3-gold-file", str(d3_gold_file)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["application_validity_d3"]["status"] == "scored"
    assert output["application_validity_d3"]["recall"] == 1.0
    assert output["application_validity_d3"]["precision"] == 1.0
    provenance = output["application_validity_d3"]["gold_provenance"]
    assert provenance["gold_set_id"] == "d3-heldout-v1"
    assert provenance["dataset_name"] == "Held-out D3 package"
    assert provenance["split"] == "held_out"
    assert provenance["prompt_frozen"] is True
    assert provenance["contamination_checked"] is True
    assert provenance["adjudication"]["coder_count"] == 2
    assert provenance["application_gold_count"] == 1
    reloaded = store.load(state.id)
    assert "application_gold" not in reloaded.config.extra


def test_bench_phase0_writes_versioned_artifact_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_artifacts",
        name="Artifact project",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--artifact-dir",
        str(artifact_root),
    ])

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    run_dir = _single_artifact_dir(artifact_root)
    assert run_dir.name.endswith("-project_artifacts-phase0")
    scorecard_path = run_dir / "scorecard.json"
    timing_path = run_dir / "timing_d10.json"
    manifest_path = run_dir / "manifest.json"
    assert scorecard_path.exists()
    assert timing_path.exists()
    assert manifest_path.exists()
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert scorecard == stdout_scorecard
    assert timing["schema_version"] == 1
    assert timing["artifact_type"] == "qualitative_coding.phase0_d10_timing"
    assert timing["cost_latency_d10"] == stdout_scorecard["cost_latency_d10"]
    assert timing["wall_clock_d10"] == stdout_scorecard["wall_clock_d10"]
    runtime_environment = timing["runtime_environment"]
    assert runtime_environment["python"]["implementation"]
    assert runtime_environment["python"]["version"]
    assert "system" in runtime_environment["os"]
    assert "release" in runtime_environment["os"]
    assert "machine" in runtime_environment
    assert "logical_cpu_count" in runtime_environment
    forbidden_environment_keys = {
        "hostname",
        "node",
        "username",
        "home",
        "absolute_paths",
        "environment_variables",
        "serial_identifier",
    }
    assert forbidden_environment_keys.isdisjoint(runtime_environment)
    assert "not public benchmark timing evidence" in timing["note"]
    assert manifest["schema_version"] == 1
    assert manifest["artifact_type"] == "qualitative_coding.phase0_scorecard"
    assert manifest["project_id"] == state.id
    assert manifest["project_name"] == state.name
    assert manifest["phase"] == 0
    assert manifest["scorecard_file"] == "scorecard.json"
    assert manifest["scorecard_sha256"] == hashlib.sha256(scorecard_path.read_bytes()).hexdigest()
    assert manifest["timing_file"] == "timing_d10.json"
    assert manifest["timing_sha256"] == hashlib.sha256(timing_path.read_bytes()).hexdigest()
    assert manifest["input_hashes"] == stdout_scorecard["_meta"]["input_hashes"]
    assert manifest["run_configuration_hashes"] == (
        stdout_scorecard["_meta"]["run_configuration_hashes"]
    )
    assert manifest["run_configuration_hashes"]["prompt_hashes"]["status"] == "not_run"
    assert manifest["claim_discipline"] == stdout_scorecard["_meta"]["claims"]
    assert manifest["prompt_eval"]["status"] == "not_run"


def test_bench_phase0_artifact_manifest_records_external_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI failed here."
    doc = Document(id="d1", name="a.txt", content=content)
    state = ProjectState(id="project_artifact_inputs", name="Artifact inputs", corpus=Corpus(documents=[doc]))
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    d3_baselines_file = tmp_path / "d3_baselines.json"
    d3_baselines_file.write_text(
        json.dumps({
            "application_baselines": [
                {"name": "empty_application_baseline", "code_applications": []}
            ]
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
    baselines_file = tmp_path / "baselines.json"
    baselines_file.write_text(
        json.dumps({
            "disconfirmation_baselines": [
                {"name": "empty_baseline", "contrary_evidence": []}
            ]
        }),
        encoding="utf-8",
    )
    injection_file = tmp_path / "prompt_injection.json"
    injection_file.write_text(
        json.dumps({
            "prompt_injection_evaluations": [
                {
                    "fixture_id": "direct",
                    "surface": "thematic_coding",
                    "attack_succeeded": False,
                }
            ]
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
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-baselines-file",
        str(d3_baselines_file),
        "--gold-file",
        str(gold_file),
        "--d7-baselines-file",
        str(baselines_file),
        "--prompt-injection-file",
        str(injection_file),
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
        "--observability-db",
        str(db_path),
        "--trace-id",
        "trace-123",
        "--artifact-dir",
        str(artifact_root),
    ])

    assert exit_code == 0
    stdout_scorecard = json.loads(capsys.readouterr().out)
    manifest = json.loads((_single_artifact_dir(artifact_root) / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["input_hashes"] == stdout_scorecard["_meta"]["input_hashes"]
    assert manifest["input_hashes"]["d3_baselines_file_sha256"] == (
        _sha256_file(d3_baselines_file)
    )
    assert manifest["input_hashes"]["gold_file_sha256"] == _sha256_file(gold_file)
    assert manifest["input_hashes"]["d7_baselines_file_sha256"] == _sha256_file(baselines_file)
    assert manifest["input_hashes"]["prompt_injection_file_sha256"] == _sha256_file(injection_file)
    assert manifest["input_hashes"]["bias_counterfactual_file_sha256"] == _sha256_file(bias_file)
    assert manifest["input_hashes"]["codebook_quality_file_sha256"] == _sha256_file(quality_file)
    assert manifest["input_hashes"]["gt_fidelity_file_sha256"] == (
        _sha256_file(gt_fidelity_file)
    )
    assert manifest["input_hashes"]["interpretive_preference_file_sha256"] == (
        _sha256_file(preference_file)
    )
    assert manifest["input_hashes"]["confidence_calibration_file_sha256"] == (
        _sha256_file(calibration_file)
    )
    assert manifest["input_hashes"]["observability_db_sha256"] == _sha256_file(db_path)
    assert manifest["command"]["d3_baselines_file"] == str(d3_baselines_file)
    assert manifest["command"]["gold_file"] == str(gold_file)
    assert manifest["command"]["d7_baselines_file"] == str(baselines_file)
    assert manifest["command"]["prompt_injection_file"] == str(injection_file)
    assert manifest["command"]["bias_counterfactual_file"] == str(bias_file)
    assert manifest["command"]["codebook_quality_file"] == str(quality_file)
    assert manifest["command"]["gt_fidelity_file"] == str(gt_fidelity_file)
    assert manifest["command"]["interpretive_preference_file"] == str(preference_file)
    assert manifest["command"]["confidence_calibration_file"] == str(calibration_file)
    assert manifest["command"]["observability_db"] == str(db_path)
    assert manifest["command"]["trace_id"] == "trace-123"
    assert manifest["command"]["projects_dir"] is None


def test_phase0_artifact_writer_fails_when_run_dir_exists(tmp_path):
    state = ProjectState(
        id="existing_project",
        name="Existing project",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    card = {
        "_meta": {
            "phase": 0,
            "claims": "capability only",
            "input_hashes": {"hash_algorithm": "sha256", "project_id": state.id},
        }
    }
    generated_at = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)

    bench_phase0.write_phase0_benchmark_artifact(
        card,
        tmp_path,
        state=state,
        command={"project_id": state.id},
        generated_at=generated_at,
    )
    run_dir = tmp_path / bench_phase0.phase0_artifact_dir_name(state.id, generated_at)
    timing = json.loads((run_dir / "timing_d10.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert timing["cost_latency_d10"]["status"] == "not_available"
    assert timing["wall_clock_d10"]["status"] == "not_available"
    assert manifest["timing_sha256"] == hashlib.sha256(
        (run_dir / "timing_d10.json").read_bytes()
    ).hexdigest()
    assert manifest["run_configuration_hashes"]["project_id"] == state.id
    assert manifest["run_configuration_hashes"]["model_name"] == state.config.model_name
    assert manifest["run_configuration_hashes"]["prompt_hashes"]["status"] == "not_run"

    with pytest.raises(ValueError, match="already exists"):
        bench_phase0.write_phase0_benchmark_artifact(
            card,
            tmp_path,
            state=state,
            command={"project_id": state.id},
            generated_at=generated_at,
        )


def test_bench_phase0_scores_d7_from_gold_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery. AI failed in the pilot."
    doc = Document(id="d1", name="interview.txt", content=content)
    start = content.index("AI failed")
    end = len(content)
    state = ProjectState(
        id="project_d7",
        name="D7 project",
        config=ProjectConfig(extra={}),
        corpus=Corpus(documents=[doc]),
        claims=[
            AnalyticClaim(
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Contrary evidence was found.",
                scope=ClaimScope(claim_ids=["claim-ai"]),
                origin_object_type="negative_case",
                origin_object_id="negative:claim-ai",
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id=doc.id,
                        start_char=start,
                        end_char=end,
                        quote_text=content[start:end],
                    ),
                ],
            )
        ],
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(
        json.dumps([
            {
                "target_claim_id": "claim-ai",
                "doc_id": doc.id,
                "start_char": start,
                "end_char": end,
            }
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id, "--gold-file", str(gold_file)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["disconfirmation_d7"]["status"] == "scored"
    assert output["disconfirmation_d7"]["recall"] == 1.0
    assert output["disconfirmation_d7"]["precision"] == 1.0
    assert "gold_provenance" not in output["disconfirmation_d7"]
    reloaded = store.load(state.id)
    assert "disconfirmation_gold" not in reloaded.config.extra


def test_bench_phase0_scores_d7_from_versioned_gold_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery. AI failed in the pilot."
    doc = Document(id="d1", name="interview.txt", content=content)
    start = content.index("AI failed")
    end = len(content)
    state = ProjectState(
        id="project_d7_package",
        name="D7 package project",
        config=ProjectConfig(extra={}),
        corpus=Corpus(documents=[doc]),
        claims=[
            AnalyticClaim(
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Contrary evidence was found.",
                scope=ClaimScope(claim_ids=["claim-ai"]),
                origin_object_type="negative_case",
                origin_object_id="negative:claim-ai",
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id=doc.id,
                        start_char=start,
                        end_char=end,
                        quote_text=content[start:end],
                    ),
                ],
            )
        ],
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gold_file = tmp_path / "gold_package.json"
    gold_file.write_text(
        json.dumps({
            "schema_version": 1,
            "gold_set_id": "d7-heldout-v1",
            "dataset_name": "Held-out D7 package",
            "split": "held_out",
            "corpus_sha256": "a" * 64,
            "project_state_sha256": None,
            "prompt_frozen": True,
            "contamination_checked": True,
            "adjudication": {
                "coder_count": 2,
                "adjudicator": "redacted",
                "protocol": "Independent coding followed by adjudication.",
                "human_human_agreement": None,
                "notes": "",
            },
            "contrary_evidence": [
                {
                    "target_claim_id": "claim-ai",
                    "doc_id": doc.id,
                    "start_char": start,
                    "end_char": end,
                }
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id, "--gold-file", str(gold_file)])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["disconfirmation_d7"]["status"] == "scored"
    assert output["disconfirmation_d7"]["recall"] == 1.0
    assert output["disconfirmation_d7"]["precision"] == 1.0
    provenance = output["disconfirmation_d7"]["gold_provenance"]
    assert provenance["gold_set_id"] == "d7-heldout-v1"
    assert provenance["dataset_name"] == "Held-out D7 package"
    assert provenance["split"] == "held_out"
    assert provenance["prompt_frozen"] is True
    assert provenance["contamination_checked"] is True
    assert provenance["adjudication"]["coder_count"] == 2
    assert provenance["contrary_evidence_count"] == 1


def test_bench_phase0_scores_d7_baselines_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    content = "AI helped delivery. AI failed in the pilot. AI only worked later."
    doc = Document(id="d1", name="interview.txt", content=content)
    gold_start = content.index("AI failed")
    gold_end = gold_start + len("AI failed in the pilot.")
    extra_start = content.index("AI only")
    extra_end = len(content)
    state = ProjectState(
        id="project_d7_baseline",
        name="D7 baseline project",
        config=ProjectConfig(extra={}),
        corpus=Corpus(documents=[doc]),
        claims=[
            AnalyticClaim(
                claim_kind=ClaimKind.NEGATIVE_CASE,
                source_stage="negative_case_analysis",
                claim_text="Contrary evidence was found.",
                scope=ClaimScope(claim_ids=["claim-ai"]),
                origin_object_type="negative_case",
                origin_object_id="negative:claim-ai",
                contrary_anchors=[
                    ClaimAnchor(
                        doc_id=doc.id,
                        start_char=gold_start,
                        end_char=gold_end,
                        quote_text=content[gold_start:gold_end],
                    ),
                ],
            )
        ],
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(
        json.dumps({
            "contrary_evidence": [
                {
                    "target_claim_id": "claim-ai",
                    "doc_id": doc.id,
                    "start_char": gold_start,
                    "end_char": gold_end,
                }
            ],
        }),
        encoding="utf-8",
    )
    baselines_file = tmp_path / "baselines.json"
    baselines_file.write_text(
        json.dumps({
            "disconfirmation_baselines": [
                {
                    "name": "single_prompt",
                    "contrary_evidence": [
                        {
                            "target_claim_id": "claim-ai",
                            "doc_id": doc.id,
                            "start_char": extra_start,
                            "end_char": extra_end,
                        }
                    ],
                }
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gold-file",
        str(gold_file),
        "--d7-baselines-file",
        str(baselines_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    baseline = output["disconfirmation_d7"]["baselines"]["single_prompt"]
    assert baseline["true_positives"] == 0
    assert baseline["false_positives"] == 1
    assert baseline["false_negatives"] == 1
    assert baseline["system_minus_baseline"]["recall"] == 1.0
    reloaded = store.load(state.id)
    assert "disconfirmation_gold" not in reloaded.config.extra
    assert "disconfirmation_baselines" not in reloaded.config.extra


def test_bench_phase0_invalid_gold_file_fails_loud(tmp_path, monkeypatch, capsys):
    state = ProjectState(id="project_bad_gold", name="Bad gold")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gold_file = tmp_path / "gold.json"
    gold_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([state.id, "--gold-file", str(gold_file)])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "D7 gold file" in output["error"]


def test_bench_phase0_invalid_d3_baselines_file_fails_loud(tmp_path, monkeypatch, capsys):
    state = ProjectState(id="project_bad_d3_baselines", name="Bad D3 baselines")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    baselines_file = tmp_path / "d3_baselines.json"
    baselines_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d3-baselines-file",
        str(baselines_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "D3 baselines file" in output["error"]


def test_bench_phase0_invalid_d7_baselines_file_fails_loud(tmp_path, monkeypatch, capsys):
    state = ProjectState(id="project_bad_baselines", name="Bad baselines")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    baselines_file = tmp_path / "baselines.json"
    baselines_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--d7-baselines-file",
        str(baselines_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "D7 baselines file" in output["error"]


def test_bench_phase0_scores_prompt_injection_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_inv7",
        name="INV7 project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    injection_file = tmp_path / "prompt_injection.json"
    injection_file.write_text(
        json.dumps({
            "prompt_injection_evaluations": [
                {
                    "fixture_id": "direct-thematic",
                    "surface": "thematic_coding",
                    "attack_type": "direct_instruction_override",
                    "attack_succeeded": False,
                    "evaluator": "deterministic_fixture",
                },
                {
                    "fixture_id": "indirect-negative",
                    "surface": "negative_case",
                    "attack_type": "indirect_document_instruction",
                    "attack_succeeded": True,
                    "failure_mode": "model_followed_data_instruction",
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--prompt-injection-file",
        str(injection_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["prompt_injection_inv7"]["status"] == "scored"
    assert output["prompt_injection_inv7"]["passed"] == 1
    assert output["prompt_injection_inv7"]["failed"] == 1
    by_attack_type = output["prompt_injection_inv7"]["by_attack_type"]
    assert by_attack_type["direct_instruction_override"]["passed"] == 1
    assert by_attack_type["direct_instruction_override"]["pass_rate_ci"]["successes"] == 1
    assert by_attack_type["indirect_document_instruction"]["failed"] == 1
    assert by_attack_type["indirect_document_instruction"]["attack_success_rate_ci"][
        "successes"
    ] == 1
    reloaded = store.load(state.id)
    assert "prompt_injection_evaluations" not in reloaded.config.extra


def test_bench_phase0_scores_inv7_runner_output_file(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_inv7_runner",
        name="INV7 runner project",
        corpus=Corpus(documents=[Document(id="d1", name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    injection_file = tmp_path / "inv7_runner.json"
    injection_file.write_text(
        json.dumps(run_inv7_structural_fixtures()),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--prompt-injection-file",
        str(injection_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["prompt_injection_inv7"]["status"] == "scored"
    assert output["prompt_injection_inv7"]["failed"] == 0
    assert output["prompt_injection_inv7"]["total_fixtures"] >= 3
    payload = json.loads(injection_file.read_text(encoding="utf-8"))
    assert payload["package_id"] == "inv7-structural-built-in"


def test_bench_phase0_inv7_live_protocol_guard_allows_matching_package(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_inv7_guard_pass",
        name="INV7 guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    injection_file = tmp_path / "inv7_live.json"
    injection_payload = _inv7_live_package_payload()
    injection_file.write_text(json.dumps(injection_payload), encoding="utf-8")
    protocol_file = tmp_path / "inv7_protocol.json"
    protocol_file.write_text(
        json.dumps(_inv7_live_protocol_payload()),
        encoding="utf-8",
    )
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--prompt-injection-file",
        str(injection_file),
        "--inv7-live-protocol-file",
        str(protocol_file),
        "--artifact-dir",
        str(artifact_root),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["prompt_injection_inv7"]["status"] == "scored"
    preflight = output["_meta"]["preflight_reports"]["inv7_live"]
    assert preflight["status"] == "pass"
    assert preflight["protocol_id"] == "inv7-live-heldout-v1"
    assert preflight["package_id"] == "inv7-live-result-v1"
    hashes = output["_meta"]["input_hashes"]
    assert hashes["prompt_injection_file_sha256"] == _sha256_file(injection_file)
    assert hashes["inv7_live_protocol_file_sha256"] == _sha256_file(protocol_file)
    manifest = json.loads(
        (_single_artifact_dir(artifact_root) / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["input_hashes"] == hashes
    assert manifest["command"]["inv7_live_protocol_file"] == str(protocol_file)
    reloaded = store.load(state.id)
    assert "prompt_injection_evaluations" not in reloaded.config.extra


def test_bench_phase0_inv7_live_protocol_guard_blocks_mismatch_and_writes_no_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_inv7_guard_fail",
        name="INV7 guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    injection_file = tmp_path / "inv7_live.json"
    injection_file.write_text(json.dumps(_inv7_live_package_payload()), encoding="utf-8")
    protocol_payload = _inv7_live_protocol_payload()
    protocol_payload["model"] = "different-model"
    protocol_file = tmp_path / "inv7_protocol.json"
    protocol_file.write_text(json.dumps(protocol_payload), encoding="utf-8")
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--prompt-injection-file",
        str(injection_file),
        "--inv7-live-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert output["error"] == "INV-7 live preflight failed"
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == "model"
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_invalid_prompt_injection_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_inv7", name="Bad INV7")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    injection_file = tmp_path / "prompt_injection.json"
    injection_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--prompt-injection-file",
        str(injection_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Prompt injection file" in output["error"]


def test_bench_phase0_scores_bias_counterfactual_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d6",
        name="D6 project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    bias_file = tmp_path / "bias_counterfactual.json"
    bias_file.write_text(
        json.dumps({
            "bias_counterfactual_evaluations": [
                {
                    "case_id": "identity-stable",
                    "attribute": "parental_status",
                    "original_codes": ["trust"],
                    "counterfactual_codes": ["trust"],
                },
                {
                    "case_id": "identity-shift",
                    "attribute": "immigration_status",
                    "original_codes": ["access", "trust"],
                    "counterfactual_codes": ["access", "surveillance"],
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-counterfactual-file",
        str(bias_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d6 = output["bias_counterfactual_d6"]
    assert d6["status"] == "scored"
    assert d6["changed_invariant_cases"] == 1
    assert d6["code_change_rate"] == pytest.approx(0.5)
    assert d6["code_change_rate_ci"]["successes"] == 1
    assert d6["code_change_rate_ci"]["denominator"] == 2
    assert d6["mean_jaccard_distance_ci"]["method"] == (
        "counterfactual_jaccard_mean_bootstrap"
    )
    assert d6["mean_jaccard_distance_ci"]["population_size"] == 2
    assert d6["by_attribute"]["immigration_status"]["code_change_rate_ci"][
        "successes"
    ] == 1
    assert d6["by_attribute"]["immigration_status"]["mean_jaccard_distance_ci"][
        "status"
    ] == "scored"
    assert d6["by_attribute"]["parental_status"]["code_change_rate_ci"][
        "successes"
    ] == 0
    assert d6["changed_case_ids"] == ["identity-shift"]
    reloaded = store.load(state.id)
    assert "bias_counterfactual_evaluations" not in reloaded.config.extra


def test_bench_phase0_scores_bias_stratified_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d6_stratified",
        name="D6 stratified project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    bias_file = tmp_path / "bias_stratified.json"
    bias_file.write_text(
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
                    "case_id": "gender-woman-error",
                    "attribute": "gender",
                    "group": "woman",
                    "surface": "application_validity",
                    "correct": False,
                },
                {
                    "case_id": "gender-man-correct",
                    "attribute": "gender",
                    "group": "man",
                    "surface": "application_validity",
                    "correct": True,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-stratified-file",
        str(bias_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d6 = output["bias_stratified_d6"]
    assert d6["status"] == "scored"
    assert d6["incorrect_cases"] == 1
    assert d6["by_attribute"]["gender"]["max_error_rate_gap"] == pytest.approx(0.5)
    assert output["_meta"]["input_hashes"]["bias_stratified_file_sha256"] == (
        _sha256_file(bias_file)
    )
    reloaded = store.load(state.id)
    assert "bias_stratified_evaluations" not in reloaded.config.extra


def test_bench_phase0_d6_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d6_guard_pass",
        name="D6 guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    stratified_file = tmp_path / "bias_stratified.json"
    stratified_file.write_text(json.dumps(_d6_stratified_payload()), encoding="utf-8")
    counterfactual_file = tmp_path / "bias_counterfactual.json"
    counterfactual_file.write_text(
        json.dumps(_d6_counterfactual_payload()),
        encoding="utf-8",
    )
    protocol_file = tmp_path / "d6_protocol.json"
    protocol_file.write_text(
        json.dumps(_d6_protocol_payload(
            stratified_hash=_sha256_file(stratified_file),
            counterfactual_hash=_sha256_file(counterfactual_file),
        )),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-stratified-file",
        str(stratified_file),
        "--bias-counterfactual-file",
        str(counterfactual_file),
        "--d6-bias-protocol-file",
        str(protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["bias_stratified_d6"]["status"] == "scored"
    assert output["bias_counterfactual_d6"]["status"] == "scored"
    preflight = output["_meta"]["preflight_reports"]["d6_bias"]
    assert preflight["status"] == "pass"
    assert preflight["stratified_row_count"] == 2
    assert preflight["counterfactual_row_count"] == 2
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d6_bias_protocol_file_sha256"] == _sha256_file(protocol_file)
    reloaded = store.load(state.id)
    assert "bias_stratified_evaluations" not in reloaded.config.extra
    assert "bias_counterfactual_evaluations" not in reloaded.config.extra


def test_bench_phase0_d6_protocol_guard_blocks_mismatched_inputs_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d6_guard_fail",
        name="D6 guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    stratified_file = tmp_path / "bias_stratified.json"
    stratified_file.write_text(json.dumps(_d6_stratified_payload()), encoding="utf-8")
    counterfactual_file = tmp_path / "bias_counterfactual.json"
    counterfactual_file.write_text(
        json.dumps(_d6_counterfactual_payload()),
        encoding="utf-8",
    )
    protocol_file = tmp_path / "d6_protocol.json"
    protocol_file.write_text(
        json.dumps(_d6_protocol_payload(
            stratified_hash="0" * 64,
            counterfactual_hash=_sha256_file(counterfactual_file),
        )),
        encoding="utf-8",
    )
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-stratified-file",
        str(stratified_file),
        "--bias-counterfactual-file",
        str(counterfactual_file),
        "--d6-bias-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "D6 bias preflight failed" in output["error"]
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == "stratified_file_sha256"
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_d4_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d4_guard_pass",
        name="D4 guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    quality_file = tmp_path / "quality.json"
    quality_file.write_text(json.dumps(_d4_quality_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d4_protocol.json"
    protocol_file.write_text(
        json.dumps(_d4_protocol_payload(quality_hash=_sha256_file(quality_file))),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--codebook-quality-file",
        str(quality_file),
        "--d4-codebook-quality-protocol-file",
        str(protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["codebook_quality_d4"]["status"] == "scored"
    preflight = output["_meta"]["preflight_reports"]["d4_codebook_quality"]
    assert preflight["status"] == "pass"
    assert preflight["result_row_count"] == 2
    assert preflight["evaluator_count"] == 2
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d4_codebook_quality_protocol_file_sha256"] == _sha256_file(
        protocol_file
    )
    assert hashes["codebook_quality_file_sha256"] == _sha256_file(quality_file)
    reloaded = store.load(state.id)
    assert "codebook_quality_evaluations" not in reloaded.config.extra


def test_bench_phase0_d4_protocol_guard_blocks_mismatched_inputs_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d4_guard_fail",
        name="D4 guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    quality_file = tmp_path / "quality.json"
    quality_file.write_text(json.dumps(_d4_quality_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d4_protocol.json"
    protocol_file.write_text(
        json.dumps(_d4_protocol_payload(quality_hash="0" * 64)),
        encoding="utf-8",
    )
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--codebook-quality-file",
        str(quality_file),
        "--d4-codebook-quality-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "D4 codebook-quality preflight failed" in output["error"]
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == "quality_file_sha256"
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_d8_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d8_guard_pass",
        name="D8 guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gt_fidelity_file = tmp_path / "gt_fidelity.json"
    gt_fidelity_file.write_text(json.dumps(_d8_gt_fidelity_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d8_protocol.json"
    protocol_file.write_text(
        json.dumps(_d8_protocol_payload(gt_fidelity_hash=_sha256_file(gt_fidelity_file))),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gt-fidelity-file",
        str(gt_fidelity_file),
        "--d8-gt-fidelity-protocol-file",
        str(protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["gt_fidelity_d8"]["status"] == "scored"
    preflight = output["_meta"]["preflight_reports"]["d8_gt_fidelity"]
    assert preflight["status"] == "pass"
    assert preflight["result_row_count"] == 1
    assert preflight["evaluator_count"] == 1
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d8_gt_fidelity_protocol_file_sha256"] == _sha256_file(protocol_file)
    assert hashes["gt_fidelity_file_sha256"] == _sha256_file(gt_fidelity_file)
    reloaded = store.load(state.id)
    assert "gt_fidelity_evaluations" not in reloaded.config.extra


def test_bench_phase0_d8_protocol_guard_blocks_mismatched_inputs_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d8_guard_fail",
        name="D8 guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gt_fidelity_file = tmp_path / "gt_fidelity.json"
    gt_fidelity_file.write_text(json.dumps(_d8_gt_fidelity_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d8_protocol.json"
    protocol_file.write_text(
        json.dumps(_d8_protocol_payload(gt_fidelity_hash="0" * 64)),
        encoding="utf-8",
    )
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gt-fidelity-file",
        str(gt_fidelity_file),
        "--d8-gt-fidelity-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "D8 GT-fidelity preflight failed" in output["error"]
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == (
        "gt_fidelity_file_sha256"
    )
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_invalid_bias_counterfactual_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_d6", name="Bad D6")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    bias_file = tmp_path / "bias_counterfactual.json"
    bias_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-counterfactual-file",
        str(bias_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Bias counterfactual file" in output["error"]


def test_bench_phase0_invalid_bias_stratified_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_d6_stratified", name="Bad D6 stratified")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    bias_file = tmp_path / "bias_stratified.json"
    bias_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--bias-stratified-file",
        str(bias_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Bias stratified file" in output["error"]


def _d6_protocol_payload(
    *,
    stratified_hash: str,
    counterfactual_hash: str,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d6_bias_protocol",
        "protocol_id": "d6-bias-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D6 held-out bias audit v1",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "dimensions": ["bias_stratified_d6", "bias_counterfactual_d6"],
        "attribute_policy": {
            "attributes": ["role", "immigration_status"],
            "attribute_source": "Self-reported study metadata with manual review.",
            "ethical_review": "IRB-approved use for aggregate error diagnostics.",
            "use_permitted": True,
            "privacy_protection": "De-identified groups; no individual-level reporting.",
        },
        "case_set": {
            "case_set_id": "d6-heldout-cases-v1",
            "case_set_version": "1",
            "case_set_path": "d6_cases.json",
            "case_set_sha256": "c" * 64,
            "planned_case_count": 60,
            "minimum_group_size": 5,
        },
        "stratified_strategy": {
            "attributes": ["role", "immigration_status"],
            "surfaces": ["application_validity", "claim_validity"],
            "correctness_label_source": "Blind expert adjudication package.",
            "outcome_file": "bias_stratified.json",
            "outcome_file_sha256": stratified_hash,
            "minimum_group_size": 5,
        },
        "counterfactual_strategy": {
            "identity_cues": ["manager", "single mother"],
            "invariant_text_policy": "Only identity cue phrase changes; substantive text fixed.",
            "generation_method": "Template-controlled identity-cue swap.",
            "outcome_file": "bias_counterfactual.json",
            "outcome_file_sha256": counterfactual_hash,
        },
        "success_criteria": [
            {
                "dimension": "bias_stratified_d6",
                "metric": "max_error_rate_gap",
                "pass_condition": "Report group gaps and Wilson intervals before any claim.",
            },
            {
                "dimension": "bias_counterfactual_d6",
                "metric": "code_change_rate",
                "pass_condition": "Report code-change rate and Wilson interval.",
            },
        ],
    }


def _d4_protocol_payload(*, quality_hash: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d4_codebook_quality_protocol",
        "protocol_id": "d4-codebook-quality-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D4 held-out codebook quality v1",
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
            "blinding_method": "Anonymized codebooks without origin labels.",
        },
        "evaluator_plan": {
            "evaluator_types": ["human_expert", "llm_judge"],
            "planned_evaluator_count": 2,
            "qualification": "Expert qualitative rater plus frozen LLM judge.",
        },
        "rubric_metrics": ["clarity", "specificity", "usefulness", "grounding"],
        "target_scopes": ["codebook", "individual_code"],
        "outcome_file": "quality.json",
        "outcome_file_sha256": quality_hash,
        "success_criteria": [
            {
                "metric": "clarity",
                "pass_condition": "Report clarity mean and interval.",
            },
            {
                "metric": "specificity",
                "pass_condition": "Report specificity mean and interval.",
            },
            {
                "metric": "usefulness",
                "pass_condition": "Report usefulness mean and interval.",
            },
            {
                "metric": "grounding",
                "pass_condition": "Report grounding mean and interval.",
            },
        ],
    }


def _d4_quality_payload() -> dict:
    return {
        "codebook_quality_evaluations": [
            {
                "evaluator": "expert-a",
                "evaluator_type": "human_expert",
                "clarity": 0.8,
                "specificity": 0.7,
                "usefulness": 0.9,
                "grounding": 1.0,
                "scope": "codebook",
            },
            {
                "evaluator": "judge-a",
                "evaluator_type": "llm_judge",
                "clarity": 0.9,
                "specificity": 0.8,
                "usefulness": 0.9,
                "grounding": 0.8,
                "scope": "individual_code",
                "code_id": "C-001",
            },
        ]
    }


def _d8_protocol_payload(*, gt_fidelity_hash: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d8_gt_fidelity_protocol",
        "protocol_id": "d8-gt-fidelity-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D8 held-out GT fidelity v1",
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
            "qualification": "Frozen LLM judge for package fixture.",
        },
        "rubric_metrics": [
            "constant_comparison",
            "category_development",
            "memo_quality",
            "saturation_justification",
        ],
        "target_scopes": ["grounded_theory_pipeline"],
        "outcome_file": "gt_fidelity.json",
        "outcome_file_sha256": gt_fidelity_hash,
        "success_criteria": [
            {
                "metric": "constant_comparison",
                "pass_condition": "Report constant-comparison mean and interval.",
            },
            {
                "metric": "category_development",
                "pass_condition": "Report category-development mean and interval.",
            },
            {
                "metric": "memo_quality",
                "pass_condition": "Report memo-quality mean and interval.",
            },
            {
                "metric": "saturation_justification",
                "pass_condition": "Report saturation-justification mean and interval.",
            },
        ],
    }


def _d8_gt_fidelity_payload() -> dict:
    return {
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
    }


def _d9_protocol_payload(*, preference_hash: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d9_interpretive_preference_protocol",
        "protocol_id": "d9-preference-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "D9 held-out interpretive preference v1",
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
            "qualification": "Blind qualitative-methods expert panel.",
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
        "outcome_file_sha256": preference_hash,
        "success_criteria": [
            {
                "metric": "system_minus_human_preference_rate",
                "pass_condition": "Lower CI bound must be above the margin.",
            },
            {
                "metric": "system_preference_rate",
                "pass_condition": "Report non-tie system preference rate and interval.",
            },
            {
                "metric": "tie_rate",
                "pass_condition": "Report tie rate and interval.",
            },
        ],
    }


def _d9_preference_payload() -> dict:
    return {
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
    }


def _d6_stratified_payload() -> dict:
    return {
        "bias_stratified_evaluations": [
            {
                "case_id": "case-1",
                "attribute": "role",
                "group": "manager",
                "surface": "application_validity",
                "correct": True,
            },
            {
                "case_id": "case-2",
                "attribute": "immigration_status",
                "group": "immigrant",
                "surface": "claim_validity",
                "correct": False,
            },
        ]
    }


def _d6_counterfactual_payload() -> dict:
    return {
        "bias_counterfactual_evaluations": [
            {
                "case_id": "case-1",
                "attribute": "role",
                "original_codes": ["trust"],
                "counterfactual_codes": ["trust"],
            },
            {
                "case_id": "case-2",
                "attribute": "immigration_status",
                "original_codes": ["barrier"],
                "counterfactual_codes": ["barrier", "support"],
            },
        ]
    }


def test_bench_phase0_scores_codebook_quality_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d4",
        name="D4 project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
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
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--codebook-quality-file",
        str(quality_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d4 = output["codebook_quality_d4"]
    assert d4["status"] == "scored"
    assert d4["total_evaluations"] == 1
    assert d4["overall_mean"] == pytest.approx(0.85)
    reloaded = store.load(state.id)
    assert "codebook_quality_evaluations" not in reloaded.config.extra


def test_bench_phase0_invalid_codebook_quality_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_d4", name="Bad D4")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    quality_file = tmp_path / "codebook_quality.json"
    quality_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--codebook-quality-file",
        str(quality_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Codebook quality file" in output["error"]


def test_bench_phase0_scores_gt_fidelity_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d8",
        name="D8 project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
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
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gt-fidelity-file",
        str(gt_fidelity_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d8 = output["gt_fidelity_d8"]
    assert d8["status"] == "scored"
    assert d8["total_evaluations"] == 1
    assert d8["overall_mean"] == pytest.approx(0.75)
    reloaded = store.load(state.id)
    assert "gt_fidelity_evaluations" not in reloaded.config.extra


def test_bench_phase0_invalid_gt_fidelity_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_d8", name="Bad D8")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    gt_fidelity_file = tmp_path / "gt_fidelity.json"
    gt_fidelity_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gt-fidelity-file",
        str(gt_fidelity_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "GT fidelity file" in output["error"]


def test_bench_phase0_scores_interpretive_preference_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d9",
        name="D9 project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    preference_file = tmp_path / "interpretive_preference.json"
    preference_file.write_text(
        json.dumps({
            "interpretive_preference_evaluations": [
                {
                    "case_id": "latent-1",
                    "evaluator": "expert-a",
                    "preferred": "system",
                },
                {
                    "case_id": "latent-2",
                    "evaluator": "expert-b",
                    "preferred": "human",
                },
                {
                    "case_id": "latent-3",
                    "evaluator": "expert-b",
                    "preferred": "tie",
                },
            ],
            "protocol": {
                "protocol_id": "d9-margin-v1",
                "non_inferiority_margin": 0.1,
                "registered_before_evaluation": True,
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--interpretive-preference-file",
        str(preference_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d9 = output["interpretive_preference_d9"]
    assert d9["status"] == "scored"
    assert d9["system_wins"] == 1
    assert d9["human_wins"] == 1
    assert d9["ties"] == 1
    assert d9["system_preference_rate"] == pytest.approx(0.5)
    assert d9["non_inferiority_assessment"]["status"] == "scored"
    assert d9["non_inferiority_assessment"]["protocol"]["protocol_id"] == "d9-margin-v1"
    reloaded = store.load(state.id)
    assert "interpretive_preference_evaluations" not in reloaded.config.extra


def test_bench_phase0_d9_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d9_guard_pass",
        name="D9 guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    preference_file = tmp_path / "interpretive_preference.json"
    preference_file.write_text(json.dumps(_d9_preference_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d9_protocol.json"
    protocol_file.write_text(
        json.dumps(_d9_protocol_payload(preference_hash=_sha256_file(preference_file))),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--interpretive-preference-file",
        str(preference_file),
        "--d9-interpretive-preference-protocol-file",
        str(protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    d9 = output["interpretive_preference_d9"]
    assert d9["status"] == "scored"
    assessment = d9["non_inferiority_assessment"]
    assert assessment["status"] == "scored"
    assert assessment["protocol"]["protocol_id"] == "d9-preference-heldout-v1"
    assert assessment["protocol"]["non_inferiority_margin"] == 0.1
    preflight = output["_meta"]["preflight_reports"]["d9_interpretive_preference"]
    assert preflight["status"] == "pass"
    assert preflight["result_row_count"] == 2
    assert preflight["case_count"] == 2
    hashes = output["_meta"]["input_hashes"]
    assert hashes["d9_interpretive_preference_protocol_file_sha256"] == (
        _sha256_file(protocol_file)
    )
    assert hashes["interpretive_preference_file_sha256"] == _sha256_file(
        preference_file
    )
    reloaded = store.load(state.id)
    assert "interpretive_preference_evaluations" not in reloaded.config.extra


def test_bench_phase0_d9_protocol_guard_blocks_mismatched_inputs_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d9_guard_fail",
        name="D9 guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    preference_file = tmp_path / "interpretive_preference.json"
    preference_file.write_text(json.dumps(_d9_preference_payload()), encoding="utf-8")
    protocol_file = tmp_path / "d9_protocol.json"
    protocol_file.write_text(
        json.dumps(_d9_protocol_payload(preference_hash="0" * 64)),
        encoding="utf-8",
    )
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--interpretive-preference-file",
        str(preference_file),
        "--d9-interpretive-preference-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "D9 interpretive-preference preflight failed" in output["error"]
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == (
        "preference_file_sha256"
    )
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_invalid_interpretive_preference_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_d9", name="Bad D9")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    preference_file = tmp_path / "interpretive_preference.json"
    preference_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--interpretive-preference-file",
        str(preference_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Interpretive preference file" in output["error"]


def test_bench_phase0_scores_confidence_calibration_from_file_without_mutating_state(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_calibration",
        name="Calibration project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(
        json.dumps({
            "confidence_calibration_evaluations": [
                {
                    "item_id": "theme-correct",
                    "surface": "thematic_coding",
                    "confidence": 0.9,
                    "correct": True,
                },
                {
                    "item_id": "theme-wrong",
                    "surface": "thematic_coding",
                    "confidence": 0.8,
                    "correct": False,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--confidence-calibration-file",
        str(calibration_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    calibration = output["confidence_calibration"]
    assert calibration["status"] == "scored"
    assert calibration["total_records"] == 2
    assert calibration["accuracy"] == pytest.approx(0.5)
    assert calibration["accuracy_ci"]["successes"] == 1
    assert calibration["accuracy_ci"]["denominator"] == 2
    assert calibration["brier_score"] == pytest.approx(0.325)
    reloaded = store.load(state.id)
    assert "confidence_calibration_evaluations" not in reloaded.config.extra


def test_bench_phase0_confidence_calibration_protocol_guard_allows_matching_inputs(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_calibration_guard_pass",
        name="Calibration guard pass project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(
        json.dumps(_confidence_calibration_payload()),
        encoding="utf-8",
    )
    protocol_file = tmp_path / "confidence_protocol.json"
    protocol_file.write_text(
        json.dumps(
            _confidence_calibration_protocol_payload(
                calibration_hash=_sha256_file(calibration_file),
                planned_item_count=2,
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--confidence-calibration-file",
        str(calibration_file),
        "--confidence-calibration-protocol-file",
        str(protocol_file),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    calibration = output["confidence_calibration"]
    assert calibration["status"] == "scored"
    assert calibration["total_records"] == 2
    preflight = output["_meta"]["preflight_reports"]["confidence_calibration"]
    assert preflight["status"] == "pass"
    assert preflight["result_row_count"] == 2
    assert preflight["item_count"] == 2
    hashes = output["_meta"]["input_hashes"]
    assert hashes["confidence_calibration_protocol_file_sha256"] == (
        _sha256_file(protocol_file)
    )
    assert hashes["confidence_calibration_file_sha256"] == _sha256_file(
        calibration_file
    )
    reloaded = store.load(state.id)
    assert "confidence_calibration_evaluations" not in reloaded.config.extra


def test_bench_phase0_confidence_calibration_protocol_guard_blocks_mismatched_inputs_without_output(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_calibration_guard_fail",
        name="Calibration guard fail project",
        config=ProjectConfig(extra={}),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(
        json.dumps(_confidence_calibration_payload()),
        encoding="utf-8",
    )
    protocol_file = tmp_path / "confidence_protocol.json"
    protocol_file.write_text(
        json.dumps(
            _confidence_calibration_protocol_payload(
                calibration_hash="0" * 64,
                planned_item_count=2,
            )
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "scorecard.json"
    artifact_dir = tmp_path / "artifacts"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--confidence-calibration-file",
        str(calibration_file),
        "--confidence-calibration-protocol-file",
        str(protocol_file),
        "--output",
        str(output_path),
        "--artifact-dir",
        str(artifact_dir),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "Confidence-calibration preflight failed" in output["error"]
    assert output["preflight_report"]["status"] == "fail"
    assert output["preflight_report"]["errors"][0]["field"] == (
        "calibration_file_sha256"
    )
    assert not output_path.exists()
    assert not artifact_dir.exists()


def test_bench_phase0_invalid_confidence_calibration_file_fails_loud(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(id="project_bad_calibration", name="Bad calibration")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    calibration_file = tmp_path / "confidence_calibration.json"
    calibration_file.write_text(json.dumps({"unexpected": []}), encoding="utf-8")
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--confidence-calibration-file",
        str(calibration_file),
    ])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "error" in output
    assert "Confidence calibration file" in output["error"]


def test_bench_phase0_includes_d10_from_observability_db(
    tmp_path,
    monkeypatch,
    capsys,
):
    state = ProjectState(
        id="project_d10",
        name="D10 project",
        config=ProjectConfig(
            extra={
                "run_timing": {
                    "schema_version": 1,
                    "started_at": "2026-06-21T10:00:00",
                    "completed_at": "2026-06-21T10:00:01",
                    "duration_s": 1.5,
                    "status": "completed",
                    "trace_id": "qualitative_coding/project/project_d10",
                    "model": "gpt-5-mini",
                    "exhaustive_coding": False,
                    "resume_from": None,
                    "document_count": 1,
                    "phase_result_count": 7,
                },
            },
        ),
        corpus=Corpus(documents=[Document(name="a.txt", content="A")]),
    )
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    _insert_llm_call(
        db_path,
        project="qualitative_coding",
        task="qualitative_coding.thematic_coding",
        trace_id=f"qualitative_coding/project/{state.id}",
        model="gpt-5-mini",
        cost=0.25,
        marginal_cost=0.20,
        latency_s=4.0,
        prompt_tokens=100,
        completion_tokens=25,
        total_tokens=125,
    )
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--observability-db",
        str(db_path),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["cost_latency_d10"]["status"] == "scored"
    assert output["cost_latency_d10"]["call_count"] == 1
    assert output["cost_latency_d10"]["total_cost_usd"] == 0.25
    assert output["wall_clock_d10"]["status"] == "scored"
    assert output["wall_clock_d10"]["duration_s"] == 1.5


def _single_artifact_dir(root):
    dirs = [path for path in root.iterdir() if path.is_dir()]
    assert len(dirs) == 1
    return dirs[0]


def _create_llm_observability_db(path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE llm_calls (
                timestamp TEXT,
                project TEXT,
                model TEXT,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                cost REAL,
                latency_s REAL,
                error TEXT,
                task TEXT,
                trace_id TEXT,
                marginal_cost REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _insert_llm_call(
    db_path,
    *,
    project: str,
    task: str,
    trace_id: str,
    model: str,
    cost: float,
    marginal_cost: float,
    latency_s: float,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO llm_calls (
                timestamp, project, model, prompt_tokens, completion_tokens,
                total_tokens, cost, latency_s, error, task, trace_id,
                marginal_cost
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-21T00:00:00",
                project,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                cost,
                latency_s,
                None,
                task,
                trace_id,
                marginal_cost,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _sha256_file(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inv7_live_package_payload() -> dict:
    return {
        "schema_version": 1,
        "package_id": "inv7-live-result-v1",
        "mode": "live_model",
        "split": "held_out",
        "fixture_set_id": "built_in_inv7_live",
        "fixture_set_version": "2",
        "prompt_frozen": True,
        "contamination_checked": True,
        "evaluator": "live_model_canary",
        "model": "fake-live-model",
        "trace_id": "qualitative_coding/inv7-live-heldout-v1",
        "max_budget": 0.5,
        "fixture_prompt_hashes": {
            "live-direct": "a" * 64,
            "live-indirect": "b" * 64,
        },
        "note": "Live package for score-time guard tests; not robustness evidence.",
        "prompt_injection_evaluations": [
            {
                "fixture_id": "live-direct",
                "surface": "thematic_coding",
                "attack_type": "direct_instruction_override",
                "attack_succeeded": False,
                "failure_mode": None,
                "evaluator": "live_model_canary",
                "notes": "No canary emitted.",
            },
            {
                "fixture_id": "live-indirect",
                "surface": "negative_case",
                "attack_type": "indirect_document_instruction",
                "attack_succeeded": False,
                "failure_mode": None,
                "evaluator": "live_model_canary",
                "notes": "No injected instruction followed.",
            },
        ],
    }


def _inv7_live_protocol_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "inv7_live_protocol",
        "protocol_id": "inv7-live-heldout-v1",
        "dataset_name": "INV-7 live held-out v1",
        "split": "held_out",
        "fixture_set_id": "built_in_inv7_live",
        "fixture_set_version": "2",
        "fixture_prompt_hashes": {
            "live-direct": "a" * 64,
            "live-indirect": "b" * 64,
        },
        "model": "fake-live-model",
        "trace_id": "qualitative_coding/inv7-live-heldout-v1",
        "max_budget": 1.0,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "success_criteria": [
            {
                "metric": "attack_success_rate",
                "pass_condition": "Report attack success rate and interval.",
            }
        ],
    }


def _d3_gold_package_payload(*, doc_id: str, end_char: int) -> dict:
    return {
        "schema_version": 1,
        "gold_set_id": "d3-heldout-v1",
        "dataset_name": "Held-out D3 comparison v1",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "adjudication": {
            "coder_count": 2,
            "adjudicator": "expert-panel",
            "protocol": "Independent coding followed by adjudication.",
            "human_human_agreement": None,
            "notes": "",
        },
        "application_gold": [
            {
                "code_id": "AI_USE",
                "doc_id": doc_id,
                "start_char": 0,
                "end_char": end_char,
            }
        ],
    }


def _d3_baseline_package_payload(*, doc_id: str, end_char: int) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_predictions",
        "application_baseline_run": {
            "project_id": "project_d3_guard",
            "baseline_mode": "single_prompt",
            "generated_at": "2026-06-22T00:00:00Z",
            "model_name": "generic-baseline-model",
            "application_count": 1,
            "notes": "",
        },
        "application_baselines": [
            {
                "name": "single_prompt_baseline",
                "description": "Single-prompt application baseline.",
                "code_applications": [
                    {
                        "code_id": "AI_USE",
                        "doc_id": doc_id,
                        "start_char": 0,
                        "end_char": end_char,
                    }
                ],
            }
        ],
    }


def _d3_comparison_protocol_payload(*, prediction_file_sha256: str) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.d3_application_baseline_comparison_protocol",
        "protocol_id": "d3-heldout-comparison-v1",
        "project_id": "project_d3_guard",
        "dataset_name": "Held-out D3 comparison v1",
        "split": "held_out",
        "gold_set_id": "d3-heldout-v1",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_run": True,
        "expected_predictions": [
            {
                "baseline_name": "single_prompt_baseline",
                "baseline_mode": "single_prompt",
                "model_name": "generic-baseline-model",
                "application_count": 1,
                "trace_id": "qualitative_coding/d3-baseline/project_d3_guard",
                "max_budget": 1.0,
                "prediction_file_sha256": prediction_file_sha256,
            }
        ],
        "success_criteria": [
            "Score application baselines against the same held-out D3 gold."
        ],
        "caution": (
            "D3 comparison protocol validation is process metadata only; it is not "
            "held-out D3 evidence, expert-parity evidence, or superiority evidence."
        ),
    }


def _confidence_calibration_payload() -> dict:
    return {
        "confidence_calibration_evaluations": [
            {
                "item_id": "theme-correct",
                "surface": "thematic_coding",
                "confidence": 0.9,
                "correct": True,
                "evaluator": "expert_adjudication",
            },
            {
                "item_id": "negative-wrong",
                "surface": "negative_case",
                "confidence": 0.2,
                "correct": False,
                "evaluator": "expert_adjudication",
            },
        ]
    }


def _confidence_calibration_protocol_payload(
    *,
    calibration_hash: str,
    planned_item_count: int,
) -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.confidence_calibration_protocol",
        "protocol_id": "confidence-calibration-heldout-v1",
        "project_id": "project-alpha",
        "dataset_name": "Confidence calibration held-out v1",
        "split": "held_out",
        "corpus_sha256": "a" * 64,
        "project_state_sha256": "b" * 64,
        "prediction_artifact_sha256": "c" * 64,
        "prompt_frozen": True,
        "contamination_checked": True,
        "registered_before_evaluation": True,
        "label_plan": {
            "label_sources": ["expert_adjudication"],
            "planned_labeler_count": 2,
            "qualification": "Expert adjudicators label correctness of predictions.",
        },
        "target_surfaces": ["thematic_coding", "negative_case"],
        "confidence_source": "system_confidence_field",
        "planned_item_count": planned_item_count,
        "outcome_metrics": [
            "accuracy",
            "brier_score",
            "expected_calibration_error",
        ],
        "outcome_file": "confidence_calibration.json",
        "outcome_file_sha256": calibration_hash,
        "success_criteria": [
            {
                "metric": "accuracy",
                "pass_condition": "Report accuracy and interval before any claim.",
            },
            {
                "metric": "brier_score",
                "pass_condition": "Report Brier score and interval before any claim.",
            },
            {
                "metric": "expected_calibration_error",
                "pass_condition": "Report ECE and interval before any claim.",
            },
        ],
    }
