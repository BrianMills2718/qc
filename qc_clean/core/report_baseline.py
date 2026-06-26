"""Transcript-to-report baseline generation for reviewer-facing comparisons."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qc_clean.core.llm.llm_handler import LLMHandler
from qc_clean.core.prompting import format_untrusted_documents
from qc_clean.schemas.domain import ProjectState


ReportBaselineMode = Literal["direct_report", "qa_report"]

REPORT_BASELINE_PACKAGE_TYPE = "qualitative_coding.report_baseline_outputs"
REPORT_BASELINE_PACKAGE_CAUTION = (
    "Report baseline outputs are comparison artifacts only; they are not "
    "held-out evidence, methodological-validity evidence, or superiority evidence."
)
DEFAULT_REPORT_BASELINE_MODES: tuple[ReportBaselineMode, ...] = (
    "direct_report",
    "qa_report",
)
DEFAULT_QA_QUESTION_SET_ID = "reviewer_qa_v1"
DIRECT_REPORT_PROMPT_SPEC_ID = "transcript_direct_report_v1"
QA_REPORT_PROMPT_SPEC_ID = "transcript_qa_report_v1"

DEFAULT_QA_QUESTIONS: tuple[tuple[str, str], ...] = (
    (
        "q1_core_problem",
        "What core problem or phenomenon do participants describe?",
    ),
    (
        "q2_participant_positions",
        "What distinct positions do the participants take, and who holds them?",
    ),
    (
        "q3_consensus",
        "Where do participants converge?",
    ),
    (
        "q4_divergence",
        "Where do participants diverge or qualify each other?",
    ),
    (
        "q5_evidence",
        "What concrete evidence or examples do participants use to support their views?",
    ),
    (
        "q6_caveats",
        "What boundary conditions, uncertainties, or caveats should a reviewer keep in mind?",
    ),
    (
        "q7_recommendations",
        "What recommendations or next steps follow from the interviews, if any?",
    ),
)


class BaselineQuestionAnswer(BaseModel):
    """One QA-style response in the QA report baseline."""

    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(description="Stable ID of the fixed reviewer question being answered")
    question: str = Field(description="Reviewer question text copied from the fixed question set")
    answer: str = Field(description="Evidence-grounded answer based only on the transcript corpus")
    evidence_quotes: list[str] = Field(
        default_factory=list,
        description="Short transcript quotes that directly support the answer",
    )
    uncertainty: str = Field(
        default="",
        description="Local uncertainty, caveat, or boundary condition for this answer",
    )


class BaselineParticipantPosition(BaseModel):
    """One participant-level position extracted by the baseline."""

    model_config = ConfigDict(extra="forbid")

    participant_name: str = Field(description="Participant name, speaker label, or document-specific identity")
    role_or_context: str = Field(
        default="",
        description="Participant role, affiliation, document context, or empty string if unavailable",
    )
    position_summary: str = Field(
        description="Concise summary of the participant's supported stance or analytic position"
    )


class BaselineReportOutput(BaseModel):
    """Structured transcript-to-report baseline output."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="", description="Short reviewer-facing report title")
    executive_summary: str = Field(
        description="Brief synthesis of the transcript-only baseline's main analytic takeaways"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Major evidence-grounded findings supported by the transcript corpus",
    )
    participant_positions: list[BaselineParticipantPosition] = Field(
        default_factory=list,
        description="Participant-specific positions or stances recoverable from the transcripts",
    )
    consensus_points: list[str] = Field(
        default_factory=list,
        description="Points where participants converge or describe compatible views",
    )
    divergence_points: list[str] = Field(
        default_factory=list,
        description="Points where participants diverge, qualify, or emphasize different interpretations",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations or next steps explicitly grounded in transcript evidence",
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Scope limits, evidence gaps, uncertainty, or cautions for reviewers",
    )
    question_answers: list[BaselineQuestionAnswer] = Field(
        default_factory=list,
        description="QA-mode answers to the fixed reviewer question set; empty for direct-report mode",
    )
    report_markdown: str = Field(
        description="Readable Markdown report summarizing the same transcript-only baseline content"
    )


class ReportBaselineArtifact(BaseModel):
    """One generated baseline report in a versioned package."""

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    mode: ReportBaselineMode
    prompt_spec_id: str
    question_set_id: str | None = None
    output: BaselineReportOutput


