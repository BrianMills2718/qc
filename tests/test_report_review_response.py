"""Tests for report review response packages."""

import asyncio

from qc_clean.core.report_review_response import (
    ReportReviewResponsePackage,
    review_report_packet_async,
)


def test_report_review_response_package_validates_ranking():
    payload = _response_payload()
    package = ReportReviewResponsePackage.model_validate(payload)

    assert package.package_type == "qualitative_coding.report_review_response"
    assert package.overall_ranking == ["structured_report", "transcript_direct_report"]


def test_review_report_packet_async_wraps_llm_output(monkeypatch):
    async def fake_extract_structured(self, prompt, schema, **kwargs):
        del self, prompt, kwargs
        return schema.model_validate({
            "artifact_responses": _response_payload()["artifact_responses"],
            "overall_ranking": ["structured_report", "transcript_direct_report"],
            "comparative_summary": "Structured report is more useful.",
            "residual_concerns": ["Agent review only."],
        })

    monkeypatch.setattr(
        "qc_clean.core.report_review_response.LLMHandler.extract_structured",
        fake_extract_structured,
    )

    response = asyncio.run(review_report_packet_async(
        _packet_payload(),
        model_name="fake-model",
        reviewer_id="test-reviewer",
        trace_id="trace-review",
        max_budget=0.5,
    ))

    assert response["package_type"] == "qualitative_coding.report_review_response"
    assert response["review_response"]["reviewer_id"] == "test-reviewer"
    assert response["review_response"]["model_name"] == "fake-model"
    assert response["overall_ranking"] == ["structured_report", "transcript_direct_report"]


def _response_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_review_response",
        "review_response": {
            "generated_at": "2026-06-26T00:00:00Z",
            "packet_rubric_id": "report_authoritativeness_human_review_v1",
            "baseline_project_id": "project-1",
            "reviewer_id": "test-reviewer",
            "model_name": "fake-model",
        },
        "artifact_responses": [
            _artifact_response("structured_report"),
            _artifact_response("transcript_direct_report"),
        ],
        "overall_ranking": ["structured_report", "transcript_direct_report"],
        "comparative_summary": "Structured report is stronger.",
        "residual_concerns": [],
        "caution": "review judgment",
    }


def _artifact_response(name: str) -> dict:
    return {
        "artifact_name": name,
        "overall_score": 4,
        "dimension_scores": [
            {"dimension": "internal_consistency", "score": 4, "evidence": "No contradictions seen."},
            {"dimension": "evidence_grounding", "score": 4, "evidence": "Uses evidence."},
            {"dimension": "disagreement_handling", "score": 4, "evidence": "Handles divergence."},
            {"dimension": "scope_discipline", "score": 4, "evidence": "Caveats are present."},
            {"dimension": "recommendation_traceability", "score": 4, "evidence": "Recommendations trace to claims."},
            {"dimension": "reviewer_usefulness", "score": 4, "evidence": "Readable."},
            {"dimension": "auditability", "score": 4, "evidence": "Auditable."},
        ],
        "strengths": ["Useful."],
        "weaknesses": ["Still needs human review."],
        "unsupported_or_overclaimed_risks": [],
    }


def _packet_payload() -> dict:
    return {
        "schema_version": 1,
        "package_type": "qualitative_coding.report_review_packet",
        "review_packet": {
            "generated_at": "2026-06-26T00:00:00Z",
            "rubric_id": "report_authoritativeness_human_review_v1",
            "structured_report_path": "reviewer_report.md",
            "baseline_package_path": "report_baselines.json",
            "baseline_project_id": "project-1",
        },
        "rubric_questions": [
            {"dimension": "internal_consistency", "question": "Consistency?"},
            {"dimension": "evidence_grounding", "question": "Grounded?"},
            {"dimension": "disagreement_handling", "question": "Disagreement?"},
            {"dimension": "scope_discipline", "question": "Scope?"},
            {"dimension": "recommendation_traceability", "question": "Recommendations?"},
            {"dimension": "reviewer_usefulness", "question": "Useful?"},
            {"dimension": "auditability", "question": "Auditable?"},
        ],
        "artifacts": [
            {
                "artifact_name": "structured_report",
                "artifact_kind": "structured_report",
                "source_path": "reviewer_report.md",
                "report_markdown": "# Structured",
            },
            {
                "artifact_name": "transcript_direct_report",
                "artifact_kind": "direct_report",
                "source_path": "report_baselines.json#direct",
                "report_markdown": "# Direct",
            },
        ],
        "response_instructions": ["Score each artifact."],
        "caution": "packet only",
    }
