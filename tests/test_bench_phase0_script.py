"""Tests for the Phase 0 bench CLI script."""

import json
import sqlite3

from scripts import bench_phase0
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
