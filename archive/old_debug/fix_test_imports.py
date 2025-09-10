#!/usr/bin/env python3
"""
Fix test imports from 'qc.' to 'src.qc.'
Run with: python fix_test_imports.py --dry-run first
"""
import os
import re
from pathlib import Path

def fix_imports(dry_run=True):
    """Fix all test imports from qc. to src.qc."""
    test_dir = Path("tests")
    fixed_files = []
    
    for py_file in test_dir.rglob("*.py"):
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all qc imports
        old_pattern = r'from qc\.'
        new_pattern = 'from src.qc.'
        
        if re.search(old_pattern, content):
            new_content = re.sub(old_pattern, new_pattern, content)
            
            if not dry_run:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            fixed_files.append(py_file)
            print(f"{'Would fix' if dry_run else 'Fixed'}: {py_file}")
    
    print(f"\nTotal files to fix: {len(fixed_files)}")
    return fixed_files

if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    
    print(f"Running in {'DRY RUN' if dry_run else 'ACTUAL FIX'} mode")
    fixed = fix_imports(dry_run)
    
    if dry_run and fixed:
        print("\nRun without --dry-run to apply fixes")