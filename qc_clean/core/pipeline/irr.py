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

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from qc_clean.schemas.domain import (
    IRRCodingPass,
    IRRResult,
    Methodology,
    ProjectState,
    StabilityResult,
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


def build_application_matrix(
    passes_segment_codes: List[Dict[str, set]],
) -> Dict[str, List[int]]:
    """Binary (segment × code) presence matrix for application-level agreement.

    ``passes_segment_codes[i]`` is ``{seg_key: {normalized_code_name, ...}}`` for
    pass i. Each row is one ``(segment, code)`` cell that was applied by at least
    one pass; the value is 1 if that pass assigned that code to that segment, else
    0. Reuses the same metric functions as codebook-discovery IRR — the only
    difference is the unit of analysis (segment×code vs. code).
    """
    cells = set()
    for sc in passes_segment_codes:
        for seg_key, codes in sc.items():
            for code in codes:
                cells.add((seg_key, code))

    matrix: Dict[str, List[int]] = {}
    for seg_key, code in sorted(cells):
        row = f"{seg_key}::{code}"
        matrix[row] = [1 if code in sc.get(seg_key, set()) else 0 for sc in passes_segment_codes]
    return matrix


def normalize_segment_decision(decision: Optional[str]) -> str:
    """Normalize exhaustive segment decisions for categorical agreement metrics."""
    if decision in {"coded", "no_code"}:
        return decision
    return "not_examined"


def build_segment_decision_matrix(
    passes_segment_decisions: List[Dict[str, str]],
) -> Dict[str, List[str]]:
    """Categorical segment-decision matrix for coded/no_code/not_examined agreement.

    ``passes_segment_decisions[i]`` is ``{seg_key: decision}`` for pass i. Missing
    or ``None`` decisions are represented as ``not_examined`` so skipped segment
    decisions are visible in the denominator instead of silently dropped.
    """
    segment_keys = set()
    for sd in passes_segment_decisions:
        segment_keys.update(sd.keys())

    matrix: Dict[str, List[str]] = {}
    for seg_key in sorted(segment_keys):
        matrix[seg_key] = [
            normalize_segment_decision(sd.get(seg_key))
            for sd in passes_segment_decisions
        ]
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


def compute_categorical_percent_agreement(matrix: Dict[str, List[str]]) -> float:
    """Proportion of categorical rows where all passes assign the same value."""
    if not matrix:
        return 0.0
    unanimous = sum(1 for row in matrix.values() if all(v == row[0] for v in row))
    return unanimous / len(matrix)


def compute_categorical_cohens_kappa(matrix: Dict[str, List[str]]) -> float:
    """Cohen's kappa for exactly 2 passes over categorical labels."""
    if not matrix:
        return 0.0
    rows = list(matrix.values())
    if len(rows[0]) != 2:
        raise ValueError("Cohen's kappa requires exactly 2 passes")

    n = len(rows)
    po = sum(1 for row in rows if row[0] == row[1]) / n
    categories = sorted({value for row in rows for value in row})
    pe = 0.0
    for cat in categories:
        p1 = sum(1 for row in rows if row[0] == cat) / n
        p2 = sum(1 for row in rows if row[1] == cat) / n
        pe += p1 * p2

    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def compute_categorical_fleiss_kappa(matrix: Dict[str, List[str]]) -> float:
    """Fleiss' kappa for 2+ passes over categorical labels."""
    if not matrix:
        return 0.0
    rows = list(matrix.values())
    n = len(rows)
    k = len(rows[0])
    if n == 0 or k == 0:
        return 0.0
    if k == 1:
        return 1.0

    categories = sorted({value for row in rows for value in row})
    p_bar = 0.0
    category_totals = {cat: 0 for cat in categories}
    for row in rows:
        counts = {cat: row.count(cat) for cat in categories}
        for cat, count in counts.items():
            category_totals[cat] += count
        p_i = sum(count * (count - 1) for count in counts.values()) / (k * (k - 1))
        p_bar += p_i
    p_bar /= n

    total_ratings = n * k
    p_e = sum((count / total_ratings) ** 2 for count in category_totals.values())
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
    application_level: bool = False,
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
    from qc_clean.core.pipeline.pipeline_engine import PipelineContext

    async def _run_one_pass(i: int) -> Tuple[IRRCodingPass, Dict[str, set], Dict[str, str]]:
        suffix = PROMPT_SUFFIXES[i % len(PROMPT_SUFFIXES)]
        pass_model = model_name
        if models:
            pass_model = models[i % len(models)]

        pass_state = state.model_copy(deep=True)
        pass_state.codebook.codes = []
        pass_state.code_applications = []

        ctx = PipelineContext(
            model_name=pass_model,
            irr_prompt_suffix=suffix,
            trace_id=f"qualitative_coding/irr/{state.id}/pass-{i + 1}",
            exhaustive_coding=application_level,  # per-segment decisions for app-level IRR
        )

        if is_gt:
            # Measure the ACTUAL GT pipeline stage (constant comparison), not the
            # legacy open-coding stage — otherwise reliability is reported for an
            # algorithm the pipeline no longer runs.
            from qc_clean.core.pipeline.stages.gt_constant_comparison import (
                GTConstantComparisonStage,
            )
            stage = GTConstantComparisonStage()
        else:
            from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage
            stage = ThematicCodingStage()

        logger.info("IRR pass %d/%d (model=%s, suffix=%r)", i + 1, num_passes, pass_model, suffix[:40])
        pass_state = await stage.execute(pass_state, ctx)

        code_names = [c.name for c in pass_state.codebook.codes]
        code_details = [
            {
                "name": c.name,
                "description": c.description,
                "quote_count": c.mention_count,
            }
            for c in pass_state.codebook.codes
        ]

        # For application-level IRR, derive:
        # - {seg_key: {normalized code names}} from positive applications
        # - {seg_key: coded/no_code/not_examined} from every segment decision
        seg_codes: Dict[str, set] = {}
        seg_decisions: Dict[str, str] = {}
        if application_level:
            id_to_name = {c.id: normalize_code_name(c.name) for c in pass_state.codebook.codes}
            for app in pass_state.code_applications:
                name = id_to_name.get(app.code_id)
                if name:
                    seg_codes.setdefault(f"{app.doc_id}#{app.start_char}", set()).add(name)
            for seg in pass_state.segments:
                seg_decisions[f"{seg.doc_id}#{seg.start_char}"] = normalize_segment_decision(seg.decision)

        return IRRCodingPass(
            pass_index=i,
            prompt_suffix=suffix,
            model_name=pass_model,
            codes_discovered=code_names,
            code_details=code_details,
            timestamp=datetime.now().isoformat(),
        ), seg_codes, seg_decisions

    pass_results = list(await asyncio.gather(*[_run_one_pass(i) for i in range(num_passes)]))
    passes = [pr[0] for pr in pass_results]
    seg_code_maps = [pr[1] for pr in pass_results]
    seg_decision_maps = [pr[2] for pr in pass_results]

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

    # Application-level metrics from exhaustive per-segment decisions:
    # 1. Positive segment × code cells (where any pass applied a code)
    # 2. Segment decision rows (coded/no_code/not_examined) over the segment universe
    app_matrix: Dict[str, List[int]] = {}
    app_pct = app_ck = app_fk = None
    app_interp = ""
    seg_decision_matrix: Dict[str, List[str]] = {}
    seg_decision_pct = seg_decision_ck = seg_decision_fk = None
    seg_decision_interp = ""
    if application_level:
        app_matrix = build_application_matrix(seg_code_maps)
        if app_matrix:
            app_pct = compute_percent_agreement(app_matrix)
            app_ck = compute_cohens_kappa(app_matrix) if num_passes == 2 else None
            app_fk = compute_fleiss_kappa(app_matrix)
            app_best = app_ck if app_ck is not None else app_fk
            app_interp = interpret_kappa(app_best) if app_best is not None else ""
        else:
            app_interp = "no positive code applications compared"

        seg_decision_matrix = build_segment_decision_matrix(seg_decision_maps)
        if seg_decision_matrix:
            seg_decision_pct = compute_categorical_percent_agreement(seg_decision_matrix)
            seg_decision_ck = (
                compute_categorical_cohens_kappa(seg_decision_matrix)
                if num_passes == 2 else None
            )
            seg_decision_fk = compute_categorical_fleiss_kappa(seg_decision_matrix)
            seg_decision_best = seg_decision_ck if seg_decision_ck is not None else seg_decision_fk
            seg_decision_interp = (
                interpret_kappa(seg_decision_best) if seg_decision_best is not None else ""
            )
        else:
            seg_decision_interp = "no segment decisions compared"

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
        application_level=application_level,
        application_units=len(app_matrix),
        application_percent_agreement=app_pct,
        application_cohens_kappa=app_ck,
        application_fleiss_kappa=app_fk,
        application_interpretation=app_interp,
        application_matrix=app_matrix,
        segment_decision_units=len(seg_decision_matrix),
        segment_decision_percent_agreement=seg_decision_pct,
        segment_decision_cohens_kappa=seg_decision_ck,
        segment_decision_fleiss_kappa=seg_decision_fk,
        segment_decision_interpretation=seg_decision_interp,
        segment_decision_matrix=seg_decision_matrix,
        timestamp=datetime.now().isoformat(),
    )

    logger.info(
        "IRR analysis complete: %d passes, %d aligned, %d unmatched, "
        "agreement=%.2f, kappa=%.3f (%s)",
        num_passes, len(aligned), len(unmatched),
        pct, best_kappa or 0.0, interp,
    )

    return result


