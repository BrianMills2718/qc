"""Structured reviewer responses for report-comparison packets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qc_clean.core.llm.llm_handler import LLMHandler
from qc_clean.core.report_baseline_comparison import RUBRIC_DIMENSIONS
from qc_clean.core.report_review_packet import ReportReviewPacket


REPORT_REVIEW_RESPONSE_TYPE = "qualitative_coding.report_review_response"
REPORT_REVIEW_RESPONSE_CAUTION = (
    "Report review responses are reviewer judgments over a supplied packet; "
    "they are not held-out validity evidence unless the reviewer protocol and "
    "reviewer qualifications are documented separately."
)


class ReportReviewDimensionScore(BaseModel):
    """One reviewer score for one artifact and rubric dimension."""

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(description="Rubric dimension ID copied from the review packet")
    score: int = Field(description="Reviewer score from 1=poor to 5=excellent")
    evidence: str = Field(description="Concise evidence or rationale for the score")

    @model_validator(mode="after")
    def validate_score(self) -> "ReportReviewDimensionScore":
        if self.dimension not in RUBRIC_DIMENSIONS:
            raise ValueError(f"Unknown report review dimension: {self.dimension}")
        if self.score < 1 or self.score > 5:
            raise ValueError("Report review dimension score must be between 1 and 5")
        return self


class ReportReviewArtifactResponse(BaseModel):
    """Reviewer response for one report artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(description="Artifact name copied from the review packet")
    overall_score: int = Field(description="Overall artifact score from 1=poor to 5=excellent")
    dimension_scores: list[ReportReviewDimensionScore] = Field(
        description="Reviewer scores for every rubric dimension"
    )
    strengths: list[str] = Field(default_factory=list, description="Main strengths of the artifact")
    weaknesses: list[str] = Field(default_factory=list, description="Main weaknesses of the artifact")
    unsupported_or_overclaimed_risks: list[str] = Field(
        default_factory=list,
        description="Unsupported, contradictory, over-scoped, or overconfident claims to review",
    )

    @model_validator(mode="after")
    def validate_artifact_response(self) -> "ReportReviewArtifactResponse":
        if self.overall_score < 1 or self.overall_score > 5:
            raise ValueError("Report review overall_score must be between 1 and 5")
        dimensions = [row.dimension for row in self.dimension_scores]
        if sorted(dimensions) != sorted(RUBRIC_DIMENSIONS):
            raise ValueError("Artifact response must score every rubric dimension exactly once")
        return self


class ReportReviewResponseMetadata(BaseModel):
    """Metadata for a report review response package."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(description="UTC ISO timestamp when response was generated")
    packet_rubric_id: str = Field(description="Rubric ID copied from the packet")
    baseline_project_id: str = Field(description="Project ID copied from the packet")
    reviewer_id: str = Field(description="Reviewer or agent identifier")
    model_name: str = Field(description="Model name used for agent-generated review")


class ReportReviewResponsePackage(BaseModel):
    """Versioned report review response package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Response schema version")
    package_type: Literal["qualitative_coding.report_review_response"] = Field(
        description="Package type discriminator"
    )
    review_response: ReportReviewResponseMetadata = Field(description="Response metadata")
    artifact_responses: list[ReportReviewArtifactResponse] = Field(
        description="Reviewer responses for each artifact"
    )
    overall_ranking: list[str] = Field(
        description="Artifact names ranked best to worst for reviewer usefulness"
    )
    comparative_summary: str = Field(description="Short comparative judgment across artifacts")
    residual_concerns: list[str] = Field(
        default_factory=list,
        description="Remaining concerns or review caveats",
    )
    caution: str = Field(
        default=REPORT_REVIEW_RESPONSE_CAUTION,
        description="Interpretive caution for this review response",
    )

    @model_validator(mode="after")
    def validate_response_package(self) -> "ReportReviewResponsePackage":
        artifact_names = [row.artifact_name for row in self.artifact_responses]
        if len(artifact_names) != len(set(artifact_names)):
            raise ValueError("Artifact response names must be unique")
        if sorted(self.overall_ranking) != sorted(artifact_names):
            raise ValueError("overall_ranking must include exactly the artifact response names")
        return self


