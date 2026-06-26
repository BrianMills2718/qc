"""Tests for report-baseline comparison script boundary."""

from __future__ import annotations

import json

from scripts import compare_report_baselines


def test_compare_report_baselines_script_writes_output(tmp_path, capsys):
    report_path = tmp_path / "report.md"
    baseline_path = tmp_path / "report_baselines.json"
    output_path = tmp_path / "comparison.json"
    report_path.write_text("# Structured\n\nConsensus appears in 1/1 documents.", encoding="utf-8")
    baseline_path.write_text(json.dumps(_baseline_package()), encoding="utf-8")

    exit_code = compare_report_baselines.main([
        str(report_path),
        str(baseline_path),
        "--output",
        str(output_path),
    ])

    assert exit_code == 0
    stdout_payload = json.loads(capsys.readouterr().out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert stdout_payload == file_payload
    assert stdout_payload["package_type"] == "qualitative_coding.report_baseline_comparison"


def test_compare_report_baselines_script_reports_invalid_json(tmp_path, capsys):
    report_path = tmp_path / "report.md"
    baseline_path = tmp_path / "bad.json"
    report_path.write_text("# Structured", encoding="utf-8")
    baseline_path.write_text("{bad", encoding="utf-8")

    exit_code = compare_report_baselines.main([str(report_path), str(baseline_path)])

    assert exit_code == 1
    assert "error" in json.loads(capsys.readouterr().out)


def _baseline_package() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_outputs",
        "report_baseline_run": {
            "project_id": "project-1",
            "project_name": "Report Baseline Test",
            "generated_at": "2026-06-26T00:00:00Z",
            "model_name": "fake-model",
            "baseline_modes": ["direct_report"],
            "corpus_document_count": 1,
            "max_chars_per_doc": None,
            "notes": "",
        },
        "report_baselines": [
            {
                "name": "transcript_direct_report",
                "description": "Direct baseline",
                "mode": "direct_report",
                "prompt_spec_id": "direct",
                "question_set_id": None,
                "output": {
                    "title": "Baseline",
                    "executive_summary": "Summary",
                    "key_findings": [],
                    "participant_positions": [],
                    "consensus_points": [],
                    "divergence_points": [],
                    "recommendations": [],
                    "caveats": [],
                    "question_answers": [],
                    "report_markdown": "# Direct\n\nConsensus is clear.",
                },
            },
        ],
        "caution": "comparison only",
    }
