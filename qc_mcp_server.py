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
import asyncio
import logging
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from qc_clean.core.persistence.project_store import ProjectStore
from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.core.pipeline.review import ReviewManager
from qc_clean.schemas.domain import ProjectState, ProjectConfig, Methodology

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


if __name__ == "__main__":
    mcp.run()
