"""Tests for the report baseline export script boundary."""

from __future__ import annotations

import json

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.schemas.domain import Corpus, Document, ProjectState
from scripts import run_report_baselines


def test_run_report_baselines_writes_output_and_stdout(tmp_path, monkeypatch, capsys):
    state = _state()
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    output_file = tmp_path / "report_baselines.json"

    async def fake_export(project_state, **kwargs):
        return _package(project_state.id, kwargs)

    monkeypatch.setattr(run_report_baselines, "ProjectStore", lambda: store)
    monkeypatch.setattr(run_report_baselines, "export_report_baseline_package_async", fake_export)

    exit_code = run_report_baselines.main([
        state.id,
        "--output",
        str(output_file),
        "--mode",
        "direct_report",
        "--model",
        "fake-model",
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.report_baseline_outputs"
    assert stdout_payload["report_baseline_run"]["project_id"] == state.id


def test_run_report_baselines_forwards_options(tmp_path, monkeypatch, capsys):
    state = _state()
    store = ProjectStore(projects_dir=tmp_path / "projects")
    store.save(state)
    captured = {}

    async def fake_export(project_state, **kwargs):
        captured["state_id"] = project_state.id
        captured["kwargs"] = kwargs
        return _package(project_state.id, kwargs)

    monkeypatch.setattr(run_report_baselines, "ProjectStore", lambda: store)
    monkeypatch.setattr(run_report_baselines, "export_report_baseline_package_async", fake_export)

    exit_code = run_report_baselines.main([
        state.id,
        "--mode",
        "direct_report",
        "--mode",
        "qa_report",
        "--model",
        "fair-baseline-model",
        "--max-chars-per-doc",
        "2500",
        "--trace-id",
        "trace-report",
        "--max-budget",
        "1.5",
    ])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["report_baseline_run"]["project_id"] == state.id
    assert captured == {
        "state_id": state.id,
        "kwargs": {
            "modes": ["direct_report", "qa_report"],
            "model_name": "fair-baseline-model",
            "max_chars_per_doc": 2500,
            "trace_id": "trace-report",
            "max_budget": 1.5,
        },
    }


def _package(project_id: str, kwargs: dict) -> dict:
    modes = kwargs["modes"]
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_outputs",
        "report_baseline_run": {
            "project_id": project_id,
            "project_name": "Report Baseline Script Test",
            "generated_at": "2026-06-26T00:00:00Z",
            "model_name": kwargs["model_name"],
            "baseline_modes": modes,
            "corpus_document_count": 1,
            "max_chars_per_doc": kwargs["max_chars_per_doc"],
            "notes": "",
        },
        "report_baselines": [],
        "caution": "comparison only",
    }


def _state() -> ProjectState:
    return ProjectState(
        id="project-report-baseline-script",
        name="Report Baseline Script Test",
        corpus=Corpus(documents=[
            Document(id="d1", name="interview.txt", content="AI is changing the workflow."),
        ]),
    )
