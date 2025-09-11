"""
Table Formatter - Format output as structured tables
"""

from typing import Dict, Any, List


def format_table_output(data: Dict[str, Any]) -> str:
    """Format data as structured table output"""
    
    if not data:
        return "No data to display"
    
    output = []
    
    # Analysis results table
    if 'results' in data:
        results = data['results']
        
        # Codes table
        codes = results.get('codes', [])
        if codes:
            output.append("CODES")
            output.append("=" * 60)
            
            if codes and isinstance(codes[0], dict):
                # Header
                output.append(f"{'#':<3} {'Name':<20} {'Frequency':<10} {'Description':<25}")
                output.append("-" * 60)
                
                # Rows
                for i, code in enumerate(codes, 1):
                    name = str(code.get('name', f'Code {i}'))[:19]
                    freq = str(code.get('frequency', 0))
                    desc = str(code.get('description', ''))[:24]
                    output.append(f"{i:<3} {name:<20} {freq:<10} {desc:<25}")
            else:
                for i, code in enumerate(codes, 1):
                    output.append(f"{i:2d}. {code}")
            
            output.append("")
        
        # Themes table
        themes = results.get('themes', [])
        if themes:
            output.append("THEMES")
            output.append("=" * 60)
            
            if themes and isinstance(themes[0], dict):
                # Header
                output.append(f"{'#':<3} {'Name':<25} {'Description':<30}")
                output.append("-" * 60)
                
                # Rows
                for i, theme in enumerate(themes, 1):
                    name = str(theme.get('name', f'Theme {i}'))[:24]
                    desc = str(theme.get('description', ''))[:29]
                    output.append(f"{i:<3} {name:<25} {desc:<30}")
            else:
                for i, theme in enumerate(themes, 1):
                    output.append(f"{i:2d}. {theme}")
            
            output.append("")
        
        # Recommendations table
        recommendations = results.get('recommendations', [])
        if recommendations:
            output.append("RECOMMENDATIONS")
            output.append("=" * 60)
            
            if recommendations and isinstance(recommendations[0], dict):
                # Header
                output.append(f"{'#':<3} {'Priority':<10} {'Recommendation':<45}")
                output.append("-" * 60)
                
                # Rows
                for i, rec in enumerate(recommendations, 1):
                    priority = str(rec.get('priority', 'medium')).upper()[:9]
                    text = str(rec.get('text', rec.get('recommendation', '')))[:44]
                    output.append(f"{i:<3} {priority:<10} {text:<45}")
            else:
                for i, rec in enumerate(recommendations, 1):
                    output.append(f"{i:2d}. {rec}")
            
            output.append("")
    
    # Query results table
    if 'data' in data and isinstance(data['data'], list):
        query_data = data['data']
        if query_data:
            output.append("QUERY RESULTS")
            output.append("=" * 60)
            
            if isinstance(query_data[0], dict):
                # Get all unique keys
                all_keys = set()
                for record in query_data:
                    all_keys.update(record.keys())
                
                keys = sorted(all_keys)
                
                # Header
                header_row = " | ".join(f"{key:<15}" for key in keys)
                output.append(header_row)
                output.append("-" * len(header_row))
                
                # Rows
                for record in query_data:
                    row_values = []
                    for key in keys:
                        value = str(record.get(key, ''))[:14]
                        row_values.append(f"{value:<15}")
                    output.append(" | ".join(row_values))
            else:
                for i, record in enumerate(query_data, 1):
                    output.append(f"{i:2d}. {record}")
            
            output.append("")
    
    # Summary table
    summary = data.get('results', {}).get('summary', {}) or data.get('summary', {})
    if summary:
        output.append("SUMMARY")
        output.append("=" * 30)
        
        for key, value in summary.items():
            formatted_key = key.replace('_', ' ').title()
            output.append(f"{formatted_key:<20}: {value}")
        
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