class ReportBaselineRunMetadata(BaseModel):
    """Run metadata for a report-baseline generation package."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    project_name: str
    generated_at: str
    model_name: str
    baseline_modes: list[ReportBaselineMode]
    corpus_document_count: int
    max_chars_per_doc: int | None = None
    notes: str = ""

    @model_validator(mode="after")
    def require_nonempty_metadata(self) -> "ReportBaselineRunMetadata":
        if not self.project_id.strip():
            raise ValueError("Report baseline project_id must be non-empty")
        if not self.project_name.strip():
            raise ValueError("Report baseline project_name must be non-empty")
        if not self.model_name.strip():
            raise ValueError("Report baseline model_name must be non-empty")
        if not self.baseline_modes:
            raise ValueError("Report baseline run requires at least one baseline mode")
        return self


class ReportBaselinePackage(BaseModel):
    """Versioned transcript-to-report baseline package."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    package_type: Literal["qualitative_coding.report_baseline_outputs"]
    report_baseline_run: ReportBaselineRunMetadata
    report_baselines: list[ReportBaselineArtifact]
    caution: str = REPORT_BASELINE_PACKAGE_CAUTION

    @model_validator(mode="after")
    def require_consistent_modes(self) -> "ReportBaselinePackage":
        if not self.report_baselines:
            raise ValueError("Report baseline package requires at least one report_baselines row")
        package_modes = [artifact.mode for artifact in self.report_baselines]
        duplicates = sorted(mode for mode in set(package_modes) if package_modes.count(mode) > 1)
        if duplicates:
            raise ValueError("Duplicate report baseline mode(s): " + ", ".join(duplicates))
        expected = sorted(self.report_baseline_run.baseline_modes)
        actual = sorted(package_modes)
        if expected != actual:
            raise ValueError(
                "Report baseline run baseline_modes do not match artifact rows: "
                f"expected {expected}, found {actual}"
            )
        return self


def build_report_baseline_prompt(
    state: ProjectState,
    *,
    mode: ReportBaselineMode,
    max_chars_per_doc: int | None = None,
) -> str:
    """Build a transcript-only prompt for a reviewer-facing baseline report."""
    documents = [
        _copy_document(doc.name, doc.content[:max_chars_per_doc] if max_chars_per_doc else doc.content)
        for doc in state.corpus.documents
    ]
    scope_lines = _scope_lines(state)
    qa_lines = []
    if mode == "qa_report":
        qa_lines.extend(["", "Fixed reviewer question set:"])
        for question_id, question in DEFAULT_QA_QUESTIONS:
            qa_lines.append(f"- {question_id}: {question}")

    mode_instructions = {
        "direct_report": (
            "Write a fair qualitative report directly from the transcripts. "
            "Do not rely on any existing codes, claims, or system-generated analysis."
        ),
        "qa_report": (
            "Answer the fixed reviewer questions directly from the transcripts, "
            "then synthesize those answers into a short qualitative report. "
            "Do not rely on any existing codes, claims, or system-generated analysis."
        ),
    }[mode]

    return "\n".join([
        "You are producing a transcript-only comparison baseline for qualitative analysis.",
        mode_instructions,
        "Use only the transcript text and the stated corpus scope below.",
        "Distinguish participant positions, convergences, divergences, recommendations, and caveats.",
        "Do not invent facts, prevalence counts, or participant views not supported by the transcripts.",
        "",
        "Corpus scope:",
        *scope_lines,
        *qa_lines,
        "",
        "Transcript corpus:",
        format_untrusted_documents(documents, label_prefix="Transcript"),
    ])


