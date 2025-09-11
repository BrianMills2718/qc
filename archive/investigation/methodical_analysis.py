#!/usr/bin/env python3
"""
METHODICAL INVESTIGATION - No assumptions, only concrete evidence
"""

import json
import glob
from pathlib import Path

def analyze_file(file_path):
    """Analyze a single output file and return concrete facts"""
    try:
        with open(file_path) as f:
            data = json.load(f)
        
        quotes = data.get('quotes', [])
        
        # Basic counts - concrete facts only
        total_quotes = len(quotes)
        quotes_with_codes = sum(1 for q in quotes if q.get('code_ids'))
        quotes_with_connections = sum(1 for q in quotes if q.get('thematic_connection') and q.get('thematic_connection') != 'none')
        none_connections = sum(1 for q in quotes if q.get('thematic_connection') == 'none')
        missing_connections = sum(1 for q in quotes if not q.get('thematic_connection'))
        null_connections = sum(1 for q in quotes if q.get('thematic_connection') is None)
        
        # Connection types - concrete distribution
        connection_types = {}
        for q in quotes:
            conn = q.get('thematic_connection')
            connection_types[str(conn)] = connection_types.get(str(conn), 0) + 1
        
        # Confidence scores - concrete values used
        confidences = []
        for q in quotes:
            conf = q.get('connection_confidence')
            if conf is not None:
                confidences.append(conf)
        
        return {
            'file_path': file_path,
            'total_quotes': total_quotes,
            'quotes_with_codes': quotes_with_codes,
            'quotes_with_connections': quotes_with_connections,
            'none_connections': none_connections,
            'missing_connections': missing_connections,
            'null_connections': null_connections,
            'connection_types': connection_types,
            'confidence_scores': sorted(set(confidences)) if confidences else [],
            'error': None
        }
        
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e),
            'total_quotes': 0
        }

def main():
    print("METHODICAL ANALYSIS OF CURRENT OUTPUT FILES")
    print("=" * 60)
    
    # Find all JSON files
    files = glob.glob('output_production/interviews/*.json')
    files.sort()
    
    print(f"Found {len(files)} output files")
    print()
    
    results = []
    for file_path in files:
        result = analyze_file(file_path)
        results.append(result)
        
        filename = Path(file_path).name
        print(f"FILE: {filename}")
        
        if result.get('error'):
            print(f"  ERROR: {result['error']}")
        else:
            print(f"  Total quotes: {result['total_quotes']}")
            print(f"  Quotes with codes: {result['quotes_with_codes']}")
            print(f"  Quotes with connections (not 'none'): {result['quotes_with_connections']}")
            print(f"  Quotes with 'none' connections: {result['none_connections']}")
            print(f"  Quotes missing connection field: {result['missing_connections']}")
            print(f"  Quotes with null connections: {result['null_connections']}")
            print(f"  Connection types: {result['connection_types']}")
            print(f"  Confidence scores: {result['confidence_scores']}")
        print()
    
    # Summary analysis - concrete patterns only
    print("CONCRETE PATTERNS OBSERVED:")
    print("-" * 40)
    
    valid_results = [r for r in results if not r.get('error')]
    
    if valid_results:
        # Pattern 1: File types
        focus_group_files = [r for r in valid_results if 'Focus Group' in r['file_path'] or 'focus group' in r['file_path']]
        individual_files = [r for r in valid_results if 'Focus Group' not in r['file_path'] and 'focus group' not in r['file_path']]
        
        print(f"Focus group files: {len(focus_group_files)}")
        print(f"Individual interview files: {len(individual_files)}")
        
        # Pattern 2: Connection rates by file type
        if focus_group_files:
            print()
            print("FOCUS GROUP FILES:")
            for r in focus_group_files:
                filename = Path(r['file_path']).name
                connection_rate = r['quotes_with_connections'] / r['total_quotes'] * 100 if r['total_quotes'] > 0 else 0
                print(f"  {filename}: {connection_rate:.1f}% connection rate")
        
        if individual_files:
            print()
            print("INDIVIDUAL INTERVIEW FILES:")
            for r in individual_files:
                filename = Path(r['file_path']).name
                connection_rate = r['quotes_with_connections'] / r['total_quotes'] * 100 if r['total_quotes'] > 0 else 0
                print(f"  {filename}: {connection_rate:.1f}% connection rate")
    
    print()
    print("ANALYSIS COMPLETE - NO INTERPRETATIONS MADE")

if __name__ == "__main__":
    main()