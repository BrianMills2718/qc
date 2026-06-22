"""Deterministic lint for corpus-scope-sensitive report phrasing."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

from qc_clean.schemas.domain import ProjectState


ScopeLintStatus = Literal["pass", "warn"]
ScopeStatus = Literal["missing", "empty", "missing_sampling_frame", "complete"]

RISKY_PHRASE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "generalization_term",
        re.compile(r"\bgeneraliz(?:e|es|ed|ing|able|ability)\b", re.IGNORECASE),
    ),
    ("representative", re.compile(r"\brepresentative(?:\s+of)?\b", re.IGNORECASE)),
    (
        "population_language",
        re.compile(r"\b(?:broader\s+)?population(?:-level)?\b", re.IGNORECASE),
    ),
    (
        "broad_across_group",
        re.compile(
            r"\b(?:across|among)\s+(?:the\s+)?(?:[A-Za-z-]+\s+){0,3}"
            r"(?:teams|participants|respondents|users|workers|clinics|"
            r"organizations|patients|families|managers|leaders|employees)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "broad_quantified_group",
        re.compile(
            r"\b(?:all|most|many|typical)\s+(?:[A-Za-z-]+\s+){0,3}"
            r"(?:teams|participants|respondents|users|workers|clinics|"
            r"organizations|patients|families|managers|leaders|employees)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "generally_group",
        re.compile(
            r"\b(?:teams|participants|respondents|users|workers|clinics|"
            r"organizations|patients|families|managers|leaders|employees|"
            r"sector|industry|field)\s+generally\b|"
            r"\bin\s+(?:the\s+)?(?:sector|industry|field)\s+generally\b",
            re.IGNORECASE,
        ),
    ),
)

WARNING_CODE_BY_SCOPE_STATUS: dict[ScopeStatus, str] = {
    "missing": "missing_corpus_scope_generalization",
    "empty": "empty_corpus_scope_generalization",
    "missing_sampling_frame": "missing_sampling_frame_generalization",
    "complete": "complete_scope_generalization",
}

WARNING_MESSAGE_BY_SCOPE_STATUS: dict[ScopeStatus, str] = {
    "missing": (
        "No corpus scope is recorded. Risky population-generalizing phrasing "
        "must be bounded to the loaded documents only."
    ),
    "empty": (
        "A corpus scope record exists, but no scope details are specified. "
        "Risky population-generalizing phrasing must be bounded to the loaded "
        "documents only."
    ),
    "missing_sampling_frame": (
        "A corpus population is recorded without a sampling frame. Risky "
        "population-generalizing phrasing must not treat the population field "
        "as a defensible generalization boundary."
    ),
    "complete": (
        "Corpus scope has enough boundary detail for this lint; this does not "
        "validate sampling adequacy."
    ),
}

SCOPE_LINT_CAVEAT = (
    "Scope phrasing lint is report discipline only; it is not sampling adequacy "
    "evidence, not validity evidence, and not proof that claims are correct."
)


class ScopePhrasingWarning(BaseModel):
    """One scope-sensitive wording warning."""

    code: str = Field(description="Stable warning code")
    source: str = Field(description="Text source label supplied by the caller")
    line_number: int = Field(description="One-indexed line number")
    matched_text: str = Field(description="Exact text span that matched a risky pattern")
    pattern: str = Field(description="Risky phrase pattern identifier")
    message: str = Field(description="Human-readable warning")


class ScopePhrasingLintReport(BaseModel):
    """Scope-sensitive wording lint report."""

    status: ScopeLintStatus = Field(description="Overall lint status")
    scope_status: ScopeStatus = Field(description="Corpus-scope status used by the lint")
    source: str = Field(description="Text source label supplied by the caller")
    warning_count: int = Field(description="Number of phrasing warnings")
    warnings: list[ScopePhrasingWarning] = Field(description="Line-level phrasing warnings")
    caveat: str = Field(description="Claim-discipline caveat for the lint")


def scope_status_for_lint(state: ProjectState) -> ScopeStatus:
    """Classify corpus scope completeness for phrasing lint policy."""
    if state.corpus_scope is None:
        return "missing"

    scope = state.corpus_scope
    has_detail = any(
        [
            scope.phenomenon,
            scope.population,
            scope.sampling_frame,
            scope.inclusion_criteria,
            scope.exclusion_criteria,
            scope.notes,
        ]
    )
    if not has_detail:
        return "empty"
    if scope.population and not scope.sampling_frame:
        return "missing_sampling_frame"
    return "complete"


def lint_scope_phrasing(
    state: ProjectState,
    text: str,
    *,
    source: str = "text",
) -> ScopePhrasingLintReport:
    """Lint report text for unsafe scope phrasing under the project's boundary."""
    scope_status = scope_status_for_lint(state)
    warnings: list[ScopePhrasingWarning] = []

    if scope_status != "complete":
        code = WARNING_CODE_BY_SCOPE_STATUS[scope_status]
        message = WARNING_MESSAGE_BY_SCOPE_STATUS[scope_status]
        for line_number, line in enumerate(text.splitlines() or [text], start=1):
            warnings.extend(
                ScopePhrasingWarning(
                    code=code,
                    source=source,
                    line_number=line_number,
                    matched_text=match.group(0),
                    pattern=pattern_name,
                    message=message,
                )
                for pattern_name, pattern in RISKY_PHRASE_PATTERNS
                for match in pattern.finditer(line)
            )

    return ScopePhrasingLintReport(
        status="warn" if warnings else "pass",
        scope_status=scope_status,
        source=source,
        warning_count=len(warnings),
        warnings=warnings,
        caveat=SCOPE_LINT_CAVEAT,
    )
