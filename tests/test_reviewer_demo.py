"""Tests for deterministic reviewer demo packet generation."""

from pathlib import Path

from qc_clean.core.persistence.project_store import ProjectStore
from scripts import build_reviewer_demo


def test_build_reviewer_demo_writes_packet(tmp_path):
    output_dir = tmp_path / "reviewer_demo"

    manifest = build_reviewer_demo.build_reviewer_demo(output_dir)

    expected = {
        "readme",
        "self_review",
        "project_state",
        "markdown_export",
        "json_export",
        "scorecard",
        "benchmark_manifest",
        "claims_snapshot",
        "patterns_snapshot",
        "abductive_snapshot",
        "review_abductive_candidates_snapshot",
        "review_claims_snapshot",
        "review_codes_snapshot",
        "graph_codes_snapshot",
    }
    assert expected.issubset(manifest)
    for key in expected:
        assert Path(manifest[key]).exists(), key

    readme = Path(manifest["readme"]).read_text(encoding="utf-8")
    self_review = Path(manifest["self_review"]).read_text(encoding="utf-8")
    markdown = Path(manifest["markdown_export"]).read_text(encoding="utf-8")

    assert "QC_PROJECTS_DIR" in readme
    assert "project patterns" in readme
    assert "project abductive" in readme
    assert "review/abductive-candidates" in readme
    assert "not methodological validity evidence" in self_review
    assert "not SOTA evidence" in self_review
    assert "Workflow Visibility" in markdown
    assert "## Observed Patterns" in markdown
    assert "## Abductive Candidate Explanations" in markdown
    assert "not causal proof" in markdown


def test_reviewer_demo_project_loads_from_env_store(tmp_path, monkeypatch):
    output_dir = tmp_path / "reviewer_demo"
    manifest = build_reviewer_demo.build_reviewer_demo(output_dir)
    monkeypatch.setenv("QC_PROJECTS_DIR", str(output_dir / "projects"))

    state = ProjectStore().load(manifest["project_id"])

    assert state.id == "reviewer-demo"
    assert state.corpus.num_documents == 2
    assert len(state.claims) >= 3
    assert len(state.observed_patterns) >= 3
    assert len(state.abductive_explanations) >= 2
    assert state.corpus_scope is not None
