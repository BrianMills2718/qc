"""
Table Formatter - Format output as structured tables
"""

from typing import Dict, Any, List


def format_table_output(data: Dict[str, Any]) -> str:
    """Format data as structured table output.

    Expects the job-status dict returned by the API:
    ``{"job_id": ..., "status": ..., "results": {<structured_results>}}``
    """

    if not data:
        return "No data to display"

    output = []

    # Analysis results table
    if 'results' in data:
        results = data['results']

        # Codes table
        codes = results.get('codes_identified', [])
        if codes:
            output.append("CODES")
            output.append("=" * 60)

            if codes and isinstance(codes[0], dict):
                # Header
                output.append(f"{'#':<3} {'Code':<25} {'Mentions':<10} {'Confidence':<10}")
                output.append("-" * 60)

                # Rows
                for i, code in enumerate(codes, 1):
                    name = str(code.get('code', f'Code {i}'))[:24]
                    mentions = str(code.get('mention_count', 0))
                    conf = code.get('confidence', 0)
                    output.append(f"{i:<3} {name:<25} {mentions:<10} {conf:.2f}")
            else:
                for i, code in enumerate(codes, 1):
                    output.append(f"{i:2d}. {code}")

            output.append("")

        # Key themes table
        themes = results.get('key_themes', [])
        if themes:
            output.append("KEY THEMES")
            output.append("=" * 60)

            for i, theme in enumerate(themes, 1):
                if isinstance(theme, str):
                    output.append(f"{i:2d}. {theme}")
                elif isinstance(theme, dict):
                    output.append(f"{i:2d}. {theme.get('name', theme.get('title', str(theme)))}")
                else:
                    output.append(f"{i:2d}. {theme}")

            output.append("")

        # Recommendations table
        recommendations = results.get('recommendations', [])
        if recommendations:
            output.append("RECOMMENDATIONS")
            output.append("=" * 60)

            if recommendations and isinstance(recommendations[0], dict):
                # Header
                output.append(f"{'#':<3} {'Priority':<10} {'Title':<45}")
                output.append("-" * 60)

                # Rows
                for i, rec in enumerate(recommendations, 1):
                    priority = str(rec.get('priority', 'medium')).upper()[:9]
                    title = str(rec.get('title', rec.get('description', '')))[:44]
                    output.append(f"{i:<3} {priority:<10} {title:<45}")
            else:
                for i, rec in enumerate(recommendations, 1):
                    output.append(f"{i:2d}. {rec}")

            output.append("")

        # Pipeline phases
        phases = results.get('pipeline_phases', [])
        if phases:
            output.append("PIPELINE PHASES")
            output.append("=" * 40)
            output.append(f"{'Phase':<25} {'Status':<15}")
            output.append("-" * 40)
            for p in phases:
                if isinstance(p, dict):
                    output.append(f"{p.get('phase', ''):<25} {p.get('status', ''):<15}")
            output.append("")

    # Summary table
    if 'results' in data:
        results = data['results']
        summary_items = [
            ("Methodology", results.get('methodology', '')),
            ("Total interviews", results.get('total_interviews', '')),
            ("Total codes", results.get('total_codes', '')),
            ("Model", results.get('model_used', '')),
            ("Processing time", f"{results.get('processing_time_seconds', '')}s"),
        ]
        summary_items = [(k, v) for k, v in summary_items if v]
        if summary_items:
            output.append("SUMMARY")
            output.append("=" * 40)
            for key, value in summary_items:
                output.append(f"{key:<20}: {value}")
            output.append("")

    return "\n".join(output) if output else "No tabular data available"


def format_simple_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format simple table with headers and rows"""

    if not headers or not rows:
        return "No data to display"

    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    output = []

    # Header
    header_row = " | ".join(f"{header:<{col_widths[i]}}" for i, header in enumerate(headers))
    output.append(header_row)
    output.append("-" * len(header_row))

    # Rows
    for row in rows:
        row_cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                row_cells.append(f"{str(cell):<{col_widths[i]}}")
        output.append(" | ".join(row_cells))

    return "\n".join(output)
