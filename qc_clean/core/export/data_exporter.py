#!/usr/bin/env python3
"""
Data Exporter - Export analysis results to various formats.

ProjectExporter: accepts a ProjectState and exports to JSON, CSV, or Markdown.
DataExporter: legacy dict-based exporter (kept for backward compatibility).
"""

import csv
import io
import json
import logging
import re
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree.ElementTree import Element, SubElement, ElementTree

from qc_clean.core.claims import format_claim_scope_summary, summarize_claim_ledger
from qc_clean.core.patterns import summarize_observed_patterns
from qc_clean.schemas.domain import ProjectState

logger = logging.getLogger(__name__)

UNSAFE_FILENAME_CHARS_RE = re.compile(r"[^A-Za-z0-9 _.-]+")
MISSING_CORPUS_SCOPE_WARNING_MESSAGE = (
    "No corpus scope is recorded. Treat all claims below as bounded to "
    "the loaded documents only; do not generalize to a population without "
    "a stated and defensible sampling frame."
)
EMPTY_CORPUS_SCOPE_WARNING_MESSAGE = (
    "A corpus scope record exists, but no scope details are specified. Treat "
    "claim-bearing exports as bounded to the loaded documents only until the "
    "phenomenon, population, sampling frame, criteria, or caveats are recorded."
)
MISSING_SAMPLING_FRAME_WARNING_MESSAGE = (
    "A corpus population is recorded without a sampling frame. Do not treat "
    "the population field as a defensible generalization boundary until the "
    "selection basis is stated."
)


def _safe_filename_stem(value: str, fallback: str = "project") -> str:
    """Convert a display name into one filesystem-local filename stem."""
    safe = UNSAFE_FILENAME_CHARS_RE.sub("_", value).strip(" .")
    return safe or fallback


def _default_export_path(project_name: str, suffix: str) -> Path:
    """Build a default export path without allowing project names to add dirs."""
    return Path(f"{_safe_filename_stem(project_name)}{suffix}")


def _ensure_can_write(path: Path, *, overwrite: bool) -> None:
    """Fail before writing when overwrite is disabled and the target exists."""
    if not overwrite and path.exists():
        raise FileExistsError(f"Refusing to overwrite existing export artifact: {path}")


def _ensure_can_write_all(paths: List[Path], *, overwrite: bool) -> None:
    """Fail before writing any artifact when one target would be clobbered."""
    for path in paths:
        _ensure_can_write(path, overwrite=overwrite)


def _corpus_scope_export_warnings(
    state: ProjectState,
) -> List[Dict[str, Any]]:
    """Return report-boundary warning metadata for claim-bearing exports."""
    if not state.claims:
        return []

    if state.corpus_scope is None:
        return [
            {
                "code": "missing_corpus_scope",
                "message": MISSING_CORPUS_SCOPE_WARNING_MESSAGE,
                "applies_to": "claim_ledger",
                "claim_count": len(state.claims),
            }
        ]

    scope = state.corpus_scope
    warnings: List[Dict[str, Any]] = []
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
        warnings.append(
            {
                "code": "empty_corpus_scope",
                "message": EMPTY_CORPUS_SCOPE_WARNING_MESSAGE,
                "applies_to": "claim_ledger",
                "claim_count": len(state.claims),
            }
        )
    if scope.population and not scope.sampling_frame:
        warnings.append(
            {
                "code": "missing_sampling_frame",
                "message": MISSING_SAMPLING_FRAME_WARNING_MESSAGE,
                "applies_to": "claim_ledger",
                "claim_count": len(state.claims),
            }
        )
    return warnings


def _documents_count_phrase(state: ProjectState) -> str:
    """Return a compact document-count phrase for scope-bound report text."""
    count = state.corpus.num_documents
    noun = "document" if count == 1 else "documents"
    return f"{count} {noun}"


def _corpus_scope_boundary_for_export(state: ProjectState) -> str:
    """Return deterministic per-row corpus boundary context for claim exports."""
    if state.corpus_scope is None:
        return (
            f"Loaded document corpus only ({_documents_count_phrase(state)}); "
            "no CorpusScope recorded."
        )

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
        return (
            f"Loaded document corpus only ({_documents_count_phrase(state)}); "
            "CorpusScope has no details."
        )

    if scope.population and not scope.sampling_frame:
        return (
            f"Unvalidated population boundary: {scope.population}; "
            "sampling frame not recorded."
        )

    parts: list[str] = []
    if scope.phenomenon:
        parts.append(f"phenomenon={scope.phenomenon}")
    if scope.population:
        parts.append(f"population={scope.population}")
    if scope.sampling_frame:
        parts.append(f"sampling_frame={scope.sampling_frame}")
    if scope.inclusion_criteria:
        parts.append(f"inclusion={', '.join(scope.inclusion_criteria)}")
    if scope.exclusion_criteria:
        parts.append(f"exclusion={', '.join(scope.exclusion_criteria)}")
    if scope.notes:
        parts.append(f"notes={scope.notes}")
    return "; ".join(parts)


