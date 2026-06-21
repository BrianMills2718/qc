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
    Corpus,
    Document,
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
    assert hashes["gold_file_sha256"] is None
    assert hashes["d7_baselines_file_sha256"] is None
    assert hashes["prompt_injection_file_sha256"] is None
    assert hashes["observability_db_sha256"] is None


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
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gold-file",
        str(gold_file),
        "--d7-baselines-file",
        str(baselines_file),
        "--prompt-injection-file",
        str(injection_file),
        "--observability-db",
        str(db_path),
    ])

    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)
    hashes = output["_meta"]["input_hashes"]
    assert hashes["gold_file_sha256"] == _sha256_file(gold_file)
    assert hashes["d7_baselines_file_sha256"] == _sha256_file(baselines_file)
    assert hashes["prompt_injection_file_sha256"] == _sha256_file(injection_file)
    assert hashes["observability_db_sha256"] == _sha256_file(db_path)
    reloaded = store.load(state.id)
    assert "disconfirmation_gold" not in reloaded.config.extra
    assert "disconfirmation_baselines" not in reloaded.config.extra
    assert "prompt_injection_evaluations" not in reloaded.config.extra


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
    manifest_path = run_dir / "manifest.json"
    assert scorecard_path.exists()
    assert manifest_path.exists()
    scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert scorecard == stdout_scorecard
    assert manifest["schema_version"] == 1
    assert manifest["artifact_type"] == "qualitative_coding.phase0_scorecard"
    assert manifest["project_id"] == state.id
    assert manifest["project_name"] == state.name
    assert manifest["phase"] == 0
    assert manifest["scorecard_file"] == "scorecard.json"
    assert manifest["scorecard_sha256"] == hashlib.sha256(scorecard_path.read_bytes()).hexdigest()
    assert manifest["input_hashes"] == stdout_scorecard["_meta"]["input_hashes"]
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
    db_path = tmp_path / "observability.db"
    _create_llm_observability_db(db_path)
    artifact_root = tmp_path / "benchmark_results"
    monkeypatch.setattr(bench_phase0, "ProjectStore", lambda: store)

    exit_code = bench_phase0.main([
        state.id,
        "--gold-file",
        str(gold_file),
        "--d7-baselines-file",
        str(baselines_file),
        "--prompt-injection-file",
        str(injection_file),
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
    assert manifest["input_hashes"]["gold_file_sha256"] == _sha256_file(gold_file)
    assert manifest["input_hashes"]["d7_baselines_file_sha256"] == _sha256_file(baselines_file)
    assert manifest["input_hashes"]["prompt_injection_file_sha256"] == _sha256_file(injection_file)
    assert manifest["input_hashes"]["observability_db_sha256"] == _sha256_file(db_path)
    assert manifest["command"]["gold_file"] == str(gold_file)
    assert manifest["command"]["d7_baselines_file"] == str(baselines_file)
    assert manifest["command"]["prompt_injection_file"] == str(injection_file)
    assert manifest["command"]["observability_db"] == str(db_path)
    assert manifest["command"]["trace_id"] == "trace-123"


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
