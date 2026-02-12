#!/usr/bin/env python3
"""
Data Exporter - Export analysis results to various formats.

ProjectExporter: accepts a ProjectState and exports to JSON, CSV, or Markdown.
DataExporter: legacy dict-based exporter (kept for backward compatibility).
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from qc_clean.schemas.domain import ProjectState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ProjectExporter -- works directly with ProjectState
# ---------------------------------------------------------------------------

class ProjectExporter:
    """Export a ProjectState to JSON, CSV, or Markdown."""

    def export_json(self, state: ProjectState, output_file: Optional[str] = None) -> str:
        """Export full project state as JSON. Returns the output path."""
        path = Path(output_file) if output_file else Path(f"{state.name}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Exported JSON to %s", path)
        return str(path)

    def export_csv(self, state: ProjectState, output_dir: Optional[str] = None) -> List[str]:
        """
        Export codes and code-applications as two CSV files.
        Returns list of output paths.
        """
        out = Path(output_dir) if output_dir else Path(".")
        out.mkdir(parents=True, exist_ok=True)

        paths: List[str] = []

        # -- codes.csv --
        codes_path = out / "codes.csv"
        with open(codes_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "code_id", "name", "description", "parent_id",
                "level", "mention_count", "confidence", "provenance",
            ])
            for code in state.codebook.codes:
                writer.writerow([
                    code.id, code.name, code.description, code.parent_id or "",
                    code.level, code.mention_count, f"{code.confidence:.2f}",
                    code.provenance.value,
                ])
        paths.append(str(codes_path))

        # -- applications.csv --
        apps_path = out / "applications.csv"
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

        logger.info("Exported CSV to %s", out)
        return paths

    def export_markdown(self, state: ProjectState, output_file: Optional[str] = None) -> str:
        """Export a human-readable Markdown report. Returns the output path."""
        path = Path(output_file) if output_file else Path(f"{state.name}_report.md")
        path.parent.mkdir(parents=True, exist_ok=True)

        lines: List[str] = []
        _a = lines.append  # shorthand

        _a(f"# {state.name}")
        _a("")
        _a(f"**Methodology**: {state.config.methodology.value}")
        _a(f"**Documents**: {state.corpus.num_documents}")
        _a(f"**Pipeline status**: {state.pipeline_status.value}")
        _a(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
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
            _a(f"| Code | Description | Mentions | Confidence |")
            _a(f"|------|-------------|----------|------------|")
            for code in sorted(state.codebook.codes, key=lambda c: c.mention_count, reverse=True):
                desc = code.description[:80] + "..." if len(code.description) > 80 else code.description
                _a(f"| {code.name} | {desc} | {code.mention_count} | {code.confidence:.2f} |")
            _a("")

        # Code hierarchy (top-level with children)
        top_level = state.codebook.top_level_codes()
        children_map: Dict[str, list] = {}
        for code in state.codebook.codes:
            if code.parent_id:
                children_map.setdefault(code.parent_id, []).append(code)
        if children_map:
            _a("### Code Hierarchy")
            _a("")
            for parent in top_level:
                kids = children_map.get(parent.id, [])
                if kids:
                    _a(f"- **{parent.name}**")
                    for kid in kids:
                        _a(f"  - {kid.name}")
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
                _a(f">")
                _a(f"> -- **{code_name}**{speaker}")
                _a("")
                shown += 1

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
        output_path = self.output_dir / f"{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        return str(output_path)

    def _export_csv(self, results: Dict[str, Any], filename: str) -> str:
        output_path = self.output_dir / f"{filename}.csv"
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
        output_path = self.output_dir / f"{filename}.md"
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