class _LLMReportReviewOutput(BaseModel):
    """LLM-facing report review output."""

    model_config = ConfigDict(extra="forbid")

    artifact_responses: list[ReportReviewArtifactResponse] = Field(
        description="Scores and rationales for every report artifact in the packet"
    )
    overall_ranking: list[str] = Field(
        description="Artifact names ranked best to worst for reviewer usefulness"
    )
    comparative_summary: str = Field(description="Short comparative judgment across artifacts")
    residual_concerns: list[str] = Field(
        default_factory=list,
        description="Remaining caveats about the review or artifacts",
    )


async def review_report_packet_async(
    packet_payload: dict,
    *,
    model_name: str = "gpt-5-mini",
    reviewer_id: str = "agent-reviewer",
    trace_id: str = "qualitative_coding/report-review",
    max_budget: float = 5.0,
) -> dict:
    """Run an LLM reviewer over a report review packet and return a response package."""
    packet = ReportReviewPacket.model_validate(packet_payload)
    llm = LLMHandler(model_name=model_name, temperature=0.2)
    output = await llm.extract_structured(
        _review_prompt(packet),
        _LLMReportReviewOutput,
        instructions=_review_instructions(packet),
        task="qualitative_coding.report_review_response",
        trace_id=trace_id,
        max_budget=max_budget,
    )
    package = ReportReviewResponsePackage(
        schema_version=1,
        package_type=REPORT_REVIEW_RESPONSE_TYPE,
        review_response=ReportReviewResponseMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            packet_rubric_id=packet.review_packet.rubric_id,
            baseline_project_id=packet.review_packet.baseline_project_id,
            reviewer_id=reviewer_id,
            model_name=model_name,
        ),
        artifact_responses=output.artifact_responses,
        overall_ranking=output.overall_ranking,
        comparative_summary=output.comparative_summary,
        residual_concerns=output.residual_concerns,
    )
    return package.model_dump(mode="json")


async def review_report_packet_file_async(
    packet_path: Path,
    *,
    model_name: str = "gpt-5-mini",
    reviewer_id: str = "agent-reviewer",
    trace_id: str | None = None,
    max_budget: float = 5.0,
) -> dict:
    """Read a report review packet and run an LLM reviewer over it."""
    packet_payload = json.loads(packet_path.read_text(encoding="utf-8"))
    return await review_report_packet_async(
        packet_payload,
        model_name=model_name,
        reviewer_id=reviewer_id,
        trace_id=trace_id or f"qualitative_coding/report-review/{packet_path.stem}",
        max_budget=max_budget,
    )


def _review_prompt(packet: ReportReviewPacket) -> str:
    artifact_blocks = []
    for artifact in packet.artifacts:
        artifact_blocks.append(
            "\n".join([
                f"ARTIFACT: {artifact.artifact_name}",
                f"KIND: {artifact.artifact_kind}",
                f"SOURCE: {artifact.source_path}",
                "BEGIN REPORT MARKDOWN",
                artifact.report_markdown,
                "END REPORT MARKDOWN",
            ])
        )
    rubric_lines = [
        f"- {question.dimension}: {question.question}"
        for question in packet.rubric_questions
    ]
    return "\n\n".join([
        "You are reviewing qualitative analysis report artifacts for reviewer usefulness.",
        "Score each artifact independently, then rank them comparatively.",
        "Use only the report artifacts and rubric below.",
        "Do not treat deterministic scores, if present, as authoritative.",
        "",
        "Rubric dimensions:",
        "\n".join(rubric_lines),
        "",
        "Artifacts:",
        "\n\n".join(artifact_blocks),
    ])


def _review_instructions(packet: ReportReviewPacket) -> str:
    artifact_names = ", ".join(artifact.artifact_name for artifact in packet.artifacts)
    dimensions = ", ".join(RUBRIC_DIMENSIONS)
    return (
        "Return one artifact_responses row for each artifact: "
        f"{artifact_names}. Score every artifact on every dimension: {dimensions}. "
        "Use integer scores from 1 to 5. Include concise evidence for each score, "
        "strengths, weaknesses, and any unsupported_or_overclaimed_risks. "
        "overall_ranking must include exactly the artifact names, best to worst."
    )
