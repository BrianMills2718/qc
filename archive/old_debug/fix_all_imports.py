#!/usr/bin/env python3
"""
Fix all import statements from 'qc.' to 'src.qc.' throughout the codebase
"""
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path, dry_run=True):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False
    
    # Find and replace patterns
    patterns = [
        (r'^from qc\.', 'from src.qc.'),
        (r'^import qc\.', 'import src.qc.'),
        (r'^import qc$', 'import src.qc'),
        (r'"qc\.', '"src.qc.'),  # String references
        (r"'qc\.", "'src.qc."),  # String references
    ]
    
    modified = False
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            modified = True
            content = new_content
    
    if modified:
        if not dry_run:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Fixed: {file_path}")
            except Exception as e:
                print(f"Error writing {file_path}: {e}")
                return False
        else:
            print(f"Would fix: {file_path}")
    
    return modified

def main():
    """Fix all imports in the codebase"""
    import sys
    
    dry_run = "--dry-run" in sys.argv
    
    print(f"Running in {'DRY RUN' if dry_run else 'ACTUAL FIX'} mode")
    print("=" * 60)
    
    # Define paths to process
    paths_to_process = [
        "src/",
        "tests/",
        "scripts/",
        "archive/",
        "test_*.py",  # Root level test files
    ]
    
    fixed_files = []
    error_files = []
    
    # Process each path
    for path_pattern in paths_to_process:
        if path_pattern.endswith('/'):
            # Directory - process all Python files
            dir_path = Path(path_pattern)
            if dir_path.exists():
                for py_file in dir_path.rglob("*.py"):
                    if fix_imports_in_file(py_file, dry_run):
                        fixed_files.append(py_file)
        else:
            # Pattern - use glob
            for py_file in Path('.').glob(path_pattern):
                if py_file.suffix == '.py':
                    if fix_imports_in_file(py_file, dry_run):
                        fixed_files.append(py_file)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Total files to fix: {len(fixed_files)}")
    
    if dry_run and fixed_files:
        print("\nRun without --dry-run to apply fixes")
        print("python fix_all_imports.py")
    elif not dry_run:
        print("\nAll imports have been fixed!")
        print("You may need to restart any running Python processes.")

if __name__ == "__main__":
    main()