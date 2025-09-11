#!/usr/bin/env python3
"""
Test QC Clean Plugin System - Phase 2 Validation

This script tests the plugin system functionality without requiring actual plugins.
Tests plugin interfaces, registry, discovery, and manager components.
"""

import sys
import logging
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_plugin_interfaces():
    """Test plugin interface definitions"""
    print("\n=== TESTING PLUGIN INTERFACES ===")
    
    try:
        from plugins.base import QCPlugin, QCAPlugin, APIPlugin, TaxonomyPlugin, PluginStatus
        print("[SUCCESS] Successfully imported plugin interfaces")
        
        # Test base plugin interface
        assert hasattr(QCPlugin, 'get_name'), "QCPlugin missing get_name method"
        assert hasattr(QCPlugin, 'initialize'), "QCPlugin missing initialize method"
        assert hasattr(QCPlugin, 'is_available'), "QCPlugin missing is_available method"
        print("[SUCCESS] QCPlugin interface validation passed")
        
        # Test specialized interfaces
        assert hasattr(QCAPlugin, 'can_process'), "QCAPlugin missing can_process method"
        assert hasattr(QCAPlugin, 'convert_to_qca'), "QCAPlugin missing convert_to_qca method"
        print("[SUCCESS] QCAPlugin interface validation passed")
        
        assert hasattr(APIPlugin, 'start_server'), "APIPlugin missing start_server method"
        assert hasattr(APIPlugin, 'register_gt_endpoints'), "APIPlugin missing register_gt_endpoints method"
        print("[SUCCESS] APIPlugin interface validation passed")
        
        assert hasattr(TaxonomyPlugin, 'load_taxonomy'), "TaxonomyPlugin missing load_taxonomy method"
        assert hasattr(TaxonomyPlugin, 'enhance_codes'), "TaxonomyPlugin missing enhance_codes method"
        print("[SUCCESS] TaxonomyPlugin interface validation passed")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin interface test failed: {e}")
        return False


def test_plugin_registry():
    """Test plugin registry functionality"""
    print("\n=== TESTING PLUGIN REGISTRY ===")
    
    try:
        from plugins.registry import PluginRegistry, PluginDependencyError
        from plugins.base import QCPlugin, PluginStatus
        
        # Create test plugin class
        class TestPlugin(QCPlugin):
            def get_name(self) -> str:
                return "test_plugin"
            
            def get_version(self) -> str:
                return "1.0.0"
            
            def get_description(self) -> str:
                return "Test plugin for validation"
            
            def get_dependencies(self):
                return []
            
            def initialize(self, config):
                return True
            
            def is_available(self) -> bool:
                return True
        
        # Test registry operations
        registry = PluginRegistry()
        print("[SUCCESS] Created plugin registry")
        
        # Test registration
        success = registry.register_plugin(TestPlugin)
        assert success, "Failed to register test plugin"
        print("[SUCCESS] Plugin registration successful")
        
        # Test listing
        registered = registry.get_registered_plugins()
        assert "test_plugin" in registered, "Test plugin not in registered list"
        print("[SUCCESS] Plugin listing successful")
        
        # Test plugin info
        plugin_info = registry.get_plugin_info("test_plugin")
        assert plugin_info is not None, "Failed to get plugin info"
        assert plugin_info['name'] == "test_plugin", "Plugin info incorrect"
        print("[SUCCESS] Plugin info retrieval successful")
        
        # Test activation (should work since is_available returns True)
        activation_success = registry.activate_plugin("test_plugin")
        assert activation_success, "Failed to activate test plugin"
        print("[SUCCESS] Plugin activation successful")
        
        # Test active plugin retrieval
        active_plugins = registry.get_active_plugins()
        assert "test_plugin" in active_plugins, "Test plugin not in active list"
        print("[SUCCESS] Active plugin listing successful")
        
        # Test deactivation
        deactivation_success = registry.deactivate_plugin("test_plugin")
        assert deactivation_success, "Failed to deactivate test plugin"
        print("[SUCCESS] Plugin deactivation successful")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plugin_discovery():
    """Test plugin discovery system"""
    print("\n=== TESTING PLUGIN DISCOVERY ===")
    
    try:
        from plugins.registry import PluginRegistry, PluginDiscovery
        
        registry = PluginRegistry()
        discovery = PluginDiscovery(registry)
        print("[SUCCESS] Created plugin discovery system")
        
        # Test discovery in non-existent directory (should handle gracefully)
        plugins = discovery.discover_plugins_in_directory("nonexistent_directory")
        assert isinstance(plugins, list), "Discovery should return list even for missing directory"
        print("[SUCCESS] Graceful handling of missing directory")
        
        # Test discovery in empty directory
        plugin_dir = Path("qc_clean/plugins")
        if plugin_dir.exists():
            # Should not find any actual plugin implementations (just base files)
            plugins = discovery.discover_plugins_in_directory(str(plugin_dir))
            print(f"[SUCCESS] Discovery system functional (found {len(plugins)} plugins in base directory)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin discovery test failed: {e}")
        return False


def test_configuration_system():
    """Test configuration system integration"""
    print("\n=== TESTING CONFIGURATION SYSTEM ===")
    
    try:
        from config.config_manager import QCCleanConfigManager, QCCleanConfig
        
        # Test config manager creation
        config_manager = QCCleanConfigManager()
        print("[SUCCESS] Created configuration manager")
        
        # Test configuration loading
        config = config_manager.load_config()
        assert isinstance(config, QCCleanConfig), "Failed to load configuration"
        print("[SUCCESS] Configuration loading successful")
        
        # Test plugin-specific config access
        enabled_plugins = config_manager.get_enabled_plugins()
        assert isinstance(enabled_plugins, list), "Failed to get enabled plugins list"
        print(f"[SUCCESS] Enabled plugins: {enabled_plugins}")
        
        # Test plugin configuration access
        if enabled_plugins:
            first_plugin = enabled_plugins[0]
            plugin_config = config_manager.get_plugin_config(first_plugin)
            assert isinstance(plugin_config, dict), "Failed to get plugin configuration"
            print(f"[SUCCESS] Plugin configuration access successful for '{first_plugin}'")
        
        # Test plugin checks
        auto_discover = config_manager.should_auto_discover_plugins()
        auto_activate = config_manager.should_auto_activate_plugins()
        plugin_dir = config_manager.get_plugin_directory()
        
        print(f"[SUCCESS] Configuration values: auto_discover={auto_discover}, auto_activate={auto_activate}, plugin_dir={plugin_dir}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plugin_manager():
    """Test plugin manager integration"""
    print("\n=== TESTING PLUGIN MANAGER ===")
    
    try:
        from plugins.plugin_manager import PluginManager
        from config.config_manager import QCCleanConfigManager
        
        # Test manager creation
        config_manager = QCCleanConfigManager()
        plugin_manager = PluginManager(config_manager)
        print("[SUCCESS] Created plugin manager")
        
        # Test initialization
        init_success = plugin_manager.initialize()
        assert init_success, "Plugin manager initialization failed"
        print("[SUCCESS] Plugin manager initialization successful")
        
        # Test plugin listing (should be empty or contain discovered plugins)
        registered_plugins = plugin_manager.list_registered_plugins()
        active_plugins = plugin_manager.list_active_plugins()
        
        print(f"[SUCCESS] Plugin status: {len(registered_plugins)} registered, {len(active_plugins)} active")
        
        # Test validation
        validation = plugin_manager.validate_plugin_system()
        assert isinstance(validation, dict), "Validation should return dictionary"
        assert 'system_initialized' in validation, "Validation missing system_initialized"
        assert validation['system_initialized'] == True, "System should be initialized"
        
        print(f"[SUCCESS] System validation: {validation['is_valid']} (issues: {len(validation['config_issues']) + len(validation['plugin_issues'])})")
        
        # Test shutdown
        shutdown_success = plugin_manager.shutdown()
        assert shutdown_success, "Plugin manager shutdown failed"
        print("[SUCCESS] Plugin manager shutdown successful")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plugin_system_integration():
    """Test complete plugin system integration"""
    print("\n=== TESTING PLUGIN SYSTEM INTEGRATION ===")
    
    try:
        from plugins import PluginManager
        
        # Test context manager usage
        with PluginManager() as plugin_manager:
            print("[SUCCESS] Plugin manager context manager working")
            
            # Test system validation
            validation = plugin_manager.validate_plugin_system()
            
            if validation['is_valid']:
                print("[SUCCESS] Plugin system fully validated")
            else:
                print("[WARNING] Plugin system has minor issues but is functional:")
                for issue in validation['config_issues']:
                    print(f"   Config: {issue}")
                for issue in validation['plugin_issues']:
                    print(f"   Plugin: {issue}")
        
        print("[SUCCESS] Plugin system integration test completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin system integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all plugin system tests"""
    print("QC Clean Plugin System - Phase 2 Validation")
    print("=" * 50)
    
    tests = [
        test_plugin_interfaces,
        test_plugin_registry,
        test_plugin_discovery,
        test_configuration_system,
        test_plugin_manager,
        test_plugin_system_integration
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
    print(f"PHASE 2 VALIDATION SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED - Plugin system ready for Phase 3")
        return True
    else:
        print("[ERROR] Some tests failed - Plugin system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)