def _markdown_table_cell(value: str) -> str:
    """Escape one value for a Markdown table cell."""
    return value.replace("\n", " ").replace("|", "\\|")


# ---------------------------------------------------------------------------
# ProjectExporter -- works directly with ProjectState
# ---------------------------------------------------------------------------

class ProjectExporter:
    """Export a ProjectState to JSON, CSV, or Markdown."""

    def export_json(
        self,
        state: ProjectState,
        output_file: Optional[str] = None,
        *,
        overwrite: bool = True,
    ) -> str:
        """Export full project state as JSON. Returns the output path."""
        path = Path(output_file) if output_file else _default_export_path(state.name, ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_can_write(path, overwrite=overwrite)
        payload = state.model_dump(mode="json")
        if warnings := _corpus_scope_export_warnings(state):
            payload["export_warnings"] = warnings
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Exported JSON to %s", path)
        return str(path)

    def export_csv(
        self,
        state: ProjectState,
        output_dir: Optional[str] = None,
        *,
        overwrite: bool = True,
    ) -> List[str]:
        """
        Export codes and code-applications as two CSV files.
        Returns list of output paths.
        """
        out = Path(output_dir) if output_dir else Path(".")
        out.mkdir(parents=True, exist_ok=True)

        codes_path = out / "codes.csv"
        apps_path = out / "applications.csv"
        memos_path = out / "memos.csv"
        claims_path = out / "claims.csv"
        warnings_path = out / "export_warnings.csv"
        irr_path = out / "irr_matrix.csv"
        app_path = out / "irr_application_matrix.csv"
        decision_path = out / "irr_segment_decisions.csv"
        stab_path = out / "stability.csv"
        planned_paths = [codes_path, apps_path]
        if state.memos:
            planned_paths.append(memos_path)
        if state.claims:
            planned_paths.append(claims_path)
        if _corpus_scope_export_warnings(state):
            planned_paths.append(warnings_path)
        if state.irr_result and state.irr_result.coding_matrix:
            planned_paths.append(irr_path)
        if state.irr_result and state.irr_result.application_matrix:
            planned_paths.append(app_path)
        if state.irr_result and state.irr_result.segment_decision_matrix:
            planned_paths.append(decision_path)
        if state.stability_result and state.stability_result.code_stability:
            planned_paths.append(stab_path)
        _ensure_can_write_all(planned_paths, overwrite=overwrite)

        paths: List[str] = []

        # -- codes.csv --
        with open(codes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "code_id", "name", "description", "parent_id",
                "level", "mention_count", "confidence", "provenance", "reasoning",
            ])
            for code in state.codebook.codes:
                writer.writerow([
                    code.id, code.name, code.description, code.parent_id or "",
                    code.level, code.mention_count, f"{code.confidence:.2f}",
                    code.provenance.value, code.reasoning,
                ])
        paths.append(str(codes_path))

        # -- applications.csv --
        with open(apps_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "application_id", "code_id", "code_name", "doc_id",
                "doc_name", "speaker", "quote_text", "confidence",
            ])
            # Build lookup maps
            code_names = {c.id: c.name for c in state.codebook.codes}
            doc_names = {d.id: d.name for d in state.corpus.documents}
            for app in state.code_applications:
                writer.writerow([
                    app.id,
                    app.code_id,
                    code_names.get(app.code_id, ""),
                    app.doc_id,
                    doc_names.get(app.doc_id, ""),
                    app.speaker or "",
                    app.quote_text,
                    f"{app.confidence:.2f}",
                ])
        paths.append(str(apps_path))

        # -- memos.csv (only if memos exist) --
        if state.memos:
            with open(memos_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "memo_id", "memo_type", "title", "content",
                    "code_refs", "doc_refs", "created_by", "created_at",
                ])
                for memo in state.memos:
                    writer.writerow([
                        memo.id,
                        memo.memo_type,
                        memo.title,
                        memo.content,
                        ";".join(memo.code_refs),
                        ";".join(memo.doc_refs),
                        memo.created_by.value,
                        memo.created_at,
                    ])
            paths.append(str(memos_path))

        # -- claims.csv (only if claim ledger exists) --
        if state.claims:
            corpus_scope_boundary = _corpus_scope_boundary_for_export(state)
            with open(claims_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "claim_id", "kind", "source_stage", "adjudication_status",
                    "support_status", "origin_object_type", "origin_object_id",
                    "claim_scope", "corpus_scope_boundary", "claim_text",
                    "supporting_anchors", "contrary_anchors",
                ])
                for claim in state.claims:
                    writer.writerow([
                        claim.id,
                        claim.claim_kind.value,
                        claim.source_stage,
                        claim.adjudication_status.value,
                        claim.support_status.value,
                        claim.origin_object_type,
                        claim.origin_object_id,
                        format_claim_scope_summary(claim.scope),
                        corpus_scope_boundary,
                        claim.claim_text,
                        json.dumps([
                            a.model_dump(mode="json") for a in claim.supporting_anchors
                        ], ensure_ascii=False),
                        json.dumps([
                            a.model_dump(mode="json") for a in claim.contrary_anchors
                        ], ensure_ascii=False),
                    ])
            paths.append(str(claims_path))

        if warnings := _corpus_scope_export_warnings(state):
            with open(warnings_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["code", "message", "applies_to", "claim_count"])
                for warning in warnings:
                    writer.writerow([
                        warning["code"],
                        warning["message"],
                        warning["applies_to"],
                        warning["claim_count"],
                    ])
            paths.append(str(warnings_path))

        # -- irr_matrix.csv (only if IRR has been run) --
        if state.irr_result and state.irr_result.coding_matrix:
            irr = state.irr_result
            with open(irr_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                header = ["code_name"] + [f"pass_{i+1}" for i in range(irr.num_passes)] + ["agreement"]
                writer.writerow(header)
                for code_name, row in sorted(irr.coding_matrix.items()):
                    agree = "yes" if all(v == row[0] for v in row) else "no"
                    writer.writerow([code_name] + row + [agree])
            paths.append(str(irr_path))

        if state.irr_result and state.irr_result.application_matrix:
            irr = state.irr_result
            with open(app_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                header = ["segment_code_cell"] + [f"pass_{i+1}" for i in range(irr.num_passes)] + ["agreement"]
                writer.writerow(header)
                for cell, row in sorted(irr.application_matrix.items()):
                    agree = "yes" if all(v == row[0] for v in row) else "no"
                    writer.writerow([cell] + row + [agree])
            paths.append(str(app_path))

        if state.irr_result and state.irr_result.segment_decision_matrix:
            irr = state.irr_result
            with open(decision_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                header = ["segment_key"] + [f"pass_{i+1}" for i in range(irr.num_passes)] + ["agreement"]
                writer.writerow(header)
                for seg_key, row in sorted(irr.segment_decision_matrix.items()):
                    agree = "yes" if all(v == row[0] for v in row) else "no"
                    writer.writerow([seg_key] + row + [agree])
            paths.append(str(decision_path))

        # -- stability.csv (only if stability has been run) --
        if state.stability_result and state.stability_result.code_stability:
            sr = state.stability_result
            with open(stab_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["code_name", "stability_score", "classification",
                                 "num_runs", "model"])
                for code_name, score in sorted(sr.code_stability.items(), key=lambda x: -x[1]):
                    if score >= 0.8:
                        classification = "stable"
                    elif score >= 0.5:
                        classification = "moderate"
                    else:
                        classification = "unstable"
                    writer.writerow([code_name, f"{score:.2f}", classification,
                                     sr.num_runs, sr.model_name])
            paths.append(str(stab_path))

        logger.info("Exported CSV to %s", out)
        return paths

    def export_markdown(
        self,
        state: ProjectState,
        output_file: Optional[str] = None,
        *,
        overwrite: bool = True,
    ) -> str:
        """Export a human-readable Markdown report. Returns the output path."""
        path = Path(output_file) if output_file else _default_export_path(
            f"{state.name}_report",
            ".md",
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_can_write(path, overwrite=overwrite)

        lines: List[str] = []
        _a = lines.append  # shorthand

        _a(f"# {state.name}")
        _a("")
        _a(f"**Methodology**: {state.config.methodology.value}")
        _a(f"**Documents**: {state.corpus.num_documents}")
        _a(f"**Pipeline status**: {state.pipeline_status.value}")
        _a(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        _a("")

        # Data warnings — surfaced prominently so stale or unanchored outputs are
        # never silently rendered as current (INV-11/INV-1).
        if state.data_warnings:
            _a("> ⚠️ **Data warnings** — read before relying on the results below:")
            for w in state.data_warnings:
                _a(f"> - {w}")
            _a("")

        scope_warnings = _corpus_scope_export_warnings(state)
        if state.corpus_scope:
            scope = state.corpus_scope
            _a("## Corpus Scope")
            _a("")
            wrote_scope_detail = False
            if scope.phenomenon:
                _a(f"**Phenomenon**: {scope.phenomenon}")
                wrote_scope_detail = True
            if scope.population:
                _a(f"**Population**: {scope.population}")
                wrote_scope_detail = True
            if scope.sampling_frame:
                _a(f"**Sampling frame**: {scope.sampling_frame}")
                wrote_scope_detail = True
            if scope.inclusion_criteria:
                _a("")
                _a("**Inclusion criteria**:")
                for criterion in scope.inclusion_criteria:
                    _a(f"- {criterion}")
                wrote_scope_detail = True
            if scope.exclusion_criteria:
                _a("")
                _a("**Exclusion criteria**:")
                for criterion in scope.exclusion_criteria:
                    _a(f"- {criterion}")
                wrote_scope_detail = True
            if scope.notes:
                _a("")
                _a(f"**Notes**: {scope.notes}")
                wrote_scope_detail = True
            if not wrote_scope_detail:
                _a("Scope record exists, but no scope details are specified.")
            if scope_warnings:
                _a("")
                for warning in scope_warnings:
                    _a(warning["message"])
            _a("")
        elif scope_warnings:
            _a("## Corpus Scope")
            _a("")
            for warning in scope_warnings:
                _a(warning["message"])
            _a("")

        # Executive summary
        if state.synthesis and state.synthesis.executive_summary:
            _a("## Executive Summary")
            _a("")
            _a(state.synthesis.executive_summary)
            _a("")

        # Key findings
        if state.synthesis and state.synthesis.key_findings:
            _a("## Key Findings")
            _a("")
            for finding in state.synthesis.key_findings:
                _a(f"- {finding}")
            _a("")

        # Codes
        if state.codebook.codes:
            _a("## Codebook")
            _a("")
            _a("| Code | Description | Mentions | Confidence |")
            _a("|------|-------------|----------|------------|")
            for code in sorted(state.codebook.codes, key=lambda c: c.mention_count, reverse=True):
                desc = code.description[:80] + "..." if len(code.description) > 80 else code.description
                _a(f"| {code.name} | {desc} | {code.mention_count} | {code.confidence:.2f} |")
            _a("")

        # Code hierarchy (top-level with children)
        top_level = state.codebook.top_level_codes()
        # parent_id values may differ in case from code.id (e.g. GT open coding
        # uses "Code_Name" vs ID "CODE_NAME"), so normalize when grouping.
        children_map: Dict[str, list] = {}
        for code in state.codebook.codes:
            if code.parent_id:
                # Normalize to match code IDs
                norm_pid = code.parent_id.upper().replace(" ", "_")
                children_map.setdefault(norm_pid, []).append(code)
        if children_map:
            _a("### Code Hierarchy")
            _a("")

            def _render_tree(code, indent=0):
                prefix = "  " * indent
                if indent == 0:
                    _a(f"{prefix}- **{code.name}**")
                else:
                    _a(f"{prefix}- {code.name}")
                for child in children_map.get(code.id.upper(), []):
                    _render_tree(child, indent + 1)

            for parent in top_level:
                _render_tree(parent)
            _a("")

        # Audit trail (per-code reasoning)
        codes_with_reasoning = [c for c in state.codebook.codes if c.reasoning]
        if codes_with_reasoning:
            _a("## Audit Trail")
            _a("")
            _a("*Per-code reasoning explaining why each code was created.*")
            _a("")
            for code in codes_with_reasoning:
                _a(f"- **{code.name}**: {code.reasoning}")
            _a("")

        # Key quotes (sample)
        if state.code_applications:
            _a("## Key Quotes")
            _a("")
            code_names = {c.id: c.name for c in state.codebook.codes}
            shown = 0
            for app in state.code_applications:
                if shown >= 20:
                    _a(f"*... and {len(state.code_applications) - 20} more applications*")
                    break
                code_name = code_names.get(app.code_id, app.code_id)
                speaker = f" ({app.speaker})" if app.speaker else ""
                _a(f"> {app.quote_text}")
                _a(">")
                _a(f"> -- **{code_name}**{speaker}")
                _a("")
                shown += 1

        # Analytical Memos
        if state.memos:
            _a("## Analytical Memos")
            _a("")
            for memo in state.memos:
                _a(f"### {memo.title or memo.memo_type}")
                _a(f"*Type: {memo.memo_type} | Generated: {memo.created_at[:10]}*")
                _a("")
                _a(memo.content)
                _a("")

        # First-class claim ledger (INV-9)
        if state.claims:
            summary = summarize_claim_ledger(state)
            _a("## Claim Ledger")
            _a("")
            _a(f"**Total claims**: {summary['total_claims']}")
            _a(f"**Unsupported or needing anchors**: {summary['unsupported_or_needing_anchor']}")
            _a("")
            _a("### Counts")
            _a("")
            _a(f"- By kind: {summary['by_kind']}")
            _a(f"- By stage: {summary['by_stage']}")
            _a(f"- By adjudication status: {summary['by_adjudication_status']}")
            _a(f"- By support status: {summary['by_support_status']}")
            _a("")
            _a("### Claims")
            _a("")
            corpus_scope_boundary = _corpus_scope_boundary_for_export(state)
            _a("| Kind | Stage | Scope | Corpus boundary | Support | Adjudication | Claim |")
            _a("|------|-------|-------|-----------------|---------|--------------|-------|")
            for claim in state.claims[:50]:
                text = _markdown_table_cell(claim.claim_text)
                if len(text) > 120:
                    text = text[:117] + "..."
                scope_summary = _markdown_table_cell(format_claim_scope_summary(claim.scope))
                boundary = _markdown_table_cell(corpus_scope_boundary)
                _a(
                    f"| {claim.claim_kind.value} | {claim.source_stage} | "
                    f"{scope_summary} | {boundary} | {claim.support_status.value} | "
                    f"{claim.adjudication_status.value} | {text} |"
                )
            if len(state.claims) > 50:
                _a("")
                _a(f"*... and {len(state.claims) - 50} more claims*")
            _a("")

        # Descriptive observed patterns
        if state.observed_patterns:
            summary = summarize_observed_patterns(state)
            _a("## Observed Patterns")
            _a("")
            _a(
                "*Descriptive observed patterns only; not causal proof, "
                "abductive synthesis, methodological-validity evidence, or SOTA evidence.*"
            )
            _a("")
            _a(f"**Total patterns**: {summary['total_patterns']}")
            _a("")
            _a("### Counts")
            _a("")
            _a(f"- By kind: {summary['by_kind']}")
            _a(f"- By stage: {summary['by_stage']}")
            _a(
                "- By causal interpretation status: "
                f"{summary['by_causal_interpretation_status']}"
            )
            _a("")
            _a("### Patterns")
            _a("")
            _a("| Kind | Stage | Status | Count | Scope | Pattern |")
            _a("|------|-------|--------|-------|-------|---------|")
            for pattern in state.observed_patterns[:50]:
                text = _markdown_table_cell(pattern.summary)
                if len(text) > 120:
                    text = text[:117] + "..."
                scope_parts = []
                if pattern.code_ids:
                    scope_parts.append(f"codes={','.join(pattern.code_ids)}")
                if pattern.doc_ids:
                    scope_parts.append(f"docs={','.join(pattern.doc_ids)}")
                if pattern.application_ids:
                    scope_parts.append(
                        f"applications={','.join(pattern.application_ids)}"
                    )
                scope = _markdown_table_cell("; ".join(scope_parts) or "not recorded")
                count = f"{pattern.count}/{pattern.total}" if pattern.total else str(pattern.count)
                _a(
                    f"| {pattern.pattern_kind.value} | {pattern.source_stage} | "
                    f"{pattern.causal_interpretation_status.value} | {count} | "
                    f"{scope} | {text} |"
                )
            if len(state.observed_patterns) > 50:
                _a("")
                _a(f"*... and {len(state.observed_patterns) - 50} more patterns*")
            _a("")

        # Perspectives
        if state.perspective_analysis and state.perspective_analysis.participants:
            _a("## Participant Perspectives")
            _a("")
            for p in state.perspective_analysis.participants:
                _a(f"### {p.name}")
                if p.role:
                    _a(f"**Role**: {p.role}")
                if p.perspective_summary:
                    _a(f"\n{p.perspective_summary}")
                _a("")

        # Entity relationships
        if state.entity_relationships:
            _a("## Entity Relationships")
            _a("")
            _a("| Entity 1 | Relationship | Entity 2 | Strength |")
            _a("|----------|-------------|----------|----------|")
            entity_names = {e.id: e.name for e in state.entities}
            for rel in state.entity_relationships:
                e1 = entity_names.get(rel.entity_1_id, rel.entity_1_id)
                e2 = entity_names.get(rel.entity_2_id, rel.entity_2_id)
                _a(f"| {e1} | {rel.relationship_type} | {e2} | {rel.strength:.2f} |")
            _a("")

        # Recommendations
        if state.synthesis and state.synthesis.recommendations:
            _a("## Recommendations")
            _a("")
            for rec in state.synthesis.recommendations:
                _a(f"### {rec.title}")
                _a(f"**Priority**: {rec.priority}")
                _a(f"\n{rec.description}")
                _a("")

        # GT-specific
        if state.core_categories:
            _a("## Core Categories (Grounded Theory)")
            _a("")
            for cc in state.core_categories:
                _a(f"### {cc.category_name}")
                if cc.definition:
                    _a(f"\n{cc.definition}")
                _a("")

        if state.theoretical_model:
            _a("## Theoretical Model")
            _a("")
            _a(f"**Model**: {state.theoretical_model.model_name}")
            if state.theoretical_model.theoretical_framework:
                _a(f"\n{state.theoretical_model.theoretical_framework}")
            _a("")

        # Inter-Rater Reliability
        if state.irr_result:
            irr = state.irr_result
            _a("## Inter-Rater Reliability")
            _a("")
            _a(f"**Passes**: {irr.num_passes}")
            _a(f"**Aligned codes**: {len(irr.aligned_codes)}")
            _a(f"**Unmatched codes**: {len(irr.unmatched_codes)}")
            _a("")
            _a("| Metric | Value | Interpretation |")
            _a("|--------|-------|----------------|")
            _a(f"| Percent agreement | {irr.percent_agreement:.1%} | |")
            if irr.cohens_kappa is not None:
                _a(f"| Cohen's kappa | {irr.cohens_kappa:.3f} | {irr.interpretation} |")
            if irr.fleiss_kappa is not None:
                label = irr.interpretation if irr.cohens_kappa is None else ""
                _a(f"| Fleiss' kappa | {irr.fleiss_kappa:.3f} | {label} |")
            if irr.gwet_ac1 is not None:
                _a(f"| Gwet's AC1 | {irr.gwet_ac1:.3f} | prevalence-robust consistency |")
            _a("")
            if irr.application_level:
                _a("### Application-Level Agreement")
                _a("")
                _a("Positive code-application cells compare only segment x code rows where at least one pass applied that code.")
                _a("")
                _a("| Metric | Value | Interpretation |")
                _a("|--------|-------|----------------|")
                _a(f"| Positive cell units | {irr.application_units} | |")
                if irr.application_percent_agreement is not None:
                    _a(f"| Positive cell percent agreement | {irr.application_percent_agreement:.1%} | |")
                if irr.application_cohens_kappa is not None:
                    _a(f"| Positive cell Cohen's kappa | {irr.application_cohens_kappa:.3f} | {irr.application_interpretation} |")
                if irr.application_fleiss_kappa is not None:
                    label = irr.application_interpretation if irr.application_cohens_kappa is None else ""
                    _a(f"| Positive cell Fleiss' kappa | {irr.application_fleiss_kappa:.3f} | {label} |")
                if irr.application_gwet_ac1 is not None:
                    _a(f"| Positive cell Gwet's AC1 | {irr.application_gwet_ac1:.3f} | prevalence-robust consistency |")
                _a(f"| Segment decision units | {irr.segment_decision_units} | |")
                if irr.segment_decision_percent_agreement is not None:
                    _a(f"| Segment decision percent agreement | {irr.segment_decision_percent_agreement:.1%} | |")
                if irr.segment_decision_cohens_kappa is not None:
                    _a(f"| Segment decision Cohen's kappa | {irr.segment_decision_cohens_kappa:.3f} | {irr.segment_decision_interpretation} |")
                if irr.segment_decision_fleiss_kappa is not None:
                    label = irr.segment_decision_interpretation if irr.segment_decision_cohens_kappa is None else ""
                    _a(f"| Segment decision Fleiss' kappa | {irr.segment_decision_fleiss_kappa:.3f} | {label} |")
                if irr.segment_decision_gwet_ac1 is not None:
                    _a(f"| Segment decision Gwet's AC1 | {irr.segment_decision_gwet_ac1:.3f} | prevalence-robust consistency |")
                _a("")
            if irr.coding_matrix:
                _a("### Coding Matrix")
                _a("")
                headers = ["Code"] + [f"Pass {i+1}" for i in range(irr.num_passes)] + ["Agreement"]
                _a("| " + " | ".join(headers) + " |")
                _a("|" + "|".join(["---"] * len(headers)) + "|")
                for code_name, row in sorted(irr.coding_matrix.items()):
                    agree = "Yes" if all(v == row[0] for v in row) else "No"
                    cells = [code_name] + [str(v) for v in row] + [agree]
                    _a("| " + " | ".join(cells) + " |")
                _a("")

        # Multi-Run Stability
        if state.stability_result:
            sr = state.stability_result
            _a("## Multi-Run Stability Analysis")
            _a("")
            _a(f"**Runs**: {sr.num_runs} | **Model**: {sr.model_name} | **Overall stability**: {sr.overall_stability:.1%}")
            _a("")
            _a(f"- Stable codes (>= 80%): {len(sr.stable_codes)}")
            _a(f"- Moderate codes (50-79%): {len(sr.moderate_codes)}")
            _a(f"- Unstable codes (< 50%): {len(sr.unstable_codes)}")
            _a("")
            if sr.code_stability:
                _a("| Code | Stability | Classification |")
                _a("|------|-----------|----------------|")
                for code_name, score in sorted(sr.code_stability.items(), key=lambda x: -x[1]):
                    if score >= 0.8:
                        classification = "Stable"
                    elif score >= 0.5:
                        classification = "Moderate"
                    else:
                        classification = "Unstable"
                    _a(f"| {code_name} | {score:.0%} | {classification} |")
                _a("")

        # Pipeline phases
        if state.phase_results:
            _a("## Pipeline Phases")
            _a("")
            _a("| Phase | Status |")
            _a("|-------|--------|")
            for pr in state.phase_results:
                _a(f"| {pr.phase_name} | {pr.status.value} |")
            _a("")

        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Exported Markdown to %s", path)
        return str(path)

    def export_qdpx(
        self,
        state: ProjectState,
        output_file: Optional[str] = None,
        *,
        overwrite: bool = True,
    ) -> str:
        """
        Export as REFI-QDA QDPX file (ZIP containing project.qde XML + source texts).

        Compatible with ATLAS.ti, NVivo, MAXQDA, and other REFI-QDA tools.
        Returns the output path.
        """
        path = Path(output_file) if output_file else _default_export_path(state.name, ".qdpx")
        path.parent.mkdir(parents=True, exist_ok=True)
        _ensure_can_write(path, overwrite=overwrite)

        NS = "urn:QDA-XML:project:1.0"
        user_guid = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # -- Root --
        root = Element(f"{{{NS}}}Project")
        root.set("name", state.name)
        root.set("basePath", "")
        root.set("creatingUserGUID", user_guid)
        root.set("creationDateTime", timestamp)
        root.set("modifyingUserGUID", user_guid)
        root.set("modifiedDateTime", timestamp)

        desc = SubElement(root, f"{{{NS}}}Description")
        desc.text = f"{state.config.methodology.value} analysis — {state.corpus.num_documents} document(s)"

        # -- Users --
        users_el = SubElement(root, f"{{{NS}}}Users")
        user_el = SubElement(users_el, f"{{{NS}}}User")
        user_el.set("guid", user_guid)
        user_el.set("name", "QC Researcher")

        # -- CodeBook --
        codebook_el = SubElement(root, f"{{{NS}}}CodeBook")
        codes_el = SubElement(codebook_el, f"{{{NS}}}Codes")

        # Build children map for hierarchy
        children_map: Dict[str, list] = {}
        for code in state.codebook.codes:
            pid = code.parent_id or "__root__"
            children_map.setdefault(pid, []).append(code)

        # Assign stable colours based on code index
        palette = [
            "#E63946", "#457B9D", "#2A9D8F", "#E9C46A",
            "#F4A261", "#264653", "#6A4C93", "#1982C4",
            "#8AC926", "#FF595E", "#6D6875", "#B5838D",
        ]

        def _add_code(parent_el, code, depth=0):
            code_el = SubElement(parent_el, f"{{{NS}}}Code")
            code_el.set("guid", code.id)
            code_el.set("name", code.name)
            code_el.set("isCodable", "true")
            code_el.set("color", palette[depth % len(palette)])
            if code.description:
                d = SubElement(code_el, f"{{{NS}}}Description")
                d.text = code.description
            for child in children_map.get(code.id, []):
                _add_code(code_el, child, depth + 1)

        for code in children_map.get("__root__", []):
            _add_code(codes_el, code)

        # Also add codes that have a parent_id but whose parent doesn't exist
        # (orphans — put them at top level)
        all_ids = {c.id for c in state.codebook.codes}
        for code in state.codebook.codes:
            if code.parent_id and code.parent_id not in all_ids and code.parent_id != "__root__":
                _add_code(codes_el, code)

        # -- Sources + Code Applications --
        sources_el = SubElement(root, f"{{{NS}}}Sources")
        source_files: Dict[str, str] = {}

        # Group applications by doc_id
        apps_by_doc: Dict[str, list] = {}
        for app in state.code_applications:
            apps_by_doc.setdefault(app.doc_id, []).append(app)

        for doc in state.corpus.documents:
            source_el = SubElement(sources_el, f"{{{NS}}}TextSource")
            source_el.set("guid", doc.id)
            source_el.set("name", doc.name)
            txt_filename = f"{doc.id}.txt"
            source_el.set("plainTextPath", f"internal://{txt_filename}")
            source_el.set("creatingUser", user_guid)
            source_el.set("creationDateTime", timestamp)
            source_el.set("modifyingUser", user_guid)
            source_el.set("modifiedDateTime", timestamp)

            source_files[txt_filename] = doc.content

            for app in apps_by_doc.get(doc.id, []):
                # Find quote position in document text
                start_pos = doc.content.find(app.quote_text) if doc.content else -1
                if start_pos == -1:
                    # If exact match fails, skip (quote may have been truncated)
                    continue
                end_pos = start_pos + len(app.quote_text)

                sel_el = SubElement(source_el, f"{{{NS}}}PlainTextSelection")
                sel_el.set("guid", app.id)
                sel_el.set("startPosition", str(start_pos))
                sel_el.set("endPosition", str(end_pos))
                sel_el.set("creatingUser", user_guid)
                sel_el.set("creationDateTime", timestamp)
                sel_el.set("modifyingUser", user_guid)
                sel_el.set("modifiedDateTime", timestamp)

                coding_el = SubElement(sel_el, f"{{{NS}}}Coding")
                coding_el.set("guid", str(uuid.uuid4()))
                coding_el.set("creatingUser", user_guid)
                coding_el.set("creationDateTime", timestamp)

                ref_el = SubElement(coding_el, f"{{{NS}}}CodeRef")
                ref_el.set("targetGUID", app.code_id)

        # -- Notes (memos) --
        if state.memos:
            notes_el = SubElement(root, f"{{{NS}}}Notes")
            for memo in state.memos:
                note_el = SubElement(notes_el, f"{{{NS}}}Note")
                note_el.set("guid", memo.id)
                note_el.set("name", memo.title or memo.memo_type)
                note_el.set("creatingUser", user_guid)
                note_el.set("creationDateTime", timestamp)
                note_desc = SubElement(note_el, f"{{{NS}}}Description")
                note_desc.text = memo.content

        # -- Write ZIP --
        tree = ElementTree(root)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            xml_buf = io.BytesIO()
            tree.write(xml_buf, encoding="utf-8", xml_declaration=True)
            zf.writestr("project.qde", xml_buf.getvalue())
            for filename, content in source_files.items():
                zf.writestr(f"sources/{filename}", content.encode("utf-8"))

        logger.info("Exported QDPX to %s", path)
        return str(path)


# ---------------------------------------------------------------------------
# Legacy DataExporter -- kept for backward compatibility
# ---------------------------------------------------------------------------

class DataExporter:
    """Export qualitative coding analysis results to various formats (legacy)."""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_results(self, results: Dict[str, Any], format: str = "json", filename: str = "results") -> str:
        if format.lower() == "json":
            return self._export_json(results, filename)
        elif format.lower() == "csv":
            return self._export_csv(results, filename)
        elif format.lower() == "markdown":
            return self._export_markdown(results, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, results: Dict[str, Any], filename: str) -> str:
        output_path = self.output_dir / f"{_safe_filename_stem(filename, 'results')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        return str(output_path)

    def _export_csv(self, results: Dict[str, Any], filename: str) -> str:
        output_path = self.output_dir / f"{_safe_filename_stem(filename, 'results')}.csv"
        rows: List[Dict[str, Any]] = []
        if 'codes' in results:
            for code in results['codes']:
                rows.append({
                    'type': 'code',
                    'name': code.get('code_name', 'Unknown'),
                    'description': code.get('description', ''),
                    'frequency': code.get('frequency', 0),
                })
        if rows:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['type', 'name', 'description', 'frequency'])
                writer.writeheader()
                writer.writerows(rows)
        return str(output_path)

    def _export_markdown(self, results: Dict[str, Any], filename: str) -> str:
        output_path = self.output_dir / f"{_safe_filename_stem(filename, 'results')}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Qualitative Coding Analysis Results\n\n")
            if 'codes' in results:
                f.write("## Codes Discovered\n\n")
                for code in results['codes']:
                    name = code.get('code_name', 'Unknown')
                    desc = code.get('description', 'No description')
                    freq = code.get('frequency', 0)
                    f.write(f"### {name}\n**Description**: {desc}\n**Frequency**: {freq}\n\n")
        return str(output_path)
