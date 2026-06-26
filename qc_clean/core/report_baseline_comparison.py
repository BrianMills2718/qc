"""Deterministic scoring for structured reports versus transcript baselines."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qc_clean.core.report_baseline import ReportBaselinePackage


REPORT_COMPARISON_PACKAGE_TYPE = "qualitative_coding.report_baseline_comparison"
REPORT_COMPARISON_RUBRIC_ID = "report_authoritativeness_v1"
REPORT_COMPARISON_CAUTION = (
    "Report comparison scores are deterministic heuristic readouts for triage; "
    "they are not human adjudication, held-out evidence, or superiority proof."
)

ReportArtifactKind = Literal["structured_report", "direct_report", "qa_report"]

RUBRIC_DIMENSIONS: tuple[str, ...] = (
    "internal_consistency",
    "evidence_grounding",
    "disagreement_handling",
    "scope_discipline",
    "recommendation_traceability",
    "reviewer_usefulness",
    "auditability",
)

_PREVALENCE_PATTERN = re.compile(
    r"(?P<label>[*A-Za-z][*A-Za-z0-9 ,/&+'().:-]{3,140}?)"
    r"\s*:?\s+(?:appears|present)\s+in\s+"
    r"(?P<count>\d+)\s*/\s*(?P<total>\d+)\s+documents?",
    re.IGNORECASE,
)
_QUOTE_PATTERN = re.compile(r"(^>|\n>|\"[^\"]{20,}\")")
_CLAIM_ID_PATTERN = re.compile(r"\b(?:claim|claims?)[: #_-]*[A-Za-z0-9-]{6,}\b", re.IGNORECASE)


class ReportDimensionScore(BaseModel):
    """One scored report-comparison rubric dimension."""

    model_config = ConfigDict(extra="forbid")

    dimension: str = Field(description="Rubric dimension ID")
    score: float = Field(description="Heuristic score from 0.0 to 1.0")
    evidence: list[str] = Field(
        default_factory=list,
        description="Short deterministic signals that explain the score",
    )

    @model_validator(mode="after")
    def validate_score_bounds(self) -> "ReportDimensionScore":
        if self.score < 0 or self.score > 1:
            raise ValueError("Report dimension score must be between 0 and 1")
        if self.dimension not in RUBRIC_DIMENSIONS:
            raise ValueError(f"Unknown report comparison dimension: {self.dimension}")
        return self


class ReportArtifactScore(BaseModel):
    """Scores for one report artifact under the comparison rubric."""

    model_config = ConfigDict(extra="forbid")

    artifact_name: str = Field(description="Stable report artifact name")
    artifact_kind: ReportArtifactKind = Field(description="Report artifact class")
    word_count: int = Field(description="Approximate whitespace word count")
    overall_score: float = Field(description="Mean dimension score from 0.0 to 1.0")
    dimension_scores: list[ReportDimensionScore] = Field(
        description="Scores for every rubric dimension"
    )
    deterministic_findings: list[str] = Field(
        default_factory=list,
        description="Concise deterministic observations about the report",
    )

    @model_validator(mode="after")
    def validate_dimensions(self) -> "ReportArtifactScore":
        dimensions = [row.dimension for row in self.dimension_scores]
        if sorted(dimensions) != sorted(RUBRIC_DIMENSIONS):
            raise ValueError("Report artifact score must include every rubric dimension exactly once")
        if self.overall_score < 0 or self.overall_score > 1:
            raise ValueError("Report artifact overall_score must be between 0 and 1")
        return self


class ReportBaselineComparisonMetadata(BaseModel):
    """Metadata for one report-baseline comparison package."""

    model_config = ConfigDict(extra="forbid")

    generated_at: str = Field(description="UTC ISO timestamp when the comparison package was generated")
    rubric_id: str = Field(description="Scoring rubric identifier")
    structured_report_path: str = Field(description="Path of the structured Markdown report scored")
    baseline_package_path: str = Field(description="Path of the report-baseline package scored")
    baseline_project_id: str = Field(description="Project ID from the baseline package")


class ReportBaselineComparisonPackage(BaseModel):
    """Versioned side-by-side comparison of structured and baseline reports."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = Field(description="Comparison package schema version")
    package_type: Literal["qualitative_coding.report_baseline_comparison"] = Field(
        description="Package type discriminator"
    )
    comparison: ReportBaselineComparisonMetadata = Field(description="Comparison run metadata")
    artifact_scores: list[ReportArtifactScore] = Field(description="Scores for each report artifact")
    ranking: list[str] = Field(description="Artifact names ordered by descending overall score")
    caution: str = Field(
        default=REPORT_COMPARISON_CAUTION,
        description="Interpretive caution for this heuristic comparison package",
    )

    @model_validator(mode="after")
    def validate_ranking(self) -> "ReportBaselineComparisonPackage":
        artifact_names = [score.artifact_name for score in self.artifact_scores]
        if sorted(self.ranking) != sorted(artifact_names):
            raise ValueError("Ranking must include exactly the scored artifact names")
        return self


