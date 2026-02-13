"""
Inter-Rater Reliability (IRR) analysis.

Runs the coding stage multiple times with prompt variation, aligns codes
across passes, and computes agreement metrics (percent agreement,
Cohen's kappa, Fleiss' kappa).

References:
- Landis & Koch (1977) for kappa interpretation
- Cohen (1960) for 2-rater kappa
- Fleiss (1971) for multi-rater kappa
"""

from __future__ import annotations

import copy
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from qc_clean.schemas.domain import (
    IRRCodingPass,
    IRRResult,
    Methodology,
    ProjectState,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt variation suffixes
# ---------------------------------------------------------------------------

PROMPT_SUFFIXES = [
    "",  # baseline
    "Focus especially on capturing nuanced, less obvious themes.",
    "Prioritize themes most strongly supported by direct evidence in the text.",
    "Consider both manifest (explicitly stated) and latent (implied) themes.",
    "Pay particular attention to themes reflecting tensions or contradictions.",
]


# ---------------------------------------------------------------------------
# Pure functions (no I/O, fully testable)
# ---------------------------------------------------------------------------

def normalize_code_name(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    name = name.lower().strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def align_codes(
    passes: List[List[str]],
) -> Tuple[List[str], List[str]]:
    """
    Align code names across passes.

    A code is 'aligned' if it appears (after normalization) in >= 2 passes.
    Returns (aligned_codes, unmatched_codes).
    """
    # Count how many passes each normalized code appears in
    code_pass_count: Dict[str, int] = {}
    for pass_codes in passes:
        seen_in_pass: set = set()
        for code in pass_codes:
            norm = normalize_code_name(code)
            if norm and norm not in seen_in_pass:
                code_pass_count[norm] = code_pass_count.get(norm, 0) + 1
                seen_in_pass.add(norm)

    aligned = sorted(k for k, v in code_pass_count.items() if v >= 2)
    unmatched = sorted(k for k, v in code_pass_count.items() if v < 2)
    return aligned, unmatched


def build_coding_matrix(
    passes: List[List[str]],
    aligned_codes: List[str],
) -> Dict[str, List[int]]:
    """
    Build a binary presence matrix: {code_name: [0_or_1_per_pass]}.

    Each column is a pass; each row is an aligned code.
    Value is 1 if that pass discovered the code, 0 otherwise.
    """
    # Pre-compute normalized sets per pass
    pass_sets = []
    for pass_codes in passes:
        pass_sets.append({normalize_code_name(c) for c in pass_codes})

    matrix: Dict[str, List[int]] = {}
    for code in aligned_codes:
        matrix[code] = [1 if code in ps else 0 for ps in pass_sets]
    return matrix


def compute_percent_agreement(matrix: Dict[str, List[int]]) -> float:
    """Proportion of codes where all passes agree (all 1 or all 0)."""
    if not matrix:
        return 0.0
    n_codes = len(matrix)
    unanimous = 0
    for row in matrix.values():
        if all(v == 1 for v in row) or all(v == 0 for v in row):
            unanimous += 1
    return unanimous / n_codes


def compute_cohens_kappa(matrix: Dict[str, List[int]]) -> float:
    """
    Cohen's kappa for exactly 2 passes.

    Treats each code as a binary rating (present/absent).
    """
    if not matrix:
        return 0.0
    rows = list(matrix.values())
    n = len(rows)
    if n == 0:
        return 0.0

    # Ensure 2 passes
    if len(rows[0]) != 2:
        raise ValueError("Cohen's kappa requires exactly 2 passes")

    # Count agreement cells
    a = sum(1 for r in rows if r[0] == 1 and r[1] == 1)  # both present
    b = sum(1 for r in rows if r[0] == 1 and r[1] == 0)  # pass1 only
    c = sum(1 for r in rows if r[0] == 0 and r[1] == 1)  # pass2 only
    d = sum(1 for r in rows if r[0] == 0 and r[1] == 0)  # both absent

    po = (a + d) / n  # observed agreement
    # Expected agreement
    p1_yes = (a + b) / n
    p2_yes = (a + c) / n
    pe = p1_yes * p2_yes + (1 - p1_yes) * (1 - p2_yes)

    if pe == 1.0:
        return 1.0  # perfect agreement by chance
    return (po - pe) / (1 - pe)


def compute_fleiss_kappa(matrix: Dict[str, List[int]]) -> float:
    """
    Fleiss' kappa for 2+ passes.

    Each code is a 'subject', each pass is a 'rater', and the rating
    is binary (present=1 / absent=0).
    """
    if not matrix:
        return 0.0
    rows = list(matrix.values())
    n = len(rows)  # number of subjects (codes)
    k = len(rows[0])  # number of raters (passes)

    if n == 0 or k == 0:
        return 0.0

    # For binary categories (0 and 1):
    # P_i = (1 / (k*(k-1))) * (n_i1*(n_i1-1) + n_i0*(n_i0-1))
    # where n_i1 = count of 1s in row i, n_i0 = count of 0s
    p_bar = 0.0
    for row in rows:
        n_present = sum(row)
        n_absent = k - n_present
        p_i = (n_present * (n_present - 1) + n_absent * (n_absent - 1)) / (k * (k - 1))
        p_bar += p_i
    p_bar /= n

    # P_e = sum over categories of (proportion)^2
    total_ratings = n * k
    total_present = sum(sum(row) for row in rows)
    p_present = total_present / total_ratings
    p_absent = 1 - p_present
    p_e = p_present ** 2 + p_absent ** 2

    if p_e == 1.0:
        return 1.0
    return (p_bar - p_e) / (1 - p_e)


def interpret_kappa(kappa: float) -> str:
    """Interpret kappa using Landis & Koch (1977) scale."""
    if kappa < 0.0:
        return "poor"
    elif kappa < 0.21:
        return "slight"
    elif kappa < 0.41:
        return "fair"
    elif kappa < 0.61:
        return "moderate"
    elif kappa < 0.81:
        return "substantial"
    else:
        return "almost perfect"


# ---------------------------------------------------------------------------
# Async orchestrator
# ---------------------------------------------------------------------------

async def run_irr_analysis(
    state: ProjectState,
    num_passes: int = 3,
    model_name: str = "gpt-5-mini",
    models: Optional[List[str]] = None,
) -> IRRResult:
    """
    Run multiple coding passes and compute IRR metrics.

    Parameters
    ----------
    state : ProjectState
        Project with corpus loaded (codes will NOT be modified on the
        original state -- each pass operates on a fresh copy).
    num_passes : int
        Number of independent coding passes (default 3).
    model_name : str
        Default model for all passes unless ``models`` is specified.
    models : list[str], optional
        Per-pass model names (cycles if shorter than num_passes).

    Returns
    -------
    IRRResult
        Populated with passes, aligned codes, matrix, and metrics.
    """
    is_gt = state.config.methodology == Methodology.GROUNDED_THEORY

    passes: List[IRRCodingPass] = []

    for i in range(num_passes):
        suffix = PROMPT_SUFFIXES[i % len(PROMPT_SUFFIXES)]
        pass_model = model_name
        if models:
            pass_model = models[i % len(models)]

        # Fresh state copy: keep corpus, reset codes
        pass_state = state.model_copy(deep=True)
        pass_state.codebook.codes = []
        pass_state.code_applications = []

        config = {
            "model_name": pass_model,
            "irr_prompt_suffix": suffix,
        }

        # Run the appropriate coding stage
        if is_gt:
            from qc_clean.core.pipeline.stages.gt_open_coding import GTOpenCodingStage
            stage = GTOpenCodingStage()
        else:
            from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage
            stage = ThematicCodingStage()

        logger.info("IRR pass %d/%d (model=%s, suffix=%r)", i + 1, num_passes, pass_model, suffix[:40])
        pass_state = await stage.execute(pass_state, config)

        code_names = [c.name for c in pass_state.codebook.codes]
        code_details = [
            {
                "name": c.name,
                "description": c.description,
                "quote_count": c.mention_count,
            }
            for c in pass_state.codebook.codes
        ]

        passes.append(IRRCodingPass(
            pass_index=i,
            prompt_suffix=suffix,
            model_name=pass_model,
            codes_discovered=code_names,
            code_details=code_details,
            timestamp=datetime.now().isoformat(),
        ))

    # Compute metrics
    all_pass_codes = [p.codes_discovered for p in passes]
    aligned, unmatched = align_codes(all_pass_codes)

    # Build matrix over ALL unique codes (aligned + unmatched)
    all_unique = aligned + unmatched
    matrix = build_coding_matrix(all_pass_codes, all_unique)

    pct = compute_percent_agreement(matrix)

    ck = None
    if num_passes == 2:
        ck = compute_cohens_kappa(matrix)

    fk = compute_fleiss_kappa(matrix)

    best_kappa = ck if ck is not None else fk
    interp = interpret_kappa(best_kappa) if best_kappa is not None else ""

    result = IRRResult(
        num_passes=num_passes,
        passes=passes,
        aligned_codes=aligned,
        unmatched_codes=unmatched,
        coding_matrix=matrix,
        percent_agreement=pct,
        cohens_kappa=ck,
        fleiss_kappa=fk,
        interpretation=interp,
        timestamp=datetime.now().isoformat(),
    )

    logger.info(
        "IRR analysis complete: %d passes, %d aligned, %d unmatched, "
        "agreement=%.2f, kappa=%.3f (%s)",
        num_passes, len(aligned), len(unmatched),
        pct, best_kappa or 0.0, interp,
    )

    return result
