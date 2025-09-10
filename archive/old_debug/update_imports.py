#!/usr/bin/env python3
"""
Import Path Update Utility for QC Clean Architecture Migration
Updates import paths from old src.qc structure to new qc_clean structure
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path, import_mapping: dict):
    """Update import statements in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update each import mapping
        for old_import, new_import in import_mapping.items():
            # Handle different import patterns
            patterns = [
                f"from {old_import} import",
                f"from .{old_import} import", 
                f"import {old_import}",
                f"from ..{old_import} import"
            ]
            
            replacements = [
                f"from {new_import} import",
                f"from .{new_import} import",
                f"import {new_import}",
                f"from ..{new_import} import"
            ]
            
            for pattern, replacement in zip(patterns, replacements):
                content = content.replace(pattern, replacement)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated imports in: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update all imports in qc_clean directory"""
    
    # Define import mappings from old structure to new structure
    import_mapping = {
        # Core imports
        "src.qc.core.graceful_degradation": "qc_clean.core.cli.graceful_degradation",
        "src.qc.core.robust_cli_operations": "qc_clean.core.cli.robust_cli_operations",
        "src.qc.core.neo4j_manager": "qc_clean.core.data.neo4j_manager",
        "src.qc.core.schema_config": "qc_clean.core.data.schema_config",
        "src.qc.core.llm_client": "qc_clean.core.llm.clients.llm_client",
        "src.qc.core.native_gemini_client": "qc_clean.core.llm.clients.native_gemini_client",
        
        # Workflow imports
        "src.qc.workflows.grounded_theory": "qc_clean.core.workflow.grounded_theory",
        "src.qc.workflows.prompt_templates": "qc_clean.core.workflow.prompt_templates",
        
        # LLM imports
        "src.qc.llm.llm_handler": "qc_clean.core.llm.llm_handler",
        
        # Query imports
        "src.qc.query.cypher_builder": "qc_clean.core.data.cypher_builder",
        
        # Config imports
        "src.qc.config.methodology_config": "qc_clean.config.methodology_config",
        
        # Utils imports
        "src.qc.utils.error_handler": "qc_clean.core.utils.error_handler",
        "src.qc.utils.markdown_exporter": "qc_clean.core.utils.markdown_exporter",
        "src.qc.reporting.autonomous_reporter": "qc_clean.core.utils.autonomous_reporter",
        
        # Relative import fixes
        ".core.graceful_degradation": "graceful_degradation",
        ".core.robust_cli_operations": "robust_cli_operations", 
        ".monitoring.system_monitor": "qc_clean.core.utils.system_monitor",
        ".utils.error_handler": "qc_clean.core.utils.error_handler"
    }
    
    qc_clean_dir = Path("qc_clean")
    files_updated = 0
    
    # Process all Python files in qc_clean directory
    for py_file in qc_clean_dir.rglob("*.py"):
        if py_file.name != "__init__.py":
            if update_imports_in_file(py_file, import_mapping):
                files_updated += 1
    
    print(f"\nUpdate complete. Modified {files_updated} files.")

if __name__ == "__main__":
    main()