def compare_report_baselines(
    *,
    structured_report_markdown: str,
    baseline_package_payload: dict,
    structured_report_path: str,
    baseline_package_path: str,
) -> dict:
    """Score a structured Markdown report beside generated baseline reports."""
    baseline_package = ReportBaselinePackage.model_validate(baseline_package_payload)
    scores = [
        score_report_artifact(
            artifact_name="structured_report",
            artifact_kind="structured_report",
            text=structured_report_markdown,
        )
    ]
    for artifact in baseline_package.report_baselines:
        scores.append(score_report_artifact(
            artifact_name=artifact.name,
            artifact_kind=artifact.mode,
            text=artifact.output.report_markdown,
        ))

    ranking = [
        score.artifact_name
        for score in sorted(scores, key=lambda row: row.overall_score, reverse=True)
    ]
    package = ReportBaselineComparisonPackage(
        schema_version=1,
        package_type=REPORT_COMPARISON_PACKAGE_TYPE,
        comparison=ReportBaselineComparisonMetadata(
            generated_at=datetime.now(timezone.utc).isoformat(),
            rubric_id=REPORT_COMPARISON_RUBRIC_ID,
            structured_report_path=structured_report_path,
            baseline_package_path=baseline_package_path,
            baseline_project_id=baseline_package.report_baseline_run.project_id,
        ),
        artifact_scores=scores,
        ranking=ranking,
    )
    return package.model_dump(mode="json")


def compare_report_baseline_files(
    *,
    structured_report_path: Path,
    baseline_package_path: Path,
) -> dict:
    """Read report artifacts from disk and return a comparison package."""
    structured_report_markdown = structured_report_path.read_text(encoding="utf-8")
    baseline_package_payload = json.loads(baseline_package_path.read_text(encoding="utf-8"))
    return compare_report_baselines(
        structured_report_markdown=structured_report_markdown,
        baseline_package_payload=baseline_package_payload,
        structured_report_path=str(structured_report_path),
        baseline_package_path=str(baseline_package_path),
    )


def score_report_artifact(
    *,
    artifact_name: str,
    artifact_kind: ReportArtifactKind,
    text: str,
) -> ReportArtifactScore:
    """Score one report artifact using deterministic reviewer-readout signals."""
    metrics = _text_metrics(text)
    dimension_scores = [
        _score_internal_consistency(metrics),
        _score_evidence_grounding(metrics),
        _score_disagreement_handling(metrics),
        _score_scope_discipline(metrics),
        _score_recommendation_traceability(metrics),
        _score_reviewer_usefulness(metrics),
        _score_auditability(metrics),
    ]
    overall = round(
        sum(score.score for score in dimension_scores) / len(dimension_scores),
        3,
    )
    return ReportArtifactScore(
        artifact_name=artifact_name,
        artifact_kind=artifact_kind,
        word_count=metrics["word_count"],
        overall_score=overall,
        dimension_scores=dimension_scores,
        deterministic_findings=_deterministic_findings(metrics),
    )


def _text_metrics(text: str) -> dict:
    lower = text.lower()
    prevalence_counts = _prevalence_counts(text)
    conflicts = {
        label: sorted(counts)
        for label, counts in prevalence_counts.items()
        if len(counts) > 1
    }
    heading_count = len(re.findall(r"^#{1,4}\s+", text, flags=re.MULTILINE))
    bullet_count = len(re.findall(r"^\s*[-*]\s+", text, flags=re.MULTILINE))
    recommendation_mentions = len(re.findall(r"\brecommend(?:ation|ed|s)?\b", lower))
    return {
        "word_count": len(re.findall(r"\S+", text)),
        "heading_count": heading_count,
        "bullet_count": bullet_count,
        "quote_count": len(_QUOTE_PATTERN.findall(text)),
        "claim_id_count": len(_CLAIM_ID_PATTERN.findall(text)),
        "table_count": text.count("\n|"),
        "prevalence_count_count": sum(len(counts) for counts in prevalence_counts.values()),
        "prevalence_conflicts": conflicts,
        "needs_anchor_count": lower.count("needs_anchor") + lower.count("needs anchor"),
        "unsupported_count": lower.count("unsupported"),
        "consensus_mentions": lower.count("consensus") + lower.count("converge"),
        "divergence_mentions": lower.count("divergence") + lower.count("diverge") + lower.count("tension"),
        "caveat_mentions": lower.count("caveat") + lower.count("uncertain") + lower.count("scope") + lower.count("boundary"),
        "recommendation_mentions": recommendation_mentions,
        "traceability_mentions": lower.count("claim") + lower.count("evidence") + lower.count("quote"),
        "audit_mentions": lower.count("audit") + lower.count("ledger") + lower.count("relationship") + lower.count("observed pattern"),
    }


