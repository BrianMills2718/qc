#!/usr/bin/env python3
"""
Qualitative Coding MCP Server

Exposes the qualitative coding system as MCP tools:
- Project management (create, list, show, delete)
- Pipeline execution (run analysis)
- Codebook inspection (codes, applications, memos)
- Export (JSON, CSV, Markdown)
- Review (get pending, approve all)

Wraps existing ProjectStore, ProjectExporter, and ReviewManager.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.core.pipeline.review import ReviewManager
from qc_clean.core.pipeline.pipeline_factory import create_pipeline, create_incremental_pipeline
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.irr import run_irr_analysis, run_stability_analysis
from qc_clean.schemas.domain import (
    Document,
    HumanReviewDecision,
    Methodology,
    PipelineStatus,
    ProjectConfig,
    ProjectState,
    ReviewAction,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("qualitative-coding")
store = ProjectStore()
exporter = ProjectExporter()


@mcp.tool()
def qc_list_projects() -> str:
    """List all qualitative coding projects.

    Returns project summaries with id, name, status, and last update time.
    """
    projects = store.list_projects()
    if not projects:
        return json.dumps({"message": "No projects found. Create one with qc_create_project."})
    return json.dumps(projects, indent=2)


@mcp.tool()
def qc_create_project(
    name: str,
    methodology: str = "thematic_analysis",
) -> str:
    """Create a new qualitative coding project.

    Args:
        name: Project name (e.g. "Interview Study 2026")
        methodology: "thematic_analysis" (default) or "grounded_theory"
    """
    try:
        meth = Methodology(methodology)
    except ValueError:
        return json.dumps({
            "error": f"Invalid methodology '{methodology}'. Use 'thematic_analysis' or 'grounded_theory'."
        })

    config = ProjectConfig(methodology=meth)
    state = ProjectState(name=name, config=config)
    path = store.save(state)
    return json.dumps({
        "project_id": state.id,
        "name": state.name,
        "methodology": meth.value,
        "saved_to": str(path),
    })


@mcp.tool()
def qc_show_project(project_id: str) -> str:
    """Show details of a qualitative coding project.

    Returns project metadata, pipeline status, code count, application count,
    document count, and memo count.

    Args:
        project_id: The project ID (from qc_list_projects)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    phase_results = [
        {"phase": pr.phase_name, "status": pr.status.value}
        for pr in state.phase_results
    ]
    return json.dumps({
        "id": state.id,
        "name": state.name,
        "methodology": state.config.methodology.value,
        "pipeline_status": state.pipeline_status.value,
        "current_phase": state.current_phase,
        "documents": state.corpus.num_documents,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        "memos": len(state.memos),
        "entities": len(state.entities),
        "phase_results": phase_results,
        "updated_at": state.updated_at,
    }, indent=2)


@mcp.tool()
def qc_get_codebook(project_id: str) -> str:
    """Get the codebook (all codes) for a project.

    Returns hierarchical codes with names, descriptions, mention counts,
    confidence scores, and provenance (LLM vs human).

    Args:
        project_id: The project ID
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    codes = []
    for code in state.codebook.codes:
        codes.append({
            "id": code.id,
            "name": code.name,
            "description": code.description,
            "parent_id": code.parent_id,
            "level": code.level,
            "mention_count": code.mention_count,
            "confidence": round(code.confidence, 2),
            "provenance": code.provenance.value,
            "reasoning": code.reasoning,
        })
    return json.dumps({
        "project": state.name,
        "codebook_version": state.codebook.version,
        "code_count": len(codes),
        "codes": codes,
    }, indent=2)


@mcp.tool()
def qc_get_applications(project_id: str, code_name: str | None = None, limit: int = 50) -> str:
    """Get code applications (quotes tagged with codes) for a project.

    Args:
        project_id: The project ID
        code_name: Optional filter by code name (partial match)
        limit: Maximum number of applications to return (default 50)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    code_names = {c.id: c.name for c in state.codebook.codes}
    doc_names = {d.id: d.name for d in state.corpus.documents}

    apps = state.code_applications
    if code_name:
        matching_ids = {
            c.id for c in state.codebook.codes
            if code_name.lower() in c.name.lower()
        }
        apps = [a for a in apps if a.code_id in matching_ids]

    results = []
    for app in apps[:limit]:
        results.append({
            "id": app.id,
            "code": code_names.get(app.code_id, app.code_id),
            "document": doc_names.get(app.doc_id, app.doc_id),
            "speaker": app.speaker,
            "quote": app.quote_text,
            "confidence": round(app.confidence, 2),
        })

    return json.dumps({
        "project": state.name,
        "total_applications": len(state.code_applications),
        "returned": len(results),
        "applications": results,
    }, indent=2)


