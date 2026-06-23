"""Tests for the D7 retrieval export script boundary."""

from __future__ import annotations

import json

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.segmentation import segment_corpus
from qc_clean.schemas.domain import (
    AnalyticClaim,
    ClaimKind,
    ClaimScope,
    Code,
    Codebook,
    Corpus,
    Document,
    ProjectState,
)
from scripts import run_d7_retrieval


def test_run_d7_retrieval_writes_output_and_stdout(tmp_path, monkeypatch, capsys):
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    output_file = tmp_path / "retrieval_predictions.json"
    monkeypatch.setattr(run_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = run_d7_retrieval.main([
        state.id,
        "--output",
        str(output_file),
        "--name",
        "lexical_script",
        "--max-targets",
        "1",
        "--candidates-per-claim",
        "1",
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.d7_retrieval_predictions"
    assert stdout_payload["disconfirmation_baselines"][0]["name"] == "lexical_script"
    assert stdout_payload["retrieval_run"]["project_id"] == state.id
    reloaded = store.load(state.id)
    assert "disconfirmation_baselines" not in reloaded.config.extra


def test_run_d7_retrieval_accepts_projects_dir(tmp_path, capsys):
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    projects_dir = tmp_path / "portable_projects"
    store = ProjectStore(projects_dir=projects_dir)
    store.save(state)
    output_file = tmp_path / "retrieval_predictions.json"

    exit_code = run_d7_retrieval.main([
        state.id,
        "--projects-dir",
        str(projects_dir),
        "--output",
        str(output_file),
        "--max-targets",
        "1",
        "--candidates-per-claim",
        "1",
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["retrieval_run"]["project_id"] == state.id


def test_run_d7_retrieval_missing_project_returns_json_error(tmp_path, monkeypatch, capsys):
    store = ProjectStore(projects_dir=tmp_path / "projects")
    monkeypatch.setattr(run_d7_retrieval, "ProjectStore", lambda: store)

    exit_code = run_d7_retrieval.main(["missing-project"])

    assert exit_code == 1
    output = json.loads(capsys.readouterr().out)
    assert "missing-project" in output["error"]


def test_run_d7_retrieval_forwards_options_to_exporter(tmp_path, monkeypatch, capsys):
    state = _state_with_claim("AI failed badly after rollout.", "AI improves workflow.")
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    captured = {}

    def fake_export(project_state, **kwargs):
        captured["state_id"] = project_state.id
        captured["kwargs"] = kwargs
        return {
            "package_type": "qualitative_coding.d7_retrieval_predictions",
            "disconfirmation_baselines": [],
            "retrieval_run": {"project_id": project_state.id},
        }

    monkeypatch.setattr(run_d7_retrieval, "ProjectStore", lambda: store)
    monkeypatch.setattr(run_d7_retrieval, "export_d7_retrieval_baseline", fake_export)

    exit_code = run_d7_retrieval.main([
        state.id,
        "--name",
        "embedding_candidate",
        "--description",
        "Hybrid retrieval export",
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
    ])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["retrieval_run"]["project_id"] == state.id
    assert captured == {
        "state_id": state.id,
        "kwargs": {
            "name": "embedding_candidate",
            "description": "Hybrid retrieval export",
            "max_targets": 12,
            "candidates_per_claim": 7,
            "retrieval_mode": "embedding_hybrid",
            "bm25_k1": 1.4,
            "bm25_b": 0.6,
            "contrary_cue_weight": 1.8,
            "expanded_term_weight": 0.7,
            "embedding_model": "text-embedding-3-small",
            "embedding_dimensions": 256,
            "semantic_weight": 1.2,
            "min_semantic_similarity": 0.15,
            "task": "qualitative_coding.d7_retrieval_export",
            "trace_id": "trace-xyz",
            "max_budget": 2.5,
        },
    }


def _state_with_claim(content: str, claim_text: str) -> ProjectState:
    doc = Document(id="d1", name="interview.txt", content=content)
    state = ProjectState(
        id="project-d7-script",
        name="D7 retrieval script test",
        corpus=Corpus(documents=[doc]),
        codebook=Codebook(codes=[
            Code(
                id="AI_USE",
                name="AI Use",
                description="Use of AI in workflow",
            )
        ]),
        claims=[_claim(claim_text)],
    )
    state.segments = segment_corpus(state.corpus.documents)
    return state


def _claim(text: str) -> AnalyticClaim:
    return AnalyticClaim(
        id="claim-ai",
        claim_kind=ClaimKind.SYNTHESIS_FINDING,
        source_stage="synthesis",
        claim_text=text,
        scope=ClaimScope(corpus_level=True, code_ids=["AI_USE"]),
        origin_object_type="synthesis",
        origin_object_id="finding:0",
    )