def _prevalence_counts(text: str) -> dict[str, set[str]]:
    counts: dict[str, set[str]] = {}
    for match in _PREVALENCE_PATTERN.finditer(text):
        label = _normalize_label(match.group("label"))
        counts.setdefault(label, set()).add(f"{match.group('count')}/{match.group('total')}")
    return counts


def _normalize_label(label: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", " ", label.lower().strip("*")).strip()
    return re.sub(r"\s+", " ", compact)


def _score_internal_consistency(metrics: dict) -> ReportDimensionScore:
    conflicts = metrics["prevalence_conflicts"]
    score = max(0.0, 1.0 - (0.35 * len(conflicts)))
    evidence = [f"Detected {len(conflicts)} conflicting prevalence label(s)."]
    if conflicts:
        evidence.extend(
            f"{label}: {', '.join(counts)}"
            for label, counts in sorted(conflicts.items())[:5]
        )
    return _dimension("internal_consistency", score, evidence)


def _score_evidence_grounding(metrics: dict) -> ReportDimensionScore:
    signal_count = metrics["quote_count"] + metrics["claim_id_count"] + metrics["prevalence_count_count"]
    score = min(1.0, signal_count / 12)
    evidence = [
        f"quote signals={metrics['quote_count']}",
        f"claim-id signals={metrics['claim_id_count']}",
        f"prevalence-count signals={metrics['prevalence_count_count']}",
    ]
    return _dimension("evidence_grounding", score, evidence)


def _score_disagreement_handling(metrics: dict) -> ReportDimensionScore:
    signal_count = metrics["consensus_mentions"] + metrics["divergence_mentions"]
    score = min(1.0, signal_count / 8)
    evidence = [
        f"consensus/convergence mentions={metrics['consensus_mentions']}",
        f"divergence/tension mentions={metrics['divergence_mentions']}",
    ]
    return _dimension("disagreement_handling", score, evidence)


def _score_scope_discipline(metrics: dict) -> ReportDimensionScore:
    score = min(1.0, metrics["caveat_mentions"] / 6)
    if metrics["unsupported_count"]:
        score = min(1.0, score + 0.15)
    evidence = [
        f"scope/caveat/uncertainty mentions={metrics['caveat_mentions']}",
        f"unsupported markers={metrics['unsupported_count']}",
    ]
    return _dimension("scope_discipline", score, evidence)


def _score_recommendation_traceability(metrics: dict) -> ReportDimensionScore:
    if metrics["recommendation_mentions"] == 0:
        return _dimension(
            "recommendation_traceability",
            0.5,
            ["No recommendation section signal detected; traceability need is reduced but not proven."],
        )
    score = min(1.0, metrics["traceability_mentions"] / (metrics["recommendation_mentions"] * 4))
    evidence = [
        f"recommendation mentions={metrics['recommendation_mentions']}",
        f"claim/evidence/quote traceability mentions={metrics['traceability_mentions']}",
    ]
    return _dimension("recommendation_traceability", score, evidence)


def _score_reviewer_usefulness(metrics: dict) -> ReportDimensionScore:
    structure_score = min(1.0, (metrics["heading_count"] + metrics["bullet_count"]) / 25)
    length_penalty = 0.0
    if metrics["word_count"] > 4000:
        length_penalty = min(0.3, (metrics["word_count"] - 4000) / 10000)
    score = max(0.0, structure_score - length_penalty)
    evidence = [
        f"headings={metrics['heading_count']}",
        f"bullets={metrics['bullet_count']}",
        f"word_count={metrics['word_count']}",
    ]
    return _dimension("reviewer_usefulness", score, evidence)


def _score_auditability(metrics: dict) -> ReportDimensionScore:
    signal_count = (
        metrics["claim_id_count"]
        + metrics["table_count"]
        + metrics["audit_mentions"]
        + metrics["prevalence_count_count"]
    )
    score = min(1.0, signal_count / 18)
    evidence = [
        f"claim-id signals={metrics['claim_id_count']}",
        f"markdown table row signals={metrics['table_count']}",
        f"audit/ledger/relationship mentions={metrics['audit_mentions']}",
        f"prevalence-count signals={metrics['prevalence_count_count']}",
    ]
    return _dimension("auditability", score, evidence)


def _dimension(dimension: str, score: float, evidence: list[str]) -> ReportDimensionScore:
    return ReportDimensionScore(
        dimension=dimension,
        score=round(max(0.0, min(1.0, score)), 3),
        evidence=evidence,
    )


def _deterministic_findings(metrics: dict) -> list[str]:
    findings = [
        f"word_count={metrics['word_count']}",
        f"prevalence_conflict_count={len(metrics['prevalence_conflicts'])}",
        f"quote_signal_count={metrics['quote_count']}",
        f"audit_signal_count={metrics['audit_mentions']}",
    ]
    if metrics["needs_anchor_count"] or metrics["unsupported_count"]:
        findings.append(
            "support_status_markers="
            f"{metrics['needs_anchor_count'] + metrics['unsupported_count']}"
        )
    return findings