async def generate_report_baseline_async(
    state: ProjectState,
    *,
    mode: ReportBaselineMode,
    model_name: str = "gpt-5-mini",
    max_chars_per_doc: int | None = None,
    trace_id: str = "qualitative_coding/report-baseline",
    max_budget: float = 5.0,
) -> ReportBaselineArtifact:
    """Generate one transcript-to-report baseline artifact."""
    llm = LLMHandler(model_name=model_name, temperature=0.2)
    prompt = build_report_baseline_prompt(
        state,
        mode=mode,
        max_chars_per_doc=max_chars_per_doc,
    )
    instructions = _baseline_output_instructions(mode)
    output = await llm.extract_structured(
        prompt,
        BaselineReportOutput,
        instructions=instructions,
        task="qualitative_coding.report_baseline",
        trace_id=f"{trace_id}/{mode}",
        max_budget=max_budget,
    )
    prompt_spec_id = (
        DIRECT_REPORT_PROMPT_SPEC_ID
        if mode == "direct_report"
        else QA_REPORT_PROMPT_SPEC_ID
    )
    return ReportBaselineArtifact(
        name=f"transcript_{mode}",
        description=_baseline_description(mode),
        mode=mode,
        prompt_spec_id=prompt_spec_id,
        question_set_id=DEFAULT_QA_QUESTION_SET_ID if mode == "qa_report" else None,
        output=output,
    )


async def export_report_baseline_package_async(
    state: ProjectState,
    *,
    modes: Sequence[ReportBaselineMode] = DEFAULT_REPORT_BASELINE_MODES,
    model_name: str = "gpt-5-mini",
    max_chars_per_doc: int | None = None,
    trace_id: str | None = None,
    max_budget: float = 5.0,
) -> dict:
    """Generate a versioned transcript-to-report baseline package."""
    selected_modes = list(modes) if modes else list(DEFAULT_REPORT_BASELINE_MODES)
    artifacts: list[ReportBaselineArtifact] = []
    base_trace_id = trace_id or f"qualitative_coding/report-baselines/{state.id}"
    for mode in selected_modes:
        artifacts.append(await generate_report_baseline_async(
            state,
            mode=mode,
            model_name=model_name,
            max_chars_per_doc=max_chars_per_doc,
            trace_id=base_trace_id,
            max_budget=max_budget,
        ))

    package = ReportBaselinePackage(
        schema_version=1,
        package_type=REPORT_BASELINE_PACKAGE_TYPE,
        report_baseline_run=ReportBaselineRunMetadata(
            project_id=state.id,
            project_name=state.name,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_name=model_name,
            baseline_modes=selected_modes,
            corpus_document_count=len(state.corpus.documents),
            max_chars_per_doc=max_chars_per_doc,
            notes=(
                "Transcript-only comparison baselines. These prompts intentionally do not "
                "use the repo's derived codes, claims, or memo artifacts."
            ),
        ),
        report_baselines=artifacts,
    )
    return package.model_dump(mode="json")


def _baseline_description(mode: ReportBaselineMode) -> str:
    if mode == "direct_report":
        return "Direct transcript-to-report baseline with a fair reviewer-facing analytic brief."
    return "Transcript-plus-fixed-QA baseline with synthesized reviewer-facing report output."


def _baseline_output_instructions(mode: ReportBaselineMode) -> str:
    qa_instruction = ""
    if mode == "qa_report":
        qa_instruction = (
            "Populate question_answers for every fixed reviewer question in order, "
            "using the provided question_id and question text."
        )
    else:
        qa_instruction = "Leave question_answers empty."
    return (
        "Return a reviewer-usable report in the required schema. "
        "Keep key_findings, consensus_points, divergence_points, recommendations, and "
        "caveats concise and evidence-grounded. "
        f"{qa_instruction} "
        "Use participant_positions for the main speaker-level stances you can support from the transcripts. "
        "report_markdown should be a readable Markdown report summarizing the same content."
    )


def _scope_lines(state: ProjectState) -> list[str]:
    if state.corpus_scope is None:
        return [
            "- No explicit corpus_scope object is present; infer cautiously from the document set only.",
        ]
    scope = state.corpus_scope
    lines = [
        f"- Phenomenon: {scope.phenomenon or 'not specified'}",
        f"- Population: {scope.population or 'not specified'}",
        f"- Sampling frame: {scope.sampling_frame or 'not specified'}",
    ]
    if scope.inclusion_criteria:
        lines.append("- Inclusion criteria: " + "; ".join(scope.inclusion_criteria))
    if scope.exclusion_criteria:
        lines.append("- Exclusion criteria: " + "; ".join(scope.exclusion_criteria))
    if scope.notes:
        lines.append(f"- Notes: {scope.notes}")
    return lines


class _PromptDocument:
    """Minimal document adapter for prompt rendering."""

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content


def _copy_document(name: str, content: str) -> _PromptDocument:
    return _PromptDocument(name=name, content=content)