# ---------------------------------------------------------------------------
# Multi-run stability analysis
# ---------------------------------------------------------------------------

def compute_code_stability(
    coding_matrix: Dict[str, List[int]],
) -> Dict[str, float]:
    """Compute per-code stability: fraction of runs each code appeared in."""
    result = {}
    for code, runs in coding_matrix.items():
        if runs:
            result[code] = sum(runs) / len(runs)
        else:
            result[code] = 0.0
    return result


def classify_stability(
    code_stability: Dict[str, float],
    stable_threshold: float = 0.8,
    moderate_threshold: float = 0.5,
) -> tuple[list[str], list[str], list[str]]:
    """Classify codes into stable/moderate/unstable based on stability scores."""
    stable = sorted(k for k, v in code_stability.items() if v >= stable_threshold)
    moderate = sorted(
        k for k, v in code_stability.items()
        if moderate_threshold <= v < stable_threshold
    )
    unstable = sorted(k for k, v in code_stability.items() if v < moderate_threshold)
    return stable, moderate, unstable


async def run_stability_analysis(
    state: ProjectState,
    num_runs: int = 5,
    model_name: str = "gpt-5-mini",
) -> StabilityResult:
    """
    Run identical coding passes to measure LLM output stability.

    Unlike IRR (which uses prompt variation), stability analysis uses
    the SAME prompt every time to quantify non-determinism.

    Parameters
    ----------
    state : ProjectState
        Project with corpus loaded (not modified).
    num_runs : int
        Number of identical runs (default 5).
    model_name : str
        Model to use for all runs.

    Returns
    -------
    StabilityResult
        Per-code stability scores and classification.
    """
    is_gt = state.config.methodology == Methodology.GROUNDED_THEORY
    from qc_clean.core.pipeline.pipeline_engine import PipelineContext

    async def _run_one(i: int) -> tuple[list[str], dict]:
        run_state = state.model_copy(deep=True)
        run_state.codebook.codes = []
        run_state.code_applications = []

        ctx = PipelineContext(
            model_name=model_name,
            trace_id=f"qualitative_coding/stability/{state.id}/run-{i + 1}",
        )

        if is_gt:
            # Measure the actual GT pipeline stage (constant comparison), not legacy.
            from qc_clean.core.pipeline.stages.gt_constant_comparison import (
                GTConstantComparisonStage,
            )
            stage = GTConstantComparisonStage()
        else:
            from qc_clean.core.pipeline.stages.thematic_coding import ThematicCodingStage
            stage = ThematicCodingStage()

        logger.info("Stability run %d/%d (model=%s)", i + 1, num_runs, model_name)
        run_state = await stage.execute(run_state, ctx)

        code_names = [c.name for c in run_state.codebook.codes]
        details = {
            "run_index": i,
            "model_name": model_name,
            "num_codes": len(code_names),
            "codes": code_names,
            "timestamp": datetime.now().isoformat(),
        }
        return code_names, details

    results = list(await asyncio.gather(*[_run_one(i) for i in range(num_runs)]))
    all_run_codes = [codes for codes, _ in results]
    run_details = [details for _, details in results]

    # Build presence matrix over ALL unique codes across all runs
    all_unique_norm = set()
    for run_codes in all_run_codes:
        for code in run_codes:
            all_unique_norm.add(normalize_code_name(code))
    all_unique = sorted(all_unique_norm)

    matrix = build_coding_matrix(all_run_codes, all_unique)
    code_stability = compute_code_stability(matrix)
    stable, moderate, unstable = classify_stability(code_stability)

    overall = sum(code_stability.values()) / max(len(code_stability), 1)

    result = StabilityResult(
        num_runs=num_runs,
        code_stability=code_stability,
        stable_codes=stable,
        moderate_codes=moderate,
        unstable_codes=unstable,
        overall_stability=overall,
        coding_matrix=matrix,
        run_details=run_details,
        model_name=model_name,
        timestamp=datetime.now().isoformat(),
    )

    logger.info(
        "Stability analysis complete: %d runs, %d stable, %d moderate, %d unstable, "
        "overall=%.2f",
        num_runs, len(stable), len(moderate), len(unstable), overall,
    )

    return result
