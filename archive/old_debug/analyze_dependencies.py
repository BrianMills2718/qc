#!/usr/bin/env python3
"""
Comprehensive dependency analysis for QC system - Task 4.2
Compares static imports vs runtime usage to identify dead code
"""

import ast
import os
from pathlib import Path
from collections import defaultdict
import re
import json

def extract_imports(file_path):
    """Extract import statements from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = []
        
        # Find src.qc imports using regex patterns
        patterns = [
            r'from\s+src\.qc([\w\.]*)\s+import',
            r'import\s+src\.qc([\w\.]*)',
            r'from\s+\.qc([\w\.]*)\s+import',  # relative from parent
            r'from\s+\.([\w\.]+)\s+import'     # relative imports
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if pattern.startswith('from src.qc'):
                    imports.append(f"src.qc{match}")
                elif pattern.startswith('import src.qc'):
                    imports.append(f"src.qc{match}")
                elif pattern.startswith('from .qc'):
                    imports.append(f"src.qc{match}")
                elif pattern.startswith('from .'):
                    # Convert relative import to absolute
                    rel_path = str(file_path.parent).replace('\\', '.').replace('/', '.')
                    if 'src.qc' in rel_path:
                        base = rel_path
                        imports.append(f"{base}.{match}")
        
        return list(set(imports))  # Remove duplicates
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def categorize_subsystems():
    """Categorize files by subsystem for dead code analysis"""
    return {
        'Core System': ['cli_robust', 'core/', 'workflows/', 'llm/', 'config/', 'reporting/', 'monitoring/'],
        'QCA Analysis': ['qca/', 'qca_'],  
        'API Layer': ['api/', 'endpoints/', 'web/', 'fastapi'],
        'Validation System': ['validation/', 'academic/'],
        'Analytics': ['analytics/', 'quote_processing/', 'frequency_analyzer'],
        'Web Interface': ['ui/', 'interface/', 'templates/'],
        'Alternative Extractors': ['extraction/', 'extractor'],
        'Taxonomy System': ['taxonomy/', 'ai_taxonomy'],
        'Advanced Query System': ['query/', 'cypher/', 'advanced_query'],
        'Research Integration': ['research/', 'integration/', 'academic_integration'],
        'External Interfaces': ['external/', 'connector/'],
        'Additional Utils': ['utils/'],
        'Analysis Tools': ['analysis/', 'memos/']
    }

def analyze_runtime_usage():
    """Runtime essential modules from Task 4.1 evidence"""
    return {
        'src.qc.cli_robust',
        'src.qc.core.robust_cli_operations', 
        'src.qc.core.graceful_degradation',
        'src.qc.core.neo4j_manager',
        'src.qc.core.schema_config',
        'src.qc.query.cypher_builder',
        'src.qc.llm.llm_handler',
        'src.qc.core.llm_client',
        'src.qc.core.native_gemini_client',
        'src.qc.extraction.multi_pass_extractor',
        'src.qc.extraction.extraction_schemas',
        'src.qc.extraction.semantic_code_matcher',
        'src.qc.extraction.semantic_quote_extractor',
        'src.qc.monitoring.system_monitor',
        'src.qc.monitoring.health',
        'src.qc.utils.error_handler',
        'src.qc.utils.markdown_exporter',
        'src.qc.utils.token_manager',
        'src.qc.workflows.grounded_theory',
        'src.qc.workflows.prompt_templates',
        'src.qc.config.methodology_config',
        'src.qc.analysis.analytical_memos',
        'src.qc.reporting.autonomous_reporter'
    }

def file_to_module(file_path):
    """Convert file path to module name"""
    path_str = str(file_path)
    if 'src' in path_str:
        # Extract from src onward
        parts = path_str.split('src', 1)[1]
        parts = parts.replace('\\', '.').replace('/', '.')
        parts = parts.replace('.py', '')
        if parts.startswith('.'):
            parts = parts[1:]
        return f"src.{parts}"
    return path_str

def analyze_dependencies():
    """Main analysis function"""
    src_dir = Path("src/qc")
    if not src_dir.exists():
        print("ERROR: src/qc directory not found")
        return
    
    all_files = [f for f in src_dir.rglob("*.py") if f.name != '__init__.py']
    runtime_essential = analyze_runtime_usage()
    subsystem_categories = categorize_subsystems()
    
    print("=== DEPENDENCY ANALYSIS - TASK 4.2 ===")
    print(f"Total files found: {len(all_files)}")
    print(f"Runtime essential modules: {len(runtime_essential)}")
    
    # Analyze each file
    analysis_results = {
        'files_analyzed': len(all_files),
        'runtime_essential': len(runtime_essential),
        'static_imports': {},
        'dead_code_files': [],
        'subsystem_breakdown': defaultdict(lambda: {'essential': 0, 'dead': 0, 'files': []})
    }
    
    for file_path in all_files:
        module_name = file_to_module(file_path)
        imports = extract_imports(file_path)
        
        # Determine if file is essential or dead code
        is_essential = module_name in runtime_essential
        
        # Categorize by subsystem
        subsystem = 'Uncategorized'
        for cat_name, patterns in subsystem_categories.items():
            if any(pattern in str(file_path).lower() for pattern in patterns):
                subsystem = cat_name
                break
        
        # Update analysis results
        analysis_results['static_imports'][module_name] = imports
        
        file_info = {
            'module': module_name,
            'path': str(file_path),
            'imports': imports,
            'is_essential': is_essential
        }
        
        analysis_results['subsystem_breakdown'][subsystem]['files'].append(file_info)
        
        if is_essential:
            analysis_results['subsystem_breakdown'][subsystem]['essential'] += 1
        else:
            analysis_results['subsystem_breakdown'][subsystem]['dead'] += 1
            analysis_results['dead_code_files'].append(file_info)
    
    # Calculate dead code percentage
    dead_code_count = len(analysis_results['dead_code_files'])
    dead_code_percentage = (dead_code_count / analysis_results['files_analyzed']) * 100
    
    print(f"\n=== RESULTS ===")
    print(f"Essential files: {analysis_results['runtime_essential']} ({(analysis_results['runtime_essential']/analysis_results['files_analyzed']*100):.1f}%)")
    print(f"Dead code files: {dead_code_count} ({dead_code_percentage:.1f}%)")
    
    print(f"\n=== SUBSYSTEM BREAKDOWN ===")
    for subsystem, data in analysis_results['subsystem_breakdown'].items():
        total = data['essential'] + data['dead'] 
        if total > 0:
            essential_pct = (data['essential'] / total) * 100
            print(f"{subsystem}: {data['essential']}/{total} essential ({essential_pct:.0f}%)")
    
    print(f"\n=== DEAD CODE BY SUBSYSTEM ===")
    for subsystem, data in analysis_results['subsystem_breakdown'].items():
        if data['dead'] > 0:
            dead_files = [f for f in data['files'] if not f['is_essential']]
            print(f"\n{subsystem} ({data['dead']} files):")
            for file_info in dead_files[:5]:  # Show first 5
                print(f"  - {file_info['module']}")
            if len(dead_files) > 5:
                print(f"  ... and {len(dead_files) - 5} more")
    
    # Save detailed results
    save_results(analysis_results, dead_code_percentage)
    
    return analysis_results

def save_results(analysis_results, dead_code_percentage):
    """Save analysis results to JSON file"""
    output_file = "dependency_analysis_task42.json"
    
    # Prepare serializable data
    serializable_results = {
        'summary': {
            'files_analyzed': analysis_results['files_analyzed'],
            'runtime_essential': analysis_results['runtime_essential'],
            'dead_code_count': len(analysis_results['dead_code_files']),
            'dead_code_percentage': round(dead_code_percentage, 1)
        },
        'subsystem_breakdown': {},
        'dead_code_files': analysis_results['dead_code_files']
    }
    
    for subsystem, data in analysis_results['subsystem_breakdown'].items():
        serializable_results['subsystem_breakdown'][subsystem] = {
            'essential_count': data['essential'],
            'dead_count': data['dead'],
            'files': data['files']
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    analyze_dependencies()