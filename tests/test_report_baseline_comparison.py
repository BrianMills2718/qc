"""Tests for deterministic report-baseline comparison scoring."""

from __future__ import annotations

from qc_clean.core.report_baseline_comparison import compare_report_baselines, score_report_artifact


def test_score_report_artifact_detects_conflicting_prevalence_counts():
    score = score_report_artifact(
        artifact_name="structured_report",
        artifact_kind="structured_report",
        text=(
            "# Report\n\n"
            "- **Local actors**: present in 2/3 documents.\n"
            "- **Local actors**: present in 3/3 documents.\n"
            "## Claim Ledger\n\n| claim | evidence |\n| c1 | quote |\n"
        ),
    )

    internal = _dimension(score, "internal_consistency")
    assert internal.score < 1.0
    assert "Detected 1 conflicting prevalence label" in internal.evidence[0]
    assert "prevalence_conflict_count=1" in score.deterministic_findings


def test_compare_report_baselines_scores_structured_and_baseline_reports():
    payload = compare_report_baselines(
        structured_report_markdown=(
            "# Structured\n\n"
            "## Claim Ledger\n\n"
            "| claim | evidence |\n| claim-abcdef | quote |\n"
            "Consensus and divergence are both discussed.\n"
        ),
        baseline_package_payload=_baseline_package(),
        structured_report_path="report.md",
        baseline_package_path="report_baselines.json",
    )

    assert payload["package_type"] == "qualitative_coding.report_baseline_comparison"
    assert payload["comparison"]["rubric_id"] == "report_authoritativeness_v1"
    assert payload["comparison"]["baseline_project_id"] == "project-1"
    assert [row["artifact_name"] for row in payload["artifact_scores"]] == [
        "structured_report",
        "transcript_direct_report",
        "transcript_qa_report",
    ]
    assert sorted(payload["ranking"]) == [
        "structured_report",
        "transcript_direct_report",
        "transcript_qa_report",
    ]


def _dimension(score, dimension):
    return next(row for row in score.dimension_scores if row.dimension == dimension)


def _baseline_package() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_baseline_outputs",
        "report_baseline_run": {
            "project_id": "project-1",
            "project_name": "Report Baseline Test",
            "generated_at": "2026-06-26T00:00:00Z",
            "model_name": "fake-model",
            "baseline_modes": ["direct_report", "qa_report"],
            "corpus_document_count": 2,
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
                "output": _output("# Direct\n\nConsensus is clear.\nRecommendation: cite evidence."),
            },
            {
                "name": "transcript_qa_report",
                "description": "QA baseline",
                "mode": "qa_report",
                "prompt_spec_id": "qa",
                "question_set_id": "reviewer_qa_v1",
                "output": _output("# QA\n\nDivergence and caveats are explicit."),
            },
        ],
        "caution": "comparison only",
    }


def _output(markdown: str) -> dict:
    return {
        "title": "Baseline",
        "executive_summary": "Summary",
        "key_findings": [],
        "participant_positions": [],
        "consensus_points": [],
        "divergence_points": [],
        "recommendations": [],
        "caveats": [],
        "question_answers": [],
        "report_markdown": markdown,
    }
