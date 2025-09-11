"""
Human-Readable Formatter - Format output for human consumption
"""

from typing import Dict, Any, List
from datetime import datetime


def format_analysis_results(result_data: Dict[str, Any]) -> str:
    """Format analysis results in human-readable format"""
    
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
    
    # Codes section
    codes = results.get('codes', [])
    if codes:
        output.append("IDENTIFIED CODES:")
        output.append("-" * 20)
        for i, code in enumerate(codes, 1):
            if isinstance(code, dict):
                name = code.get('name', f'Code {i}')
                description = code.get('description', 'No description')
                frequency = code.get('frequency', 0)
                output.append(f"{i}. {name}")
                output.append(f"   Description: {description}")
                output.append(f"   Frequency: {frequency} occurrences")
                output.append("")
            else:
                output.append(f"{i}. {code}")
        output.append("")
    
    # Themes section
    themes = results.get('themes', [])
    if themes:
        output.append("EMERGENT THEMES:")
        output.append("-" * 20)
        for i, theme in enumerate(themes, 1):
            if isinstance(theme, dict):
                name = theme.get('name', f'Theme {i}')
                description = theme.get('description', 'No description')
                related_codes = theme.get('related_codes', [])
                output.append(f"{i}. {name}")
                output.append(f"   Description: {description}")
                if related_codes:
                    output.append(f"   Related codes: {', '.join(related_codes)}")
                output.append("")
            else:
                output.append(f"{i}. {theme}")
        output.append("")
    
    # Recommendations section
    recommendations = results.get('recommendations', [])
    if recommendations:
        output.append("ANALYSIS RECOMMENDATIONS:")
        output.append("-" * 30)
        for i, rec in enumerate(recommendations, 1):
            if isinstance(rec, dict):
                text = rec.get('text', rec.get('recommendation', f'Recommendation {i}'))
                priority = rec.get('priority', 'medium')
                output.append(f"{i}. [{priority.upper()}] {text}")
            else:
                output.append(f"{i}. {rec}")
        output.append("")
    
    # Summary statistics
    summary = results.get('summary', {})
    if summary:
        output.append("ANALYSIS SUMMARY:")
        output.append("-" * 20)
        for key, value in summary.items():
            formatted_key = key.replace('_', ' ').title()
            output.append(f"{formatted_key}: {value}")
        output.append("")
    
    # Metadata
    metadata = result_data.get('metadata', {})
    if metadata:
        output.append("ANALYSIS METADATA:")
        output.append("-" * 20)
        for key, value in metadata.items():
            formatted_key = key.replace('_', ' ').title()
            if key == 'timestamp' and isinstance(value, (int, float)):
                formatted_value = datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
            else:
                formatted_value = str(value)
            output.append(f"{formatted_key}: {formatted_value}")
        output.append("")
    
    output.append("=" * 60)
    
    return "\n".join(output)


def format_query_results(result_data: Dict[str, Any]) -> str:
    """Format query results in human-readable format"""
    
    if not result_data:
        return "No query results to display"
    
    output = []
    
    # Header
    output.append("=" * 50)
    output.append("QUERY RESULTS")
    output.append("=" * 50)
    output.append("")
    
    # Query information
    if 'cypher' in result_data:
        output.append("Generated Cypher Query:")
        output.append(f"  {result_data['cypher']}")
        output.append("")
    
    # Results
    data = result_data.get('data', [])
    if not data:
        output.append("No data returned from query")
        return "\n".join(output)
    
    output.append(f"Found {len(data)} results:")
    output.append("-" * 30)
    
    for i, record in enumerate(data, 1):
        output.append(f"Result {i}:")
        if isinstance(record, dict):
            for key, value in record.items():
                output.append(f"  {key}: {value}")
        else:
            output.append(f"  {record}")
        output.append("")
    
    output.append("=" * 50)
    
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
        output.append("✅ Server: Running")
    else:
        output.append("❌ Server: Not Running")
    
    # API endpoints
    endpoints = status_data.get('available_endpoints', [])
    if endpoints:
        output.append("")
        output.append("Available Endpoints:")
        for endpoint in endpoints:
            output.append(f"  • {endpoint}")
    
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