@mcp.tool()
def qc_get_memos(project_id: str) -> str:
    """Get analytical memos from a project.

    Memos are the LLM's reasoning trail - reflective notes generated
    at each pipeline stage about emerging patterns, uncertainties, and insights.

    Args:
        project_id: The project ID
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    memos = []
    for memo in state.memos:
        memos.append({
            "id": memo.id,
            "type": memo.memo_type,
            "title": memo.title,
            "content": memo.content,
            "code_refs": memo.code_refs,
            "doc_refs": memo.doc_refs,
            "created_by": memo.created_by.value,
            "created_at": memo.created_at,
        })

    return json.dumps({
        "project": state.name,
        "memo_count": len(memos),
        "memos": memos,
    }, indent=2)


@mcp.tool()
def qc_get_synthesis(project_id: str) -> str:
    """Get the synthesis (key findings, recommendations) from a project.

    Only available after the synthesis pipeline stage has completed.

    Args:
        project_id: The project ID
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if not state.synthesis:
        return json.dumps({"message": "No synthesis available. Run the pipeline first."})

    synth = state.synthesis
    return json.dumps({
        "project": state.name,
        "executive_summary": synth.executive_summary,
        "key_findings": synth.key_findings,
        "recommendations": [
            {"title": r.title, "priority": r.priority, "description": r.description}
            for r in (synth.recommendations or [])
        ],
    }, indent=2)


@mcp.tool()
def qc_export_markdown(project_id: str, output_file: str | None = None) -> str:
    """Export a project as a human-readable Markdown report.

    Includes executive summary, codebook, key quotes, memos,
    entity relationships, and audit trail.

    Args:
        project_id: The project ID
        output_file: Optional output file path (default: {project_name}_report.md)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    path = exporter.export_markdown(state, output_file)
    return json.dumps({"exported_to": path, "format": "markdown"})


@mcp.tool()
def qc_export_json(project_id: str, output_file: str | None = None) -> str:
    """Export a project's full state as JSON.

    Args:
        project_id: The project ID
        output_file: Optional output file path (default: {project_name}.json)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    path = exporter.export_json(state, output_file)
    return json.dumps({"exported_to": path, "format": "json"})


@mcp.tool()
def qc_review_summary(project_id: str) -> str:
    """Get a review summary for a project — how many codes and applications need review.

    Args:
        project_id: The project ID
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    rm = ReviewManager(state)
    summary = rm.get_review_summary()
    result = summary.model_dump()
    result["can_resume"] = rm.can_resume()
    return json.dumps(result, indent=2)


@mcp.tool()
def qc_approve_all_codes(project_id: str) -> str:
    """Approve all codes in a project's codebook and save.

    Marks all LLM-generated codes as human-approved. Use after reviewing
    the codebook with qc_get_codebook.

    Args:
        project_id: The project ID
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    rm = ReviewManager(state)
    result = rm.approve_all_codes()
    store.save(state)
    return json.dumps({
        "approved": result["applied"],
        "message": f"Approved {result['applied']} codes. Project saved.",
    })


@mcp.tool()
def qc_delete_project(project_id: str) -> str:
    """Delete a qualitative coding project.

    This permanently removes the project file. Cannot be undone.

    Args:
        project_id: The project ID to delete
    """
    deleted = store.delete(project_id)
    if deleted:
        return json.dumps({"message": f"Project '{project_id}' deleted."})
    return json.dumps({"error": f"Project '{project_id}' not found."})


# ---------------------------------------------------------------------------
# Document management
# ---------------------------------------------------------------------------

@mcp.tool()
def qc_add_documents(
    project_id: str,
    documents: List[Dict[str, str]],
) -> str:
    """Add documents to a project.

    Each document is a dict with 'name' and 'content' keys. The agent reads
    files and passes content as text — no file paths needed.

    Args:
        project_id: The project ID
        documents: List of {"name": "interview1.txt", "content": "transcript text..."}
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if not documents:
        return json.dumps({"error": "No documents provided."})

    added = 0
    for doc_data in documents:
        name = doc_data.get("name", "")
        content = doc_data.get("content", "")
        if not name:
            return json.dumps({"error": "Each document must have a 'name' field."})
        doc = Document(name=name, content=content)
        state.corpus.add_document(doc)
        added += 1

    store.save(state)
    return json.dumps({
        "added": added,
        "total_documents": state.corpus.num_documents,
    })


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

@mcp.tool()
async def qc_run_pipeline(
    project_id: str,
    model: str | None = None,
    enable_review: bool = False,
    prompt_overrides: Dict[str, str] | None = None,
) -> str:
    """Run the full analysis pipeline on a project.

    Runs all stages: ingest, coding, perspective, relationship, synthesis,
    negative case analysis, and cross-interview (if multi-doc).

    If the project is paused for review, resumes from the paused stage.

    Args:
        project_id: The project ID
        model: LLM model name (default: gpt-5-mini)
        enable_review: If True, pause after coding for human review
        prompt_overrides: Optional dict mapping stage names to custom prompts.
            Supported stages: "thematic_coding", "gt_constant_comparison".
            Use {combined_text} and {num_interviews} placeholders for thematic_coding.
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if state.corpus.num_documents == 0:
        return json.dumps({"error": "Project has no documents. Add documents first with qc_add_documents."})

    model_name = model or state.config.model_name
    methodology = state.config.methodology.value

    # Handle resume from paused state
    resume_from = None
    if state.pipeline_status == PipelineStatus.PAUSED_FOR_REVIEW:
        rm = ReviewManager(state)
        resume_from = rm.prepare_for_resume()

    async def _save_callback(s: ProjectState) -> None:
        store.save(s)

    pipeline = create_pipeline(
        methodology=methodology,
        on_stage_complete=_save_callback,
        enable_human_review=enable_review,
    )

    interviews = [
        {"name": d.name, "content": d.content}
        for d in state.corpus.documents
    ]
    ctx = PipelineContext(
        model_name=model_name,
        interviews=interviews,
        prompt_overrides=prompt_overrides or {},
    )

    state = await pipeline.run(state, ctx, resume_from=resume_from)
    store.save(state)

    return json.dumps({
        "status": state.pipeline_status.value,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        "memos": len(state.memos),
        "phase_results": [
            {"phase": pr.phase_name, "status": pr.status.value}
            for pr in state.phase_results
        ],
    })


@mcp.tool()
async def qc_run_stage(
    project_id: str,
    stage_name: str,
    model: str | None = None,
) -> str:
    """Run a single named pipeline stage on a project.

    Useful for re-running just one stage (e.g. coding or synthesis) without
    running the full pipeline.

    Args:
        project_id: The project ID
        stage_name: Stage name (e.g. "Thematic Coding", "Synthesis", "Ingest")
        model: LLM model name (default: gpt-5-mini)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    model_name = model or state.config.model_name
    methodology = state.config.methodology.value

    pipeline = create_pipeline(methodology=methodology)

    # Find the matching stage
    target_stage = None
    for stage in pipeline.stages:
        if stage.name() == stage_name:
            target_stage = stage
            break

    if target_stage is None:
        available = [s.name() for s in pipeline.stages]
        return json.dumps({
            "error": f"Stage '{stage_name}' not found.",
            "available_stages": available,
        })

    interviews = [
        {"name": d.name, "content": d.content}
        for d in state.corpus.documents
    ]
    ctx = PipelineContext(model_name=model_name, interviews=interviews)

    state = await target_stage.execute(state, ctx)
    store.save(state)

    return json.dumps({
        "stage": stage_name,
        "status": "completed",
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
    })


@mcp.tool()
async def qc_recode(
    project_id: str,
    model: str | None = None,
) -> str:
    """Run incremental re-coding on a project.

    Codes only uncoded documents against the existing codebook, then re-runs
    downstream stages (negative case, cross-interview). Use after adding new
    documents to a completed project.

    Args:
        project_id: The project ID
        model: LLM model name (default: gpt-5-mini)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if state.corpus.num_documents == 0:
        return json.dumps({"error": "Project has no documents."})

    if len(state.codebook.codes) == 0:
        return json.dumps({"error": "Project has no codebook. Run the full pipeline first."})

    model_name = model or state.config.model_name
    methodology = state.config.methodology.value

    async def _save_callback(s: ProjectState) -> None:
        store.save(s)

    pipeline = create_incremental_pipeline(
        methodology=methodology,
        on_stage_complete=_save_callback,
    )

    interviews = [
        {"name": d.name, "content": d.content}
        for d in state.corpus.documents
    ]
    ctx = PipelineContext(model_name=model_name, interviews=interviews)

    state = await pipeline.run(state, ctx)
    store.save(state)

    return json.dumps({
        "status": state.pipeline_status.value,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        "iteration": state.iteration,
    })


