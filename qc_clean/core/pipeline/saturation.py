"""
Saturation detection: compare codebooks across iterations
to determine when coding has stabilized.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from qc_clean.schemas.domain import (
    CategorySaturationDiagnostic,
    CategorySaturationSummary,
    Codebook,
    CodebookChangeResult,
    ProjectState,
    SaturationCheckResult,
)

logger = logging.getLogger(__name__)


def calculate_codebook_change(old: Codebook, new: Codebook) -> CodebookChangeResult:
    """
    Compare two codebooks and return change metrics.

    Returns a CodebookChangeResult with pct_change, added/removed/modified/stable codes.
    """
    old_names = {c.name for c in old.codes}
    new_names = {c.name for c in new.codes}

    added = new_names - old_names
    removed = old_names - new_names
    common = old_names & new_names

    old_by_name = {c.name: c for c in old.codes}
    new_by_name = {c.name: c for c in new.codes}

    modified = []
    stable = []
    for name in common:
        oc = old_by_name[name]
        nc = new_by_name[name]
        if (
            oc.description != nc.description
            or abs(oc.confidence - nc.confidence) > 0.1
            or oc.parent_id != nc.parent_id
        ):
            modified.append(name)
        else:
            stable.append(name)

    total_codes = max(len(old_names | new_names), 1)
    changed_count = len(added) + len(removed) + len(modified)
    pct_change = changed_count / total_codes

    return CodebookChangeResult(
        pct_change=pct_change,
        added_codes=sorted(added),
        removed_codes=sorted(removed),
        modified_codes=sorted(modified),
        stable_codes=sorted(stable),
        old_code_count=len(old.codes),
        new_code_count=len(new.codes),
    )


def check_saturation(
    state: ProjectState,
    threshold: float = 0.15,
) -> SaturationCheckResult:
    """
    Check if coding has reached saturation.

    Compares the current codebook against the most recent entry in
    ``codebook_history``.  If the change is below *threshold*, saturation
    is reached.
    """
    if not state.codebook_history:
        return SaturationCheckResult(
            saturated=False,
            change_metrics=None,
            iteration=state.iteration,
            message="First iteration -- no previous codebook to compare.",
        )

    previous = state.codebook_history[-1]
    metrics = calculate_codebook_change(previous, state.codebook)
    saturated = metrics.pct_change < threshold

    if saturated:
        msg = (
            f"Codebook stability reached at iteration {state.iteration}: "
            f"{metrics.pct_change:.1%} change (threshold={threshold:.0%}). "
            f"{len(metrics.stable_codes)} codes stable. "
            f"(Codebook convergence, NOT grounded-theory category saturation — INV-4.)"
        )
    else:
        msg = (
            f"Not yet saturated at iteration {state.iteration}: "
            f"{metrics.pct_change:.1%} change (threshold={threshold:.0%}). "
            f"Added={len(metrics.added_codes)}, removed={len(metrics.removed_codes)}, "
            f"modified={len(metrics.modified_codes)}."
        )

    logger.info(msg)
    return SaturationCheckResult(
        saturated=saturated,
        change_metrics=metrics,
        iteration=state.iteration,
        message=msg,
    )


def assess_category_saturation(
    state: ProjectState,
    *,
    min_properties: int = 1,
    min_dimensions: int = 1,
    min_supporting_applications: int = 1,
    min_supporting_documents: int = 1,
) -> CategorySaturationSummary:
    """Return a diagnostic-only category adequacy report for INV-4."""
    if min_properties < 0 or min_dimensions < 0:
        raise ValueError("Category saturation property/dimension thresholds must be non-negative")
    if min_supporting_applications < 0 or min_supporting_documents < 0:
        raise ValueError("Category saturation support thresholds must be non-negative")

    applications_by_code: dict[str, int] = defaultdict(int)
    documents_by_code: dict[str, set[str]] = defaultdict(set)
    for application in state.code_applications:
        applications_by_code[application.code_id] += 1
        documents_by_code[application.code_id].add(application.doc_id)

    categories: list[CategorySaturationDiagnostic] = []
    for code in state.codebook.codes:
        property_count = len(code.properties)
        dimension_count = len(code.dimensions)
        supporting_application_count = applications_by_code.get(code.id, 0)
        supporting_document_count = len(documents_by_code.get(code.id, set()))
        gaps = []
        if property_count < min_properties:
            gaps.append("needs_properties")
        if dimension_count < min_dimensions:
            gaps.append("needs_dimensions")
        if supporting_application_count < min_supporting_applications:
            gaps.append("needs_supporting_applications")
        if supporting_document_count < min_supporting_documents:
            gaps.append("needs_supporting_documents")

        if not gaps:
            status = "adequate"
        elif property_count or dimension_count or supporting_application_count:
            status = "developing"
        else:
            status = "underdeveloped"

        categories.append(CategorySaturationDiagnostic(
            code_id=code.id,
            code_name=code.name,
            property_count=property_count,
            dimension_count=dimension_count,
            supporting_application_count=supporting_application_count,
            supporting_document_count=supporting_document_count,
            status=status,
            gaps=gaps,
        ))

    adequate_count = sum(1 for category in categories if category.status == "adequate")
    developing_count = sum(1 for category in categories if category.status == "developing")
    underdeveloped_count = sum(1 for category in categories if category.status == "underdeveloped")
    all_adequate = bool(categories) and adequate_count == len(categories)
    status = "diagnostic" if categories else "not_available"
    note = (
        "Category saturation diagnostic only; not proof of grounded-theory saturation. "
        "Use to identify weak categories for theoretical sampling, not to claim theory adequacy."
    )
    if not categories:
        note = (
            "Category saturation diagnostic unavailable because the codebook has no categories. "
            "This is not proof of grounded-theory saturation."
        )

    return CategorySaturationSummary(
        status=status,
        categories=categories,
        all_categories_adequate=all_adequate,
        adequate_count=adequate_count,
        developing_count=developing_count,
        underdeveloped_count=underdeveloped_count,
        min_properties=min_properties,
        min_dimensions=min_dimensions,
        min_supporting_applications=min_supporting_applications,
        min_supporting_documents=min_supporting_documents,
        note=note,
    )
