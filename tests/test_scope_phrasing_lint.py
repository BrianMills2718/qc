"""Tests for corpus-scope-aware report phrasing lint."""

import json

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.scope_lint import lint_scope_phrasing
from qc_clean.schemas.domain import CorpusScope, ProjectState


def test_scope_lint_allows_loaded_document_phrasing_without_scope():
    state = ProjectState(id="scope-lint", name="Scope Lint")

    report = lint_scope_phrasing(
        state,
        "In these loaded documents, AI changes workflow priorities.",
        source="memo.md",
    ).model_dump(mode="json")

    assert report["status"] == "pass"
    assert report["scope_status"] == "missing"
    assert report["warning_count"] == 0
    assert report["warnings"] == []
    assert "not sampling adequacy evidence" in report["caveat"]


def test_scope_lint_warns_on_generalization_without_scope():
    state = ProjectState(id="scope-lint", name="Scope Lint")
    text = (
        "Across operations teams, AI changes workflow priorities.\n"
        "These findings should generalize to the broader population."
    )

    report = lint_scope_phrasing(state, text, source="memo.md").model_dump(mode="json")

    assert report["status"] == "warn"
    assert report["scope_status"] == "missing"
    assert report["warning_count"] >= 2
    assert {warning["code"] for warning in report["warnings"]} == {
        "missing_corpus_scope_generalization"
    }
    assert {warning["line_number"] for warning in report["warnings"]} == {1, 2}
    assert any("Across operations teams" in warning["matched_text"] for warning in report["warnings"])
    assert any("generalize" in warning["matched_text"] for warning in report["warnings"])


def test_scope_lint_warns_on_empty_scope():
    state = ProjectState(id="scope-lint", name="Scope Lint")
    state.corpus_scope = CorpusScope()

    report = lint_scope_phrasing(
        state,
        "This is representative of teams generally.",
        source="memo.md",
    ).model_dump(mode="json")

    assert report["status"] == "warn"
    assert report["scope_status"] == "empty"
    assert report["warnings"][0]["code"] == "empty_corpus_scope_generalization"
    assert "scope record exists" in report["warnings"][0]["message"]


def test_scope_lint_warns_when_population_lacks_sampling_frame():
    state = ProjectState(id="scope-lint", name="Scope Lint")
    state.corpus_scope = CorpusScope(population="Operations teams in pilot clinics")

    report = lint_scope_phrasing(
        state,
        "Most participants treated AI as a routine workflow dependency.",
        source="memo.md",
    ).model_dump(mode="json")

    assert report["status"] == "warn"
    assert report["scope_status"] == "missing_sampling_frame"
    assert report["warnings"][0]["code"] == "missing_sampling_frame_generalization"
    assert "population is recorded without a sampling frame" in report["warnings"][0]["message"]


def test_scope_lint_complete_scope_suppresses_under_specified_scope_warnings():
    state = ProjectState(id="scope-lint", name="Scope Lint")
    state.corpus_scope = CorpusScope(
        population="Operations teams in pilot clinics",
        sampling_frame="Volunteer interviewees from two pilot clinics",
    )

    report = lint_scope_phrasing(
        state,
        "Across operations teams, AI changes workflow priorities.",
        source="memo.md",
    ).model_dump(mode="json")

    assert report["status"] == "pass"
    assert report["scope_status"] == "complete"
    assert report["warning_count"] == 0
    assert report["warnings"] == []
    assert "not sampling adequacy evidence" in report["caveat"]


def test_scope_lint_script_outputs_json_and_exit_codes(tmp_path, capsys):
    from scripts import lint_scope_phrasing

    projects_dir = tmp_path / "projects"
    store = ProjectStore(projects_dir=projects_dir)
    state = ProjectState(id="scope-script", name="Scope Script")
    store.save(state)
    input_path = tmp_path / "report.md"
    input_path.write_text("Across operations teams, AI changes workflow.", encoding="utf-8")

    warn_exit = lint_scope_phrasing.main(
        [
            "scope-script",
            "--input-file",
            str(input_path),
            "--projects-dir",
            str(projects_dir),
        ]
    )
    warn_report = json.loads(capsys.readouterr().out)

    assert warn_exit == 1
    assert warn_report["status"] == "warn"
    assert warn_report["warning_count"] >= 1

    state.corpus_scope = CorpusScope(
        population="Operations teams in pilot clinics",
        sampling_frame="Volunteer interviewees from two pilot clinics",
    )
    store.save(state)

    pass_exit = lint_scope_phrasing.main(
        [
            "scope-script",
            "--input-file",
            str(input_path),
            "--projects-dir",
            str(projects_dir),
        ]
    )
    pass_report = json.loads(capsys.readouterr().out)

    assert pass_exit == 0
    assert pass_report["status"] == "pass"
    assert pass_report["warning_count"] == 0