@mcp.tool()
async def qc_run_irr(
    project_id: str,
    passes: int = 3,
    model: str | None = None,
    models: List[str] | None = None,
) -> str:
    """Run inter-rater reliability analysis on a project.

    Runs coding multiple times with prompt variation, aligns codes across
    passes, and computes agreement metrics (Cohen's/Fleiss' kappa).

    Args:
        project_id: The project ID
        passes: Number of independent coding passes (default 3)
        model: Default model for all passes
        models: Per-pass model names (overrides model param, cycles if shorter)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if state.corpus.num_documents == 0:
        return json.dumps({"error": "Project has no documents."})

    model_name = model or state.config.model_name

    result = await run_irr_analysis(
        state=state,
        num_passes=passes,
        model_name=model_name,
        models=models,
    )

    state.irr_result = result
    store.save(state)

    return json.dumps({
        "passes": result.num_passes,
        "aligned_codes": result.aligned_codes,
        "unmatched_codes": result.unmatched_codes,
        "percent_agreement": round(result.percent_agreement, 3),
        "cohens_kappa": round(result.cohens_kappa, 3) if result.cohens_kappa is not None else None,
        "fleiss_kappa": round(result.fleiss_kappa, 3) if result.fleiss_kappa is not None else None,
        "interpretation": result.interpretation,
    })


@mcp.tool()
async def qc_run_stability(
    project_id: str,
    runs: int = 5,
    model: str | None = None,
) -> str:
    """Run multi-run stability analysis on a project.

    Runs identical coding multiple times to measure LLM non-determinism.
    Classifies each code as stable (>=80%), moderate (50-79%), or unstable (<50%).

    Args:
        project_id: The project ID
        runs: Number of identical runs (default 5)
        model: Model to use for all runs
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if state.corpus.num_documents == 0:
        return json.dumps({"error": "Project has no documents."})

    model_name = model or state.config.model_name

    result = await run_stability_analysis(
        state=state,
        num_runs=runs,
        model_name=model_name,
    )

    state.stability_result = result
    store.save(state)

    return json.dumps({
        "runs": result.num_runs,
        "overall_stability": round(result.overall_stability, 3),
        "stable_codes": result.stable_codes,
        "moderate_codes": result.moderate_codes,
        "unstable_codes": result.unstable_codes,
        "code_stability": {k: round(v, 3) for k, v in result.code_stability.items()},
    })


# ---------------------------------------------------------------------------
# Granular review
# ---------------------------------------------------------------------------

@mcp.tool()
def qc_review_codes(
    project_id: str,
    decisions: List[Dict[str, Any]],
) -> str:
    """Apply individual review decisions to codes in a project.

    Each decision is a dict with:
    - target_type: "code", "code_application", or "codebook"
    - target_id: ID of the code or application
    - action: "approve", "reject", "modify", "merge", or "split"
    - new_value: Optional dict for modify/merge/split (e.g. {"name": "New Name"})

    Args:
        project_id: The project ID
        decisions: List of review decision dicts
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    if not decisions:
        return json.dumps({"error": "No decisions provided."})

    rm = ReviewManager(state)
    review_decisions = []
    for d in decisions:
        try:
            action = ReviewAction(d["action"])
        except (KeyError, ValueError) as e:
            return json.dumps({"error": f"Invalid decision: {e}"})
        review_decisions.append(HumanReviewDecision(
            target_type=d.get("target_type", "code"),
            target_id=d.get("target_id", ""),
            action=action,
            new_value=d.get("new_value"),
        ))

    result = rm.apply_decisions(review_decisions)
    store.save(state)

    return json.dumps({
        "applied": result["applied"],
        "can_resume": rm.can_resume(),
    })


if __name__ == "__main__":
    mcp.run()
