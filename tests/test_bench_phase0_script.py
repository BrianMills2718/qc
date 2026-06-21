"""Tests for the Phase 0 bench CLI script."""

import json

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
