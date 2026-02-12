"""
Human-Readable Formatter - Format output for human consumption
"""

from typing import Dict, Any, List
from datetime import datetime


def format_analysis_results(result_data: Dict[str, Any]) -> str:
    """Format analysis results in human-readable format.

    Expects the job-status dict returned by the API:
    ``{"job_id": ..., "status": ..., "results": {<structured_results>}}``
    """

    if not result_data:
        return "No results to display"

    output = []

    # Header
    output.append("=" * 60)
    output.append("QUALITATIVE CODING ANALYSIS RESULTS")
    output.append("=" * 60)
    output.append("")

    # Job information
    job_id = result_data.get('job_id', 'N/A')
    status = result_data.get('status', 'unknown')
    output.append(f"Job ID: {job_id}")
    output.append(f"Status: {status.upper()}")
    output.append("")

    # Results section
    results = result_data.get('results', {})
    if not results:
        output.append("No analysis results available")
        return "\n".join(output)

    # Summary line
    summary_text = results.get('analysis_summary', '')
    if summary_text:
        output.append(summary_text)
        output.append(f"Model: {results.get('model_used', 'N/A')}")
        output.append(f"Processing time: {results.get('processing_time_seconds', 'N/A')}s")
        output.append("")

    # Codes section
    codes = results.get('codes_identified', [])
    if codes:
        output.append("IDENTIFIED CODES:")
        output.append("-" * 40)
        for i, code in enumerate(codes, 1):
            if isinstance(code, dict):
                name = code.get('code', f'Code {i}')
                mentions = code.get('mention_count', 0)
                confidence = code.get('confidence', 0)
                output.append(f"{i:2d}. {name}  ({mentions} mentions, {confidence:.0%} confidence)")
            else:
                output.append(f"{i:2d}. {code}")
        output.append("")

    # Speakers section
    speakers = results.get('speakers_identified', [])
    if speakers:
        output.append("SPEAKERS:")
        output.append("-" * 40)
        for p in speakers:
            if isinstance(p, dict):
                name = p.get('name', 'Unknown')
                role = p.get('role', '')
                perspective = p.get('perspective', '')
                output.append(f"  {name}" + (f" ({role})" if role else ""))
                if perspective:
                    output.append(f"    {perspective[:100]}")
            else:
                output.append(f"  {p}")
        output.append("")

    # Key themes section
    themes = results.get('key_themes', [])
    if themes:
        output.append("KEY THEMES:")
        output.append("-" * 40)
        for i, theme in enumerate(themes, 1):
            if isinstance(theme, str):
                output.append(f"{i:2d}. {theme}")
            elif isinstance(theme, dict):
                output.append(f"{i:2d}. {theme.get('name', theme.get('title', str(theme)))}")
            else:
                output.append(f"{i:2d}. {theme}")
        output.append("")

    # Recommendations section
    recommendations = results.get('recommendations', [])
    if recommendations:
        output.append("RECOMMENDATIONS:")
        output.append("-" * 40)
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                title = rec.get('title', f'Recommendation {i}')
                priority = rec.get('priority', 'medium')
                description = rec.get('description', '')
                output.append(f"{i:2d}. [{priority.upper()}] {title}")
                if description:
                    output.append(f"    {description[:120]}")
            else:
                output.append(f"{i:2d}. {rec}")
        output.append("")

    # Key relationships
    relationships = results.get('key_relationships', [])
    if relationships:
        output.append("KEY RELATIONSHIPS:")
        output.append("-" * 40)
        for rel in relationships:
            if isinstance(rel, dict):
                entities = rel.get('entities', '')
                rel_type = rel.get('type', '')
                output.append(f"  {entities} [{rel_type}]")
        output.append("")

    # GT-specific
    core_cats = results.get('core_categories', [])
    if core_cats:
        output.append("CORE CATEGORIES:")
        output.append("-" * 40)
        for cc in core_cats:
            if isinstance(cc, dict):
                output.append(f"  {cc.get('name', 'Unknown')}: {cc.get('definition', '')[:80]}")
        output.append("")

    theo_model = results.get('theoretical_model', {})
    if theo_model:
        output.append("THEORETICAL MODEL:")
        output.append("-" * 40)
        output.append(f"  {theo_model.get('model_name', 'Unnamed')}")
        framework = theo_model.get('theoretical_framework', '')
        if framework:
            output.append(f"  {framework[:200]}")
        output.append("")

    # Data warnings
    warnings = results.get('data_warnings', [])
    if warnings:
        output.append("DATA WARNINGS:")
        for w in warnings:
            output.append(f"  ! {w}")
        output.append("")

    # Pipeline phases
    phases = results.get('pipeline_phases', [])
    if phases:
        output.append("PIPELINE PHASES:")
        for p in phases:
            if isinstance(p, dict):
                output.append(f"  {p.get('phase', 'unknown'):30s} {p.get('status', '')}")
        output.append("")

    output.append("=" * 60)

    return "\n".join(output)


def format_status_info(status_data: Dict[str, Any]) -> str:
    """Format status information in human-readable format"""

    output = []

    output.append("=" * 40)
    output.append("SYSTEM STATUS")
    output.append("=" * 40)
    output.append("")

    # Server status
    server_status = status_data.get('server_status', 'unknown')
    if server_status == 'running':
        output.append("Server: Running")
    else:
        output.append("Server: Not Running")

    # API endpoints
    endpoints = status_data.get('available_endpoints', [])
    if endpoints:
        output.append("")
        output.append("Available Endpoints:")
        for endpoint in endpoints:
            output.append(f"  {endpoint}")

    # Job status (if provided)
    if 'job_status' in status_data:
        job_data = status_data['job_status']
        output.append("")
        output.append("Job Status:")
        output.append(f"  ID: {job_data.get('job_id', 'N/A')}")
        output.append(f"  Status: {job_data.get('status', 'unknown').upper()}")

        if 'progress' in job_data:
            progress = job_data['progress']
            output.append(f"  Progress: {progress}%")

    # System info
    if 'system_info' in status_data:
        sys_info = status_data['system_info']
        output.append("")
        output.append("System Information:")
        for key, value in sys_info.items():
            formatted_key = key.replace('_', ' ').title()
            output.append(f"  {formatted_key}: {value}")

    output.append("")
    output.append("=" * 40)

    return "\n".join(output)
