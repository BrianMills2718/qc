"""Tests for report comparison review packets."""

from qc_clean.core.report_review_packet import build_report_review_packet


def test_build_report_review_packet_includes_reports_and_rubric():
    packet = build_report_review_packet(
        structured_report_markdown="# Structured\n\nEvidence.",
        baseline_package_payload=_baseline_package(),
        structured_report_path="reviewer_report.md",
        baseline_package_path="report_baselines.json",
    )

    assert packet["package_type"] == "qualitative_coding.report_review_packet"
    assert packet["review_packet"]["rubric_id"] == "report_authoritativeness_human_review_v1"
    assert packet["review_packet"]["baseline_project_id"] == "project-1"
    assert [row["artifact_name"] for row in packet["artifacts"]] == [
        "structured_report",
        "transcript_direct_report",
    ]
    assert {row["dimension"] for row in packet["rubric_questions"]} == {
        "internal_consistency",
        "evidence_grounding",
        "disagreement_handling",
        "scope_discipline",
        "recommendation_traceability",
        "reviewer_usefulness",
        "auditability",
    }
    assert "Score each artifact" in packet["response_instructions"][0]


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
