"""
JSON Formatter - Format output as JSON for programmatic consumption
"""

import json
from typing import Dict, Any


def format_json_output(data: Dict[str, Any]) -> str:
    """Format data as pretty-printed JSON"""
    try:
        return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable data
        return json.dumps({
            'error': f'JSON serialization failed: {str(e)}',
            'raw_data': str(data)
        }, indent=2)


def format_compact_json(data: Dict[str, Any]) -> str:
    """Format data as compact JSON"""
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError) as e:
        return json.dumps({
            'error': f'JSON serialization failed: {str(e)}'
        }, separators=(',', ':'))