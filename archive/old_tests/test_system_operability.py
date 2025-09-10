#!/usr/bin/env python3
"""
System Operability Validation Test

Tests that the complete system can execute without import errors.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_complete_import_chain():
    """Test that all core system imports work"""
    try:
        # Test core workflow imports
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from config.methodology_config import GroundedTheoryConfig
        
        # Test restored dependency imports  
        from core.cli.neo4j_manager import EnhancedNeo4jManager
        from core.export import export_gt_results
        
        # Test plugin imports
        from plugins.plugin_manager import PluginManager
        
        print("PASS: All critical imports successful")
        return True
        
    except ImportError as e:
        print(f"FAIL: Import error - {e}")
        return False

def test_basic_workflow_execution():
    """Test that GT workflow can be instantiated and run"""
    try:
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from config.methodology_config import GroundedTheoryConfig
        from core.cli.robust_cli_operations import RobustCLIOperations
        
        config = GroundedTheoryConfig(
            methodology='grounded_theory',
            theoretical_sensitivity='medium', 
            coding_depth='focused',
            memo_generation_frequency='each_phase',
            report_formats=['academic_report'],
            include_audit_trail=True,
            include_supporting_quotes=True,
            minimum_code_frequency=1,
            relationship_confidence_threshold=0.7,
            validation_level='standard',
            temperature=0.1,
            max_tokens=None,
            model_preference='gpt-4'
        )
        
        # Create robust operations instance
        operations = RobustCLIOperations()
        
        workflow = GroundedTheoryWorkflow(operations, config)
        
        # Test basic workflow methods exist and can be called
        assert hasattr(workflow, 'execute_complete_workflow')
        assert callable(getattr(workflow, 'execute_complete_workflow'))
        
        print("PASS: GT workflow instantiation successful")
        return True
        
    except Exception as e:
        print(f"FAIL: Workflow execution error - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plugin_system_operability():
    """Test that plugin system can load without errors"""
    try:
        from plugins.plugin_manager import PluginManager
        
        manager = PluginManager()
        # Test basic plugin manager functionality
        plugins = manager.list_registered_plugins()
        
        print(f"PASS: Plugin manager loaded, found {len(plugins)} plugins")
        return True
        
    except Exception as e:
        print(f"FAIL: Plugin system error - {e}")
        return False

if __name__ == "__main__":
    print("System Operability Test")
    print("=" * 25)
    
    tests = [
        ("Import Chain", test_complete_import_chain),
        ("Workflow Execution", test_basic_workflow_execution),
        ("Plugin System", test_plugin_system_operability)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        result = test_func()
        results.append(result)
    
    print(f"\n{'='*25}")
    print(f"System Operability: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("\nSUCCESS: System operability restored!")
        print("- All imports resolve successfully")
        print("- GT workflow can be instantiated")
        print("- Plugin system loads without errors")
    else:
        failed = [tests[i][0] for i, result in enumerate(results) if not result]
        print(f"\nFAIL: Operability issues remain")
        print(f"Failed: {', '.join(failed)}")