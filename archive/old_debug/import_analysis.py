#!/usr/bin/env python3
"""
Import Analysis Script for Qualitative Coding System
Maps actual file usage based on imports to identify dead code
"""

import re
import os
from pathlib import Path
from collections import defaultdict, deque
import json

def extract_imports_from_file(file_path):
    """Extract all imports from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        imports = set()
        
        # Match: from .module import something
        relative_imports = re.findall(r'from\s+(\.[.\w]*)\s+import', content)
        for imp in relative_imports:
            # Convert relative to absolute path
            base_path = Path(file_path).parent
            parts = imp.split('.')
            parts = [p for p in parts if p]  # Remove empty parts
            
            if len(parts) > 0:
                # Navigate up directories for each leading dot after the first one
                current_path = base_path
                for part in parts:
                    current_path = current_path / part
                
                # Try to find the actual file
                py_file = current_path.with_suffix('.py')
                if py_file.exists():
                    imports.add(str(py_file.resolve()))
                
                # Try as package (__init__.py)
                init_file = current_path / '__init__.py'
                if init_file.exists():
                    imports.add(str(init_file.resolve()))
        
        # Match: from qc.module import something  
        absolute_imports = re.findall(r'from\s+(qc[\w\.]*)\s+import', content)
        for imp in absolute_imports:
            parts = imp.split('.')
            if len(parts) > 1:  # Skip just 'qc'
                # Convert to file path
                rel_path = '/'.join(parts[1:]) + '.py'  # Skip 'qc' prefix
                abs_path = Path('src/qc') / rel_path
                if abs_path.exists():
                    imports.add(str(abs_path.resolve()))
        
        # Match: import qc.module
        simple_imports = re.findall(r'import\s+(qc[\w\.]*)', content)
        for imp in simple_imports:
            parts = imp.split('.')
            if len(parts) > 1:
                rel_path = '/'.join(parts[1:]) + '.py'
                abs_path = Path('src/qc') / rel_path
                if abs_path.exists():
                    imports.add(str(abs_path.resolve()))
                    
        return list(imports)
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []

def build_dependency_graph():
    """Build dependency graph of all files in src/qc"""
    
    # Get all Python files
    src_dir = Path("src/qc")
    all_files = list(src_dir.rglob("*.py"))
    
    # Build imports map
    imports_map = {}
    for file_path in all_files:
        imports_map[str(file_path.resolve())] = extract_imports_from_file(file_path)
    
    return imports_map

def find_reachable_files(imports_map, entry_points):
    """Find all files reachable from entry points using BFS"""
    
    reachable = set()
    queue = deque(entry_points)
    
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
            
        reachable.add(current)
        
        # Add all files this one imports
        if current in imports_map:
            for imported_file in imports_map[current]:
                if imported_file not in reachable:
                    queue.append(imported_file)
    
    return reachable

def analyze_file_usage():
    """Analyze which files are actually used"""
    
    print("Building dependency graph...")
    imports_map = build_dependency_graph()
    
    # Entry points for analysis
    entry_points = [
        str(Path("src/qc/cli_robust.py").resolve()),  # Main working CLI
        str(Path("src/qc/workflows/grounded_theory.py").resolve())  # Main GT workflow
    ]
    
    print(f"Entry points: {entry_points}")
    
    # Find all reachable files
    reachable = find_reachable_files(imports_map, entry_points)
    
    # Get all files
    all_files = set(imports_map.keys())
    unreachable = all_files - reachable
    
    print(f"\nTOTAL FILES: {len(all_files)}")
    print(f"REACHABLE FILES: {len(reachable)}")
    print(f"UNREACHABLE FILES: {len(unreachable)}")
    
    print("\nREACHABLE FILES:")
    for f in sorted(reachable):
        rel_path = Path(f).relative_to(Path.cwd())
        print(f"  [USED] {rel_path}")
    
    print("\nUNREACHABLE FILES:")
    for f in sorted(unreachable):
        rel_path = Path(f).relative_to(Path.cwd())
        print(f"  [UNUSED] {rel_path}")
    
    # Save results
    results = {
        'total_files': len(all_files),
        'reachable_count': len(reachable),
        'unreachable_count': len(unreachable),
        'reachable_files': [str(Path(f).relative_to(Path.cwd())) for f in sorted(reachable)],
        'unreachable_files': [str(Path(f).relative_to(Path.cwd())) for f in sorted(unreachable)],
        'imports_map': {str(Path(k).relative_to(Path.cwd())): [str(Path(v).relative_to(Path.cwd())) for v in vals] for k, vals in imports_map.items()}
    }
    
    with open('file_usage_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: file_usage_analysis.json")
    
    return results

if __name__ == "__main__":
    analyze_file_usage()