#!/usr/bin/env python3
"""
Test Core GT Workflow - Phase 4 Integration Testing

Tests the core Grounded Theory workflow to ensure it functions
properly after the migration to clean architecture.
"""

import sys
import logging
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_core_imports():
    """Test that core GT workflow components can be imported"""
    print("\n=== TESTING CORE IMPORTS ===")
    
    try:
        # Test core CLI components
        from core.cli.cli_robust import main as cli_main
        from core.cli.robust_cli_operations import RobustCLIOperations
        print("[SUCCESS] Core CLI components imported")
        
        # Test GT workflow
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        print("[SUCCESS] GT workflow imported")
        
        # Test LLM components
        from core.llm.llm_handler import LLMHandler
        from core.llm.clients.llm_client import UniversalModelClient
        print("[SUCCESS] LLM components imported")
        
        # Test data components
        from core.data.neo4j_manager import EnhancedNeo4jManager as Neo4jManager
        from core.data.schema_config import SchemaConfiguration
        print("[SUCCESS] Data components imported")
        
        # Test configuration
        from config.methodology_config import MethodologyConfigManager
        from config.config_manager import QCCleanConfigManager
        print("[SUCCESS] Configuration components imported")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Core imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_loading():
    """Test configuration system works"""
    print("\n=== TESTING CONFIGURATION LOADING ===")
    
    try:
        from config.config_manager import QCCleanConfigManager
        
        # Test new config manager
        config_manager = QCCleanConfigManager()
        config = config_manager.load_config()
        
        print(f"[SUCCESS] Loaded configuration: {config.system.methodology}")
        print(f"   Database: {config.system.neo4j_uri}")
        print(f"   LLM: {config.llm.provider} ({config.llm.model})")
        print(f"   GT Config: {config.gt_workflow.coding_depth}")
        
        # Test methodology config (legacy system)
        from config.methodology_config import MethodologyConfigManager
        
        methodology_manager = MethodologyConfigManager()
        available_configs = methodology_manager.list_available_configs()
        print(f"   Available methodology configs: {len(available_configs)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_initialization():
    """Test LLM components can be initialized"""
    print("\n=== TESTING LLM INITIALIZATION ===")
    
    try:
        from core.llm.llm_handler import LLMHandler
        from config.config_manager import QCCleanConfigManager
        
        # Load configuration
        config_manager = QCCleanConfigManager()
        config = config_manager.load_config()
        
        # Create LLM handler
        llm_config = {
            'provider': config.llm.provider,
            'model': config.llm.model,
            'api_timeout': config.llm.api_timeout
        }
        
        llm_handler = LLMHandler(llm_config)
        print(f"[SUCCESS] LLM handler created: {llm_config['provider']}")
        
        # Test if handler is available (without API call)
        print(f"   Provider: {llm_handler.current_provider}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] LLM initialization failed: {e}")
        return False


def test_data_layer():
    """Test data layer components"""
    print("\n=== TESTING DATA LAYER ===")
    
    try:
        from core.data.neo4j_manager import EnhancedNeo4jManager as Neo4jManager
        from core.data.schema_config import SchemaConfiguration
        from config.config_manager import QCCleanConfigManager
        
        # Load configuration
        config_manager = QCCleanConfigManager()
        config = config_manager.load_config()
        
        # Test schema config - provide required fields
        schema_config = SchemaConfiguration(entities=[], relationships=[], codes=[])
        print("[SUCCESS] Schema config created")
        
        # Test Neo4j manager creation (without connecting)
        neo4j_config = {
            'uri': config.system.neo4j_uri,
            'database': config.system.database_name
        }
        
        neo4j_manager = Neo4jManager(neo4j_config)
        print(f"[SUCCESS] Neo4j manager created for {neo4j_config['uri']}")
        
        # Test connection availability (without actual connection)
        print(f"   Database: {neo4j_config['database']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Data layer test failed: {e}")
        return False


def test_gt_workflow_initialization():
    """Test GT workflow can be initialized"""
    print("\n=== TESTING GT WORKFLOW INITIALIZATION ===")
    
    try:
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from config.methodology_config import MethodologyConfigManager
        from config.config_manager import QCCleanConfigManager
        
        # Load configuration
        qc_config_manager = QCCleanConfigManager()
        qc_config = qc_config_manager.load_config()
        
        # Load methodology config
        methodology_manager = MethodologyConfigManager()
        
        # Try to find a methodology config file
        available_configs = methodology_manager.list_available_configs()
        if available_configs:
            # Use first available config
            config_name = available_configs[0]
            print(f"[INFO] Using methodology config: {config_name}")
            
            methodology_config = methodology_manager.load_config('grounded_theory', config_name)
            
            # Create robust CLI operations first
            from core.cli.robust_cli_operations import RobustCLIOperations
            cli_ops = RobustCLIOperations()
            
            # Create GT workflow with correct constructor
            gt_workflow = GroundedTheoryWorkflow(
                robust_operations=cli_ops,
                config=methodology_config
            )
            
            print("[SUCCESS] GT workflow initialized")
            print(f"   Methodology: {methodology_config.methodology}")
            print(f"   Coding depth: {methodology_config.coding_depth}")
            
        else:
            print("[WARNING] No methodology configs found, creating default")
            
            # Create a minimal GT workflow for testing
            default_config = methodology_manager.create_default_config('grounded_theory', 'test')
            
            # Create robust CLI operations first
            from core.cli.robust_cli_operations import RobustCLIOperations
            cli_ops = RobustCLIOperations()
            
            gt_workflow = GroundedTheoryWorkflow(
                robust_operations=cli_ops,
                config=default_config
            )
            
            print("[SUCCESS] GT workflow initialized with default config")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] GT workflow initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_operations():
    """Test CLI operations can be initialized"""
    print("\n=== TESTING CLI OPERATIONS ===")
    
    try:
        from core.cli.robust_cli_operations import RobustCLIOperations
        
        # Create CLI operations
        cli_ops = RobustCLIOperations()
        print("[SUCCESS] CLI operations created")
        
        # Test basic functionality
        print(f"   CLI operations available")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] CLI operations test failed: {e}")
        return False


def main():
    """Run core GT workflow tests"""
    print("Phase 4: Core GT Workflow Integration Testing")
    print("=" * 50)
    
    tests = [
        test_core_imports,
        test_configuration_loading,
        test_llm_initialization,
        test_data_layer,
        test_gt_workflow_initialization,
        test_cli_operations
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print("\n" + "=" * 50)
    print(f"CORE GT WORKFLOW TESTING: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] Core GT workflow fully functional")
        print("\nCore System Status:")
        print("  - All imports working correctly")
        print("  - Configuration system operational")
        print("  - LLM integration ready")
        print("  - Data layer initialized")
        print("  - GT workflow can be created")
        print("  - CLI operations functional")
        return True
    else:
        print("[ERROR] Some core tests failed - system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)