"""Tests for transcript-to-report baseline generation."""

from __future__ import annotations

import asyncio

from qc_clean.core.report_baseline import (
    DEFAULT_QA_QUESTION_SET_ID,
    build_report_baseline_prompt,
    export_report_baseline_package_async,
)
from qc_clean.schemas.domain import Corpus, CorpusScope, Document, ProjectConfig, ProjectState


def test_build_report_baseline_prompt_uses_untrusted_transcript_blocks():
    state = _state()

    prompt = build_report_baseline_prompt(state, mode="direct_report")

    assert "BEGIN UNTRUSTED DATA BLOCK" in prompt
    assert "DATA> Russia is active in the information environment." in prompt
    assert "Do not rely on any existing codes, claims, or system-generated analysis." in prompt
    assert "- Phenomenon: Information manipulation in West Africa" in prompt


def test_build_report_baseline_prompt_includes_fixed_questions_for_qa_mode():
    state = _state()

    prompt = build_report_baseline_prompt(state, mode="qa_report")

    assert "Fixed reviewer question set:" in prompt
    assert "q2_participant_positions" in prompt
    assert "What distinct positions do the participants take, and who holds them?" in prompt


def test_export_report_baseline_package_includes_selected_modes(monkeypatch):
    state = _state()

    async def fake_generate(project_state, *, mode, **kwargs):
        del project_state, kwargs
        return {
            "name": f"transcript_{mode}",
            "description": f"description for {mode}",
            "mode": mode,
            "prompt_spec_id": f"{mode}_spec",
            "question_set_id": DEFAULT_QA_QUESTION_SET_ID if mode == "qa_report" else None,
            "output": {
                "title": mode,
                "executive_summary": f"summary for {mode}",
                "key_findings": ["finding"],
                "participant_positions": [],
                "consensus_points": [],
                "divergence_points": [],
                "recommendations": [],
                "caveats": [],
                "question_answers": [],
                "report_markdown": f"# {mode}",
            },
        }

    monkeypatch.setattr(
        "qc_clean.core.report_baseline.generate_report_baseline_async",
        fake_generate,
    )

    payload = asyncio.run(export_report_baseline_package_async(
        state,
        modes=["direct_report", "qa_report"],
        model_name="fake-model",
        max_chars_per_doc=500,
        trace_id="trace-report-baselines",
        max_budget=0.5,
    ))

    assert payload["package_type"] == "qualitative_coding.report_baseline_outputs"
    assert payload["report_baseline_run"]["project_id"] == state.id
    assert payload["report_baseline_run"]["model_name"] == "fake-model"
    assert payload["report_baseline_run"]["baseline_modes"] == ["direct_report", "qa_report"]
    assert payload["report_baseline_run"]["max_chars_per_doc"] == 500
    assert [row["mode"] for row in payload["report_baselines"]] == ["direct_report", "qa_report"]


def _state() -> ProjectState:
    return ProjectState(
        id="report-baseline-project",
        name="Report Baseline Project",
        config=ProjectConfig(model_name="gpt-5-mini"),
        corpus=Corpus(documents=[
            Document(
                id="d1",
                name="interview_a.txt",
                content="Russia is active in the information environment.\nLocal actors also matter.",
            ),
            Document(
                id="d2",
                name="interview_b.txt",
                content="Education and media literacy are central to the response.",
            ),
        ]),
        corpus_scope=CorpusScope(
            phenomenon="Information manipulation in West Africa",
            population="Interviewed practitioners only",
            sampling_frame="Convenience sample",
            notes="Seed corpus only.",
        ),
    )
