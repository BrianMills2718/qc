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
from qc_clean.core.export.audit_event_log import (
    append_export_audit_event,
    mirror_export_audit_event_log_to_sqlite,
)
from qc_clean.core.export.audit_manifest import (
    build_export_audit_manifest,
    verify_export_audit_manifest_payload,
    write_export_audit_manifest,
)
from qc_clean.core.export.data_exporter import ProjectExporter
from qc_clean.core.claims import summarize_claim_ledger, summarize_disconfirmation_coverage
from qc_clean.core.pipeline.review import ReviewManager
from qc_clean.core.pipeline.pipeline_factory import create_pipeline, create_incremental_pipeline
from qc_clean.core.pipeline.pipeline_engine import PipelineContext
from qc_clean.core.pipeline.irr import run_irr_analysis, run_stability_analysis
from qc_clean.schemas.domain import (
    ClaimKind,
    CorpusScope,
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

# Agent-driven exports are confined to a dedicated directory so a caller cannot
# use ``output_file`` to perform an arbitrary write (e.g. "/home/brian/.bashrc"
# or "../../etc/cron.d/x"). The trusted CLI keeps full path freedom; only this
# MCP surface is sandboxed.
import re as _re

EXPORTS_DIR = (store.projects_dir / "exports").resolve()
_UNSAFE_NAME_RE = _re.compile(r"[^A-Za-z0-9._-]+")


def _warn_payload(state) -> dict:
    """Return {"data_warnings": [...]} when the state carries warnings, else {}.

    Surfacing data_warnings on agent-facing MCP outputs keeps stale/unanchored
    outputs from being consumed as current (INV-11/INV-1).
    """
    return {"data_warnings": list(state.data_warnings)} if state.data_warnings else {}


def _confine_export_path(output_file: Optional[str], default_name: str) -> str:
    """Map an agent-supplied output_file to a sanitized path inside EXPORTS_DIR.

    Directory components in the request are discarded; only a sanitized basename
    is honored. The resolved path is verified to remain within EXPORTS_DIR.
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    raw_name = Path(output_file).name if output_file else default_name
    safe_name = _UNSAFE_NAME_RE.sub("_", raw_name).strip(" .") or default_name
    candidate = (EXPORTS_DIR / safe_name).resolve()
    if EXPORTS_DIR != candidate.parent:
        raise ValueError(f"Refusing to export outside {EXPORTS_DIR}: {output_file!r}")
    return str(candidate)


def _manifest_path_for_export(export_path: str) -> str:
    """Return a confined export-audit manifest path for one exported artifact."""
    export_name = Path(export_path).name
    stem = Path(export_name).stem or "export"
    return _confine_export_path(f"{stem}.manifest.json", "export.manifest.json")


def _event_log_path_for_export(export_path: str) -> str:
    """Return a confined export-audit event-log path for one exported artifact."""
    export_name = Path(export_path).name
    stem = Path(export_name).stem or "export"
    return _confine_export_path(f"{stem}.audit_events.jsonl", "export.audit_events.jsonl")


def _event_db_path_for_export(export_path: str) -> str:
    """Return a confined export-audit SQLite mirror path for one artifact."""
    export_name = Path(export_path).name
    stem = Path(export_name).stem or "export"
    return _confine_export_path(f"{stem}.audit_events.sqlite", "export.audit_events.sqlite")


def _with_optional_export_audit(
    payload: dict[str, Any],
    state: ProjectState,
    export_format: str,
    artifact_path: str,
    *,
    audit_manifest: bool,
    verify_audit_manifest: bool,
    audit_event_log: bool,
    audit_event_db: bool,
) -> dict[str, Any]:
    """Add optional export-audit manifest and verification fields to an MCP payload."""
    if verify_audit_manifest and not audit_manifest:
        return {"error": "verify_audit_manifest=True requires audit_manifest=True"}
    if audit_event_log and not audit_manifest:
        return {"error": "audit_event_log=True requires audit_manifest=True"}
    if audit_event_db and not audit_event_log:
        return {"error": "audit_event_db=True requires audit_event_log=True"}
    if not audit_manifest:
        return payload

    manifest_path = _manifest_path_for_export(artifact_path)
    event_log_path = _event_log_path_for_export(artifact_path) if audit_event_log else None
    event_db_path = _event_db_path_for_export(artifact_path) if audit_event_db else None
    manifest = build_export_audit_manifest(
        state,
        export_format=export_format,  # type: ignore[arg-type]
        artifact_paths=[artifact_path],
        base_dir=EXPORTS_DIR,
    )
    written = write_export_audit_manifest(manifest, manifest_path)
    payload["audit_manifest"] = written
    if event_log_path:
        append_export_audit_event(
            event_log_path,
            event_type="manifest_written",
            event_status="success",
            manifest_path=manifest_path,
            payload=manifest.model_dump(mode="json"),
        )
        payload["audit_event_log"] = event_log_path

    if verify_audit_manifest:
        report = verify_export_audit_manifest_payload(
            manifest,
            base_dir=EXPORTS_DIR,
            state=state,
        )
        if event_log_path:
            append_export_audit_event(
                event_log_path,
                event_type="manifest_verified",
                event_status=report.status,
                manifest_path=manifest_path,
                payload=report.model_dump(mode="json"),
            )
        payload["audit_verification"] = report.model_dump(mode="json")
        if report.status != "verified":
            payload["error"] = "Export audit manifest verification failed"
    if event_log_path and event_db_path:
        mirror_export_audit_event_log_to_sqlite(event_log_path, event_db_path)
        payload["audit_event_db"] = event_db_path
    return payload


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
    phenomenon: Optional[str] = None,
    population: Optional[str] = None,
    sampling_frame: Optional[str] = None,
    inclusion_criteria: Optional[List[str]] = None,
    exclusion_criteria: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> str:
    """Create a new qualitative coding project.

    Args:
        name: Project name (e.g. "Interview Study 2026")
        methodology: "thematic_analysis" (default) or "grounded_theory"
        phenomenon: Optional phenomenon, topic, or research question scope.
        population: Optional population or case universe for claims.
        sampling_frame: Optional description of how sources were selected.
        inclusion_criteria: Optional criteria that qualified sources.
        exclusion_criteria: Optional criteria that ruled sources out of scope.
        notes: Optional caveats or scope-condition notes.
    """
    try:
        meth = Methodology(methodology)
    except ValueError:
        return json.dumps({
            "error": f"Invalid methodology '{methodology}'. Use 'thematic_analysis' or 'grounded_theory'."
        })

    config = ProjectConfig(methodology=meth)
    state = ProjectState(name=name, config=config)
    scope_requested = any(
        value is not None
        for value in (
            phenomenon,
            population,
            sampling_frame,
            inclusion_criteria,
            exclusion_criteria,
            notes,
        )
    )
    if scope_requested:
        state.corpus_scope = CorpusScope(
            phenomenon=phenomenon or "",
            population=population or "",
            sampling_frame=sampling_frame or "",
            inclusion_criteria=list(inclusion_criteria or []),
            exclusion_criteria=list(exclusion_criteria or []),
            notes=notes or "",
        )
    path = store.save(state)
    return json.dumps({
        "project_id": state.id,
        "name": state.name,
        "methodology": meth.value,
        "corpus_scope": (
            state.corpus_scope.model_dump() if state.corpus_scope is not None else None
        ),
        "corpus_scope_set": state.corpus_scope is not None,
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
        "claims": len(state.claims),
        "memos": len(state.memos),
        "entities": len(state.entities),
        "phase_results": phase_results,
        "updated_at": state.updated_at,
    }, indent=2)


@mcp.tool()
def qc_get_claims(project_id: str, limit: int = 50) -> str:
    """Get the first-class analytic claim ledger for a project.

    Args:
        project_id: The project ID
        limit: Maximum number of claim rows to return (default 50)
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    rows = []
    for claim in state.claims[:max(0, limit)]:
        rows.append({
            "id": claim.id,
            "kind": claim.claim_kind.value,
            "source_stage": claim.source_stage,
            "support_status": claim.support_status.value,
            "adjudication_status": claim.adjudication_status.value,
            "claim_text": claim.claim_text,
            "origin_object_type": claim.origin_object_type,
            "origin_object_id": claim.origin_object_id,
            "supporting_anchors": len(claim.supporting_anchors),
            "contrary_anchors": len(claim.contrary_anchors),
        })

    return json.dumps({
        "project": state.name,
        "claim_summary": summarize_claim_ledger(state),
        "disconfirmation_summary": summarize_disconfirmation_coverage(state),
        "returned": len(rows),
        "claims": rows,
    }, indent=2)


def _claim_review_row(claim) -> Dict[str, Any]:
    """Return one bounded claim row for review surfaces."""
    return {
        "id": claim.id,
        "kind": claim.claim_kind.value,
        "source_stage": claim.source_stage,
        "support_status": claim.support_status.value,
        "adjudication_status": claim.adjudication_status.value,
        "claim_text": claim.claim_text,
        "scope": claim.scope.model_dump(mode="json"),
        "origin_object_type": claim.origin_object_type,
        "origin_object_id": claim.origin_object_id,
        "supporting_anchors": len(claim.supporting_anchors),
        "contrary_anchors": len(claim.contrary_anchors),
        "revision_history_count": len(claim.revision_history),
        "created_by": claim.created_by.value,
        "created_at": claim.created_at,
    }


@mcp.tool()
def qc_review_claims(project_id: str, limit: int = 100) -> str:
    """List analytic claims as bounded review targets.

    Args:
        project_id: The project ID
        limit: Maximum claim rows to return, capped at 100
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    safe_limit = min(max(0, limit), 100)
    rm = ReviewManager(state)
    claims = [_claim_review_row(claim) for claim in state.claims[:safe_limit]]
    return json.dumps({
        "project_id": state.id,
        "project_name": state.name,
        "pipeline_status": state.pipeline_status.value,
        "claims": claims,
        "returned": len(claims),
        "total_claims": len(state.claims),
        "limit": safe_limit,
        "summary": rm.get_review_summary().model_dump(mode="json"),
        "can_resume": rm.can_resume(),
    }, indent=2)


@mcp.tool()
def qc_review_negative_cases(project_id: str, limit: int = 100) -> str:
    """List negative-case claims as bounded review targets.

    Decisions for these rows should use target_type="claim" because negative
    cases are represented as AnalyticClaim objects.

    Args:
        project_id: The project ID
        limit: Maximum negative-case rows to return, capped at 100
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    safe_limit = min(max(0, limit), 100)
    rm = ReviewManager(state)
    all_negative_cases = [
        claim for claim in state.claims if claim.claim_kind == ClaimKind.NEGATIVE_CASE
    ]
    negative_cases = [
        _claim_review_row(claim) for claim in all_negative_cases[:safe_limit]
    ]
    return json.dumps({
        "project_id": state.id,
        "project_name": state.name,
        "pipeline_status": state.pipeline_status.value,
        "negative_cases": negative_cases,
        "returned": len(negative_cases),
        "total_negative_cases": len(all_negative_cases),
        "limit": safe_limit,
        "summary": rm.get_review_summary().model_dump(mode="json"),
        "can_resume": rm.can_resume(),
    }, indent=2)


@mcp.tool()
def qc_review_relationships(project_id: str, limit: int = 100) -> str:
    """List code/entity relationships as bounded review targets.

    Args:
        project_id: The project ID
        limit: Maximum relationship rows to return, capped at 100
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    safe_limit = min(max(0, limit), 100)
    rm = ReviewManager(state)
    all_relationships = rm.get_pending_relationships()
    relationships = all_relationships[:safe_limit]
    return json.dumps({
        "project_id": state.id,
        "project_name": state.name,
        "pipeline_status": state.pipeline_status.value,
        "relationships": relationships,
        "returned": len(relationships),
        "total_relationships": len(all_relationships),
        "limit": safe_limit,
        "summary": rm.get_review_summary().model_dump(mode="json"),
        "can_resume": rm.can_resume(),
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
        **_warn_payload(state),
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
        **_warn_payload(state),
    }, indent=2)


@mcp.tool()
def qc_grounding_report(project_id: str) -> str:
    """Report how well a project's code applications are anchored to source spans.

    The D1 grounding metric (INV-1): re-resolves every application's stored span
    and reports the fraction that still verifies against the source documents.

    Args:
        project_id: The project ID
    """
    from dataclasses import asdict
    from qc_clean.core.grounding import verify_grounding
    from qc_clean.core.segmentation import compute_coverage

    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    return json.dumps({
        "project": state.name,
        "grounding": asdict(verify_grounding(state)),       # D1
        "coverage": asdict(compute_coverage(state)),         # D2 (segment universe)
    }, indent=2)


@mcp.tool()
def qc_export_markdown(
    project_id: str,
    output_file: str | None = None,
    audit_manifest: bool = False,
    verify_audit_manifest: bool = False,
    audit_event_log: bool = False,
    audit_event_db: bool = False,
) -> str:
    """Export a project as a human-readable Markdown report.

    Includes executive summary, codebook, key quotes, memos,
    entity relationships, and audit trail.

    Args:
        project_id: The project ID
        output_file: Optional output file path (default: {project_name}_report.md)
        audit_manifest: Whether to write a confined export-audit manifest sidecar
        verify_audit_manifest: Whether to verify the sidecar immediately
        audit_event_log: Whether to append confined export-audit event-log records
        audit_event_db: Whether to mirror confined event-log records into SQLite
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    safe_path = _confine_export_path(output_file, f"{state.name}_report.md")
    path = exporter.export_markdown(state, safe_path)
    payload = _with_optional_export_audit(
        {"exported_to": path, "format": "markdown"},
        state,
        "markdown",
        path,
        audit_manifest=audit_manifest,
        verify_audit_manifest=verify_audit_manifest,
        audit_event_log=audit_event_log,
        audit_event_db=audit_event_db,
    )
    return json.dumps(payload)


@mcp.tool()
def qc_export_json(
    project_id: str,
    output_file: str | None = None,
    audit_manifest: bool = False,
    verify_audit_manifest: bool = False,
    audit_event_log: bool = False,
    audit_event_db: bool = False,
) -> str:
    """Export a project's full state as JSON.

    Args:
        project_id: The project ID
        output_file: Optional output file path (default: {project_name}.json)
        audit_manifest: Whether to write a confined export-audit manifest sidecar
        verify_audit_manifest: Whether to verify the sidecar immediately
        audit_event_log: Whether to append confined export-audit event-log records
        audit_event_db: Whether to mirror confined event-log records into SQLite
    """
    try:
        state = store.load(project_id)
    except FileNotFoundError:
        return json.dumps({"error": f"Project '{project_id}' not found."})

    safe_path = _confine_export_path(output_file, f"{state.name}.json")
    path = exporter.export_json(state, safe_path)
    payload = _with_optional_export_audit(
        {"exported_to": path, "format": "json"},
        state,
        "json",
        path,
        audit_manifest=audit_manifest,
        verify_audit_manifest=verify_audit_manifest,
        audit_event_log=audit_event_log,
        audit_event_db=audit_event_db,
    )
    return json.dumps(payload)


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
        trace_id=f"qualitative_coding/mcp/{project_id}/pipeline",
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
    ctx = PipelineContext(
        model_name=model_name,
        interviews=interviews,
        trace_id=f"qualitative_coding/mcp/{project_id}/stage/{stage_name}",
    )

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
    ctx = PipelineContext(
        model_name=model_name,
        interviews=interviews,
        trace_id=f"qualitative_coding/mcp/{project_id}/recode/{state.iteration + 1}",
    )

    state = await pipeline.run(state, ctx)
    store.save(state)

    return json.dumps({
        "status": state.pipeline_status.value,
        "codes": len(state.codebook.codes),
        "code_applications": len(state.code_applications),
        "iteration": state.iteration,
        **_warn_payload(state),
    })


@mcp.tool()
async def qc_run_irr(
    project_id: str,
    passes: int = 3,
    model: str | None = None,
    models: List[str] | None = None,
    application_level: bool = False,
) -> str:
    """Run inter-rater reliability analysis on a project.

    Runs coding multiple times with prompt variation, aligns codes across
    passes, and computes agreement metrics (Cohen's/Fleiss' kappa).

    Args:
        project_id: The project ID
        passes: Number of independent coding passes (default 3)
        model: Default model for all passes
        models: Per-pass model names (overrides model param, cycles if shorter)
        application_level: Run exhaustive passes and report segment-level
            application and coded/no_code decision agreement
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
        application_level=application_level,
    )

    state.irr_result = result
    store.save(state)

    payload = {
        "passes": result.num_passes,
        "aligned_codes": result.aligned_codes,
        "unmatched_codes": result.unmatched_codes,
        "percent_agreement": round(result.percent_agreement, 3),
        "cohens_kappa": round(result.cohens_kappa, 3) if result.cohens_kappa is not None else None,
        "fleiss_kappa": round(result.fleiss_kappa, 3) if result.fleiss_kappa is not None else None,
        "interpretation": result.interpretation,
    }
    if result.application_level:
        payload.update({
            "application_level": True,
            "application_units": result.application_units,
            "application_percent_agreement": (
                round(result.application_percent_agreement, 3)
                if result.application_percent_agreement is not None else None
            ),
            "application_cohens_kappa": (
                round(result.application_cohens_kappa, 3)
                if result.application_cohens_kappa is not None else None
            ),
            "application_fleiss_kappa": (
                round(result.application_fleiss_kappa, 3)
                if result.application_fleiss_kappa is not None else None
            ),
            "application_interpretation": result.application_interpretation,
            "segment_decision_units": result.segment_decision_units,
            "segment_decision_percent_agreement": (
                round(result.segment_decision_percent_agreement, 3)
                if result.segment_decision_percent_agreement is not None else None
            ),
            "segment_decision_cohens_kappa": (
                round(result.segment_decision_cohens_kappa, 3)
                if result.segment_decision_cohens_kappa is not None else None
            ),
            "segment_decision_fleiss_kappa": (
                round(result.segment_decision_fleiss_kappa, 3)
                if result.segment_decision_fleiss_kappa is not None else None
            ),
            "segment_decision_interpretation": result.segment_decision_interpretation,
        })
    return json.dumps(payload)


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

def _apply_mcp_review_decisions(
    project_id: str,
    decisions: List[Dict[str, Any]],
) -> str:
    """Apply MCP review decisions through the shared ReviewManager."""
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
            rationale=d.get("rationale", ""),
            new_value=d.get("new_value"),
        ))

    try:
        result = rm.apply_decisions(review_decisions)
    except ValueError as exc:
        return json.dumps({"error": str(exc)})
    store.save(state)

    return json.dumps({
        "applied": result["applied"],
        "codes_remaining": len(state.codebook.codes),
        "claims_count": len(state.claims),
        "relationships_count": (
            len(state.code_relationships) + len(state.entity_relationships)
        ),
        "can_resume": rm.can_resume(),
    })


@mcp.tool()
def qc_review_decisions(
    project_id: str,
    decisions: List[Dict[str, Any]],
) -> str:
    """Apply review decisions to codes, applications, codebooks, claims, or relationships.

    Each decision is a dict with:
    - target_type: "code", "code_application", "codebook", "claim",
      "code_relationship", or "entity_relationship"
    - target_id: ID of the reviewed object
    - action: "approve", "reject", "modify", "merge", or "split"
    - rationale: Optional reason for the decision
    - new_value: Optional dict for modify/merge/split decisions

    Args:
        project_id: The project ID
        decisions: List of review decision dicts
    """
    return _apply_mcp_review_decisions(project_id, decisions)


@mcp.tool()
def qc_review_codes(
    project_id: str,
    decisions: List[Dict[str, Any]],
) -> str:
    """Apply individual review decisions to a project; kept for compatibility.

    Each decision is a dict with:
    - target_type: "code", "code_application", "codebook", "claim",
      "code_relationship", or "entity_relationship"
    - target_id: ID of the reviewed object
    - action: "approve", "reject", "modify", "merge", or "split"
    - rationale: Optional reason for the decision
    - new_value: Optional dict for modify/merge/split decisions

    Args:
        project_id: The project ID
        decisions: List of review decision dicts
    """
    return _apply_mcp_review_decisions(project_id, decisions)


if __name__ == "__main__":
    mcp.run()
