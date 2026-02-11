"""
Saturation detection: compare codebooks across iterations
to determine when coding has stabilized.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from qc_clean.schemas.domain import Codebook, ProjectState

logger = logging.getLogger(__name__)


def calculate_codebook_change(old: Codebook, new: Codebook) -> Dict:
    """
    Compare two codebooks and return change metrics.

    Returns a dict with:
    - pct_change: overall change percentage (0.0-1.0)
    - added_codes: list of code names added
    - removed_codes: list of code names removed
    - modified_codes: list of code names where confidence or description changed
    - stable_codes: list of code names unchanged
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

    return {
        "pct_change": pct_change,
        "added_codes": sorted(added),
        "removed_codes": sorted(removed),
        "modified_codes": sorted(modified),
        "stable_codes": sorted(stable),
        "old_code_count": len(old.codes),
        "new_code_count": len(new.codes),
    }


def check_saturation(
    state: ProjectState,
    threshold: float = 0.15,
) -> Dict:
    """
    Check if coding has reached saturation.

    Compares the current codebook against the most recent entry in
    ``codebook_history``.  If the change is below *threshold*, saturation
    is reached.

    Returns a dict with:
    - saturated: bool
    - change_metrics: output of calculate_codebook_change (or None)
    - iteration: current iteration number
    - message: human-readable summary
    """
    if not state.codebook_history:
        return {
            "saturated": False,
            "change_metrics": None,
            "iteration": state.iteration,
            "message": "First iteration -- no previous codebook to compare.",
        }

    previous = state.codebook_history[-1]
    metrics = calculate_codebook_change(previous, state.codebook)
    saturated = metrics["pct_change"] < threshold

    if saturated:
        msg = (
            f"Saturation reached at iteration {state.iteration}: "
            f"{metrics['pct_change']:.1%} change (threshold={threshold:.0%}). "
            f"{len(metrics['stable_codes'])} codes stable."
        )
    else:
        msg = (
            f"Not yet saturated at iteration {state.iteration}: "
            f"{metrics['pct_change']:.1%} change (threshold={threshold:.0%}). "
            f"Added={len(metrics['added_codes'])}, removed={len(metrics['removed_codes'])}, "
            f"modified={len(metrics['modified_codes'])}."
        )

    logger.info(msg)
    return {
        "saturated": saturated,
        "change_metrics": metrics,
        "iteration": state.iteration,
        "message": msg,
    }
