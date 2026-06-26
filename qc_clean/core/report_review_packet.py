"""Review-packet writer for report baseline comparisons."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qc_clean.core.report_baseline import ReportBaselinePackage
from qc_clean.core.report_baseline_comparison import RUBRIC_DIMENSIONS


REPORT_REVIEW_PACKET_TYPE = "qualitative_coding.report_review_packet"
REPORT_REVIEW_RUBRIC_ID = "report_authoritativeness_human_review_v1"
REPORT_REVIEW_PACKET_CAUTION = (
    "Report review packets are adjudication inputs only; they are not completed "
    "review results or superiority evidence until reviewer responses are imported."
)

ReportReviewArtifactKind = Literal["structured_report", "direct_report", "qa_report"]

RUBRIC_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("internal_consistency", "Does the report present one coherent set of analysis facts without contradictions?"),
    ("evidence_grounding", "Are findings grounded in quotes, claims, counts, or traceable evidence?"),
    ("disagreement_handling", "Does the report clearly describe participant convergence and divergence?"),
    ("scope_discipline", "Does the report state caveats, boundaries, and uncertainty where needed?"),
    ("recommendation_traceability", "Can recommendations be traced back to specific evidence or claims?"),
    ("reviewer_usefulness", "Is the report readable and useful for a reviewer making sense of the corpus?"),
    ("auditability", "Can a reviewer audit how conclusions connect to underlying artifacts?"),
)


class ReportReviewArtifact(BaseModel):
    """One report artifact included for review."""

    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(description="Stable artifact name")
    artifact_kind: ReportReviewArtifactKind = Field(description="Artifact kind")
    source_path: str = Field(description="Source path or package artifact reference")
    report_markdown: str = Field(description="Markdown report text to review")


class ReportReviewQuestion(BaseModel):
    """One rubric question for report review."""

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(description="Rubric dimension ID")
    question: str = Field(description="Reviewer-facing question")

    @model_validator(mode="after")
    def validate_dimension(self) -> "ReportReviewQuestion":
        if self.dimension not in RUBRIC_DIMENSIONS:
            raise ValueError(f"Unknown report review dimension: {self.dimension}")
        return self


class ReportReviewPacketMetadata(BaseModel):
    """Metadata for one report review packet."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(description="UTC ISO timestamp when the packet was generated")
    rubric_id: str = Field(description="Review rubric identifier")
    structured_report_path: str = Field(description="Structured report path")
    baseline_package_path: str = Field(description="Report-baseline package path")
    baseline_project_id: str = Field(description="Project ID from the baseline package")


class ReportReviewPacket(BaseModel):
    """Versioned packet for human or agent report comparison review."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Packet schema version")
    package_type: Literal["qualitative_coding.report_review_packet"] = Field(
        description="Package type discriminator"
    )
    review_packet: ReportReviewPacketMetadata = Field(description="Packet metadata")
    rubric_questions: list[ReportReviewQuestion] = Field(description="Questions reviewers should answer")
    artifacts: list[ReportReviewArtifact] = Field(description="Report artifacts to compare")
    response_instructions: list[str] = Field(description="Instructions for completing the review")
    caution: str = Field(
        default=REPORT_REVIEW_PACKET_CAUTION,
        description="Interpretive caution for this review packet",
    )

    @model_validator(mode="after")
    def validate_artifacts(self) -> "ReportReviewPacket":
        names = [artifact.artifact_name for artifact in self.artifacts]
        if len(names) != len(set(names)):
            raise ValueError("Report review packet artifact names must be unique")
        if "structured_report" not in names:
            raise ValueError("Report review packet must include structured_report")
        return self


def build_report_review_packet(
    *,
    structured_report_markdown: str,
    baseline_package_payload: dict,
    structured_report_path: str,
    baseline_package_path: str,
) -> dict:
    """Build a report review packet from report text and baseline outputs."""
    baseline_package = ReportBaselinePackage.model_validate(baseline_package_payload)
    artifacts = [
        ReportReviewArtifact(
            artifact_name="structured_report",
            artifact_kind="structured_report",
            source_path=structured_report_path,
            report_markdown=structured_report_markdown,
        )
    ]
    for artifact in baseline_package.report_baselines:
        artifacts.append(ReportReviewArtifact(
            artifact_name=artifact.name,
            artifact_kind=artifact.mode,
            source_path=f"{baseline_package_path}#{artifact.name}",
            report_markdown=artifact.output.report_markdown,
        ))

    packet = ReportReviewPacket(
        schema_version=1,
        package_type=REPORT_REVIEW_PACKET_TYPE,
        review_packet=ReportReviewPacketMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            rubric_id=REPORT_REVIEW_RUBRIC_ID,
            structured_report_path=structured_report_path,
            baseline_package_path=baseline_package_path,
            baseline_project_id=baseline_package.report_baseline_run.project_id,
        ),
        rubric_questions=[
            ReportReviewQuestion(dimension=dimension, question=question)
            for dimension, question in RUBRIC_QUESTIONS
        ],
        artifacts=artifacts,
        response_instructions=[
            "Score each artifact from 1-5 on every rubric dimension.",
            "Record concise evidence for each score.",
            "Rank artifacts for overall reviewer usefulness.",
            "State whether any artifact makes unsupported, contradictory, or over-scoped claims.",
        ],
    )
    return packet.model_dump(mode="json")


def build_report_review_packet_from_files(
    *,
    structured_report_path: Path,
    baseline_package_path: Path,
) -> dict:
    """Read report artifacts from disk and build a report review packet."""
    return build_report_review_packet(
        structured_report_markdown=structured_report_path.read_text(encoding="utf-8"),
        baseline_package_payload=json.loads(baseline_package_path.read_text(encoding="utf-8")),
        structured_report_path=str(structured_report_path),
        baseline_package_path=str(baseline_package_path),
    )
