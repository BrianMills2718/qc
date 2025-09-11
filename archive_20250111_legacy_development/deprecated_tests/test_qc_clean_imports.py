#!/usr/bin/env python3
"""
Test QC Clean Architecture - Phase 1 Import Validation
Tests if all core files can be imported successfully in the new structure
"""

import sys
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

def test_core_imports():
    """Test importing all core modules in qc_clean"""
    print("Testing QC Clean Architecture Imports...")
    print("=" * 50)
    
    import_results = []
    
    # Test core CLI imports
    tests = [
        ("CLI - Graceful Degradation", "core.cli.graceful_degradation"),
        ("CLI - Robust Operations", "core.cli.robust_cli_operations"), 
        ("CLI - Main CLI", "core.cli.cli_robust"),
        
        # Test data layer imports  
        ("Data - Neo4j Manager", "core.data.neo4j_manager"),
        ("Data - Schema Config", "core.data.schema_config"),
        ("Data - Cypher Builder", "core.data.cypher_builder"),
        
        # Test LLM imports
        ("LLM - Handler", "core.llm.llm_handler"),
        ("LLM - Client", "core.llm.clients.llm_client"),
        ("LLM - Gemini Client", "core.llm.clients.native_gemini_client"),
        
        # Test workflow imports
        ("Workflow - GT", "core.workflow.grounded_theory"),
        ("Workflow - Prompts", "core.workflow.prompt_templates"),
        
        # Test utils imports
        ("Utils - Error Handler", "core.utils.error_handler"),
        ("Utils - Markdown Exporter", "core.utils.markdown_exporter"),
        ("Utils - Reporter", "core.utils.autonomous_reporter"),
        
        # Test config imports
        ("Config - Methodology", "config.methodology_config")
    ]
    
    for test_name, module_name in tests:
        try:
            __import__(module_name)
            print(f"[SUCCESS] {test_name}")
            import_results.append((test_name, True, None))
        except ImportError as e:
            print(f"[ERROR] {test_name}: {str(e)}")
            import_results.append((test_name, False, str(e)))
        except Exception as e:
            print(f"[ERROR] {test_name}: {str(e)}")
            import_results.append((test_name, False, str(e)))
    
    # Summary
    successful = len([r for r in import_results if r[1]])
    total = len(import_results)
    
    print(f"\n=== IMPORT TEST RESULTS ===")
    print(f"Successful: {successful}/{total}")
    print(f"Failed: {total - successful}/{total}")
    
    if successful == total:
        print("[SUCCESS] All core imports working!")
        return True
    else:
        print("[ERROR] Some imports failed - need to fix import paths")
        print("\nFailed imports:")
        for test_name, success, error in import_results:
            if not success:
                print(f"  - {test_name}: {error}")
        return False

def test_basic_functionality():
    """Test basic functionality without full dependencies"""
    print("\n=== BASIC FUNCTIONALITY TEST ===")
    
    try:
        # Test if we can create a basic config manager
        from config.methodology_config import MethodologyConfigManager
        config_mgr = MethodologyConfigManager()
        print("[SUCCESS] Config manager created")
        
        # Test error handler
        from core.utils.error_handler import ErrorHandler
        print("[SUCCESS] Error handler imported")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("QC Clean Architecture - Phase 1 Testing")
    print("Testing Date:", "2025-09-04")
    print()
    
    imports_ok = test_core_imports()
    basic_ok = test_basic_functionality()
    
    if imports_ok and basic_ok:
        print("\n[SUCCESS] Phase 1 Core Extraction - READY FOR TESTING")
    else:
        print("\n[ERROR] Phase 1 issues found - need fixes before proceeding")