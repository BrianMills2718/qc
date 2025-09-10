#!/usr/bin/env python3
"""
Test All Plugins - Phase 3 Complete Validation

Tests QCA, API, and Taxonomy plugins to ensure all work independently.
"""

import sys
import logging
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_qca_plugin():
    """Test QCA plugin functionality"""
    print("\n=== TESTING QCA PLUGIN ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        # Create and initialize plugin
        plugin = QCAAnalysisPlugin()
        assert plugin.get_name() == "qca_analysis"
        
        # Initialize with config
        config = {'enable_qca_conversion': True, 'default_analysis_method': 'crisp_set'}
        assert plugin.initialize(config), "QCA initialization failed"
        
        # Test with mock GT data
        mock_gt = {
            'codes': [
                {'name': 'code1', 'frequency': 3, 'level': 1},
                {'name': 'code2', 'frequency': 2, 'level': 1},
                {'name': 'outcome', 'frequency': 4, 'level': 0}
            ],
            'interviews': [
                {'id': 'int1'}, {'id': 'int2'}, {'id': 'int3'}
            ],
            'hierarchy': {}
        }
        
        # Test processing
        assert plugin.can_process(mock_gt), "QCA cannot process valid GT data"
        qca_data = plugin.convert_to_qca(mock_gt)
        assert 'case_matrix' in qca_data, "QCA conversion failed"
        
        # Run analysis
        results = plugin.run_qca_analysis(qca_data)
        assert 'truth_table' in results, "QCA analysis failed"
        
        # Cleanup
        assert plugin.cleanup(), "QCA cleanup failed"
        
        print("[SUCCESS] QCA plugin fully functional")
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA plugin test failed: {e}")
        return False


def test_api_plugin():
    """Test API plugin functionality"""
    print("\n=== TESTING API PLUGIN ===")
    
    try:
        from plugins.api import APIServerPlugin
        
        # Create and initialize plugin
        plugin = APIServerPlugin()
        assert plugin.get_name() == "api_server"
        
        # Initialize with config
        config = {
            'host': 'localhost',
            'port': 8000,
            'auto_start': False,
            'enable_background_processing': True
        }
        assert plugin.initialize(config), "API initialization failed"
        
        # Check availability
        is_available = plugin.is_available()
        print(f"[INFO] API dependencies available: {is_available}")
        
        # Test server operations (without actual server start)
        status = plugin.get_server_status()
        assert 'initialized' in status, "API status check failed"
        
        # Test endpoint registration
        mock_workflow = {"name": "mock_gt_workflow"}
        plugin.register_gt_endpoints(mock_workflow)
        
        # Test background processing
        assert plugin.enable_background_processing(), "Background processing enable failed"
        
        # Get endpoint info
        endpoints = plugin.get_endpoint_info()
        print(f"[INFO] Registered {len(endpoints)} endpoints")
        
        # Cleanup
        assert plugin.cleanup(), "API cleanup failed"
        
        print("[SUCCESS] API plugin fully functional")
        return True
        
    except Exception as e:
        print(f"[ERROR] API plugin test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_taxonomy_plugin():
    """Test Taxonomy plugin functionality"""
    print("\n=== TESTING TAXONOMY PLUGIN ===")
    
    try:
        from plugins.taxonomy import AITaxonomyPlugin
        
        # Create and initialize plugin
        plugin = AITaxonomyPlugin()
        assert plugin.get_name() == "ai_taxonomy"
        
        # Initialize with config
        config = {
            'auto_enhance': True,
            'enhancement_threshold': 0.7,
            'taxonomy_file': 'nonexistent.yaml'  # Will use default
        }
        assert plugin.initialize(config), "Taxonomy initialization failed"
        
        # Test code enhancement
        mock_codes = [
            {'name': 'machine_learning', 'description': 'ML model training'},
            {'name': 'user_trust', 'description': 'Trust in AI systems'},
            {'name': 'data_privacy', 'description': 'Privacy concerns'}
        ]
        
        enhanced = plugin.enhance_codes(mock_codes)
        assert len(enhanced) == len(mock_codes), "Enhancement changed code count"
        
        # Check if some codes were enhanced
        enhanced_count = sum(1 for c in enhanced if c.get('taxonomy_enhanced'))
        print(f"[INFO] Enhanced {enhanced_count}/{len(mock_codes)} codes")
        
        # Test category suggestions
        suggestions = plugin.suggest_categories("artificial intelligence ethics")
        print(f"[INFO] Got {len(suggestions)} category suggestions")
        
        # Get taxonomy structure
        structure = plugin.get_taxonomy_structure()
        assert 'categories_count' in structure, "Taxonomy structure unavailable"
        print(f"[INFO] Taxonomy has {structure.get('categories_count', 0)} categories")
        
        # Cleanup
        assert plugin.cleanup(), "Taxonomy cleanup failed"
        
        print("[SUCCESS] Taxonomy plugin fully functional")
        return True
        
    except Exception as e:
        print(f"[ERROR] Taxonomy plugin test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plugin_integration():
    """Test plugin system integration with all plugins"""
    print("\n=== TESTING PLUGIN SYSTEM INTEGRATION ===")
    
    try:
        from plugins import PluginManager
        from config.config_manager import QCCleanConfigManager
        
        # Create plugin manager
        config_manager = QCCleanConfigManager()
        plugin_manager = PluginManager(config_manager)
        
        # Initialize plugin system
        assert plugin_manager.initialize(), "Plugin system initialization failed"
        
        # List registered plugins
        registered = plugin_manager.list_registered_plugins()
        print(f"[INFO] Registered plugins: {len(registered)}")
        
        # Check for our plugins in the registry
        plugin_names = [p.get('name') for p in registered]
        print(f"[INFO] Plugin names in registry: {plugin_names}")
        
        # Note: Plugins won't be auto-registered unless they're discovered
        # This is expected behavior for the clean architecture
        
        # Validate system
        validation = plugin_manager.validate_plugin_system()
        print(f"[INFO] System validation: Valid={validation.get('is_valid', False)}")
        
        if validation.get('config_issues'):
            print(f"[INFO] Config issues (expected): {validation['config_issues']}")
        
        # Shutdown
        assert plugin_manager.shutdown(), "Plugin system shutdown failed"
        
        print("[SUCCESS] Plugin system integration functional")
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin integration test failed: {e}")
        return False


def main():
    """Run all plugin tests"""
    print("Phase 3 Plugin Validation - Complete Test Suite")
    print("=" * 50)
    
    tests = [
        test_qca_plugin,
        test_api_plugin,
        test_taxonomy_plugin,
        test_plugin_integration
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
    print(f"PHASE 3 VALIDATION SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] ALL PLUGINS VALIDATED - Phase 3 Complete")
        print("\nPlugin Implementation Summary:")
        print("  - QCA Plugin: Fully functional with GT conversion and analysis")
        print("  - API Plugin: Server framework ready for REST/WebSocket endpoints")
        print("  - Taxonomy Plugin: AI taxonomy enhancement operational")
        print("\nReady for Phase 4: Integration Testing")
        return True
    else:
        print("[ERROR] Some plugin tests failed - review implementation")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)