#!/usr/bin/env python3
"""
Test Plugin-Core Integration - Phase 4 Integration Testing

Tests that plugins can integrate properly with the core GT workflow system.
"""

import sys
import logging
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_plugin_manager_integration():
    """Test plugin manager with core system"""
    print("\n=== TESTING PLUGIN MANAGER INTEGRATION ===")
    
    try:
        from plugins import PluginManager
        from config.config_manager import QCCleanConfigManager
        
        # Initialize both systems
        config_manager = QCCleanConfigManager()
        plugin_manager = PluginManager(config_manager)
        
        # Test initialization
        assert plugin_manager.initialize(), "Plugin manager initialization failed"
        
        # Test configuration integration
        qc_config = config_manager.load_config()
        enabled_plugins = config_manager.get_enabled_plugins()
        
        print(f"[SUCCESS] Plugin manager integrated with config system")
        print(f"   Core config loaded: {qc_config.system.methodology}")
        print(f"   Enabled plugins: {enabled_plugins}")
        
        # Cleanup
        assert plugin_manager.shutdown(), "Plugin manager shutdown failed"
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Plugin manager integration failed: {e}")
        return False


def test_qca_plugin_with_mock_gt_data():
    """Test QCA plugin with mock GT workflow data"""
    print("\n=== TESTING QCA PLUGIN WITH GT DATA ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        from config.config_manager import QCCleanConfigManager
        
        # Initialize plugin
        config_manager = QCCleanConfigManager()
        qca_config = config_manager.get_plugin_config('qca_analysis')
        
        qca_plugin = QCAAnalysisPlugin()
        assert qca_plugin.initialize(qca_config), "QCA plugin initialization failed"
        
        # Mock GT workflow results (simulating real GT output)
        mock_gt_results = {
            'codes': [
                {
                    'name': 'ai_trust_issues',
                    'description': 'Trust concerns about AI systems',
                    'frequency': 5,
                    'level': 1,
                    'applications': [
                        {'interview_id': 'participant_01', 'source': 'participant_01'},
                        {'interview_id': 'participant_03', 'source': 'participant_03'}
                    ]
                },
                {
                    'name': 'transparency_needs',
                    'description': 'Need for AI system transparency',
                    'frequency': 4,
                    'level': 1,
                    'applications': [
                        {'interview_id': 'participant_02', 'source': 'participant_02'},
                        {'interview_id': 'participant_03', 'source': 'participant_03'}
                    ]
                },
                {
                    'name': 'successful_adoption',
                    'description': 'Successful AI adoption patterns',
                    'frequency': 3,
                    'level': 0,  # Core category
                    'applications': [
                        {'interview_id': 'participant_01', 'source': 'participant_01'}
                    ]
                }
            ],
            'interviews': [
                {'id': 'participant_01', 'name': 'Tech Manager Interview'},
                {'id': 'participant_02', 'name': 'Developer Interview'},
                {'id': 'participant_03', 'name': 'User Researcher Interview'}
            ],
            'hierarchy': {
                'core_categories': ['successful_adoption'],
                'subcategories': ['ai_trust_issues', 'transparency_needs']
            }
        }
        
        # Test integration workflow
        assert qca_plugin.can_process(mock_gt_results), "QCA cannot process GT results"
        
        qca_data = qca_plugin.convert_to_qca(mock_gt_results)
        assert 'case_matrix' in qca_data, "GT to QCA conversion failed"
        
        results = qca_plugin.run_qca_analysis(qca_data)
        assert 'truth_table' in results, "QCA analysis failed"
        
        print("[SUCCESS] QCA plugin integrated with GT workflow data")
        print(f"   Processed {len(mock_gt_results['codes'])} codes")
        print(f"   Analyzed {len(mock_gt_results['interviews'])} interviews")
        print(f"   Generated {len(results.get('truth_table', []))} truth table rows")
        
        # Cleanup
        assert qca_plugin.cleanup(), "QCA plugin cleanup failed"
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA-GT integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_taxonomy_plugin_with_gt_codes():
    """Test Taxonomy plugin with GT code data"""
    print("\n=== TESTING TAXONOMY PLUGIN WITH GT CODES ===")
    
    try:
        from plugins.taxonomy import AITaxonomyPlugin
        from config.config_manager import QCCleanConfigManager
        
        # Initialize plugin
        config_manager = QCCleanConfigManager()
        taxonomy_config = config_manager.get_plugin_config('ai_taxonomy')
        
        taxonomy_plugin = AITaxonomyPlugin()
        assert taxonomy_plugin.initialize(taxonomy_config), "Taxonomy plugin initialization failed"
        
        # Mock GT codes (simulating real GT output)
        mock_gt_codes = [
            {
                'name': 'machine_learning_adoption',
                'description': 'Adoption patterns for ML in organizations',
                'frequency': 8,
                'level': 1
            },
            {
                'name': 'ethical_ai_concerns',
                'description': 'Ethical considerations in AI implementation',
                'frequency': 6,
                'level': 1
            },
            {
                'name': 'human_ai_collaboration',
                'description': 'Patterns of human-AI collaborative work',
                'frequency': 5,
                'level': 1
            },
            {
                'name': 'data_privacy_issues',
                'description': 'Privacy concerns with AI systems',
                'frequency': 4,
                'level': 2
            }
        ]
        
        # Test enhancement workflow
        enhanced_codes = taxonomy_plugin.enhance_codes(mock_gt_codes)
        assert len(enhanced_codes) == len(mock_gt_codes), "Code count changed during enhancement"
        
        # Check enhancements
        enhanced_count = sum(1 for code in enhanced_codes if code.get('taxonomy_enhanced'))
        
        # Test individual suggestions
        suggestions = taxonomy_plugin.suggest_categories("artificial intelligence ethics and fairness")
        
        print("[SUCCESS] Taxonomy plugin integrated with GT codes")
        print(f"   Enhanced {enhanced_count}/{len(mock_gt_codes)} codes")
        print(f"   Generated {len(suggestions)} category suggestions")
        
        # Show some results
        for code in enhanced_codes:
            if code.get('taxonomy_enhanced'):
                categories = code.get('taxonomy_categories', [])
                print(f"   '{code['name']}' -> {len(categories)} categories")
        
        # Cleanup
        assert taxonomy_plugin.cleanup(), "Taxonomy plugin cleanup failed"
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Taxonomy-GT integration failed: {e}")
        return False


def test_api_plugin_with_gt_workflow():
    """Test API plugin integration with GT workflow"""
    print("\n=== TESTING API PLUGIN WITH GT WORKFLOW ===")
    
    try:
        from plugins.api import APIServerPlugin
        from config.config_manager import QCCleanConfigManager
        
        # Initialize plugin
        config_manager = QCCleanConfigManager()
        api_config = config_manager.get_plugin_config('api_server')
        
        api_plugin = APIServerPlugin()
        assert api_plugin.initialize(api_config), "API plugin initialization failed"
        
        # Mock GT workflow
        class MockGTWorkflow:
            def __init__(self):
                self.name = "GroundedTheoryWorkflow"
                self.status = "initialized"
            
            def analyze(self, interviews):
                return {"codes": [], "categories": [], "status": "completed"}
        
        mock_gt_workflow = MockGTWorkflow()
        
        # Test workflow registration
        api_plugin.register_gt_endpoints(mock_gt_workflow)
        
        # Test background processing
        assert api_plugin.enable_background_processing(), "Background processing enable failed"
        
        # Test server status
        status = api_plugin.get_server_status()
        assert status['initialized'], "API server not initialized"
        
        # Test endpoint registration
        endpoints = api_plugin.get_endpoint_info()
        gt_endpoints = [ep for ep in endpoints if 'gt' in ep.get('path', '')]
        
        print("[SUCCESS] API plugin integrated with GT workflow")
        print(f"   Registered {len(endpoints)} total endpoints")
        print(f"   GT-specific endpoints: {len(gt_endpoints)}")
        print(f"   Background processing: {status.get('background_processing', False)}")
        
        # Cleanup
        assert api_plugin.cleanup(), "API plugin cleanup failed"
        
        return True
        
    except Exception as e:
        print(f"[ERROR] API-GT integration failed: {e}")
        return False


def test_multi_plugin_workflow():
    """Test multiple plugins working together with GT data"""
    print("\n=== TESTING MULTI-PLUGIN WORKFLOW ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        from plugins.taxonomy import AITaxonomyPlugin
        from plugins.api import APIServerPlugin
        from config.config_manager import QCCleanConfigManager
        
        # Initialize all plugins
        config_manager = QCCleanConfigManager()
        
        qca_plugin = QCAAnalysisPlugin()
        taxonomy_plugin = AITaxonomyPlugin()
        api_plugin = APIServerPlugin()
        
        # Initialize plugins
        assert qca_plugin.initialize(config_manager.get_plugin_config('qca_analysis'))
        assert taxonomy_plugin.initialize(config_manager.get_plugin_config('ai_taxonomy'))
        assert api_plugin.initialize(config_manager.get_plugin_config('api_server'))
        
        print("[SUCCESS] All three plugins initialized")
        
        # Mock integrated workflow
        mock_gt_data = {
            'codes': [
                {'name': 'ai_ethics', 'description': 'AI ethical considerations', 'frequency': 3},
                {'name': 'user_trust', 'description': 'User trust in AI systems', 'frequency': 4},
                {'name': 'success_outcome', 'description': 'Successful AI implementation', 'frequency': 2}
            ],
            'interviews': [
                {'id': 'int1', 'name': 'Interview 1'},
                {'id': 'int2', 'name': 'Interview 2'},
                {'id': 'int3', 'name': 'Interview 3'}
            ],
            'hierarchy': {}
        }
        
        # Step 1: Enhance codes with taxonomy
        enhanced_codes = taxonomy_plugin.enhance_codes(mock_gt_data['codes'])
        enhanced_gt_data = mock_gt_data.copy()
        enhanced_gt_data['codes'] = enhanced_codes
        
        # Step 2: Convert to QCA analysis
        if qca_plugin.can_process(enhanced_gt_data):
            qca_data = qca_plugin.convert_to_qca(enhanced_gt_data)
            qca_results = qca_plugin.run_qca_analysis(qca_data)
        else:
            qca_results = {"message": "Insufficient data for QCA"}
        
        # Step 3: API plugin could serve these results
        class MockWorkflow:
            def get_results(self):
                return {
                    'enhanced_codes': enhanced_codes,
                    'qca_results': qca_results
                }
        
        api_plugin.register_gt_endpoints(MockWorkflow())
        
        print("[SUCCESS] Multi-plugin workflow completed")
        print(f"   Taxonomy enhanced {len(enhanced_codes)} codes")
        print(f"   QCA analysis: {'completed' if 'truth_table' in qca_results else 'skipped'}")
        print(f"   API endpoints ready for serving results")
        
        # Cleanup all plugins
        qca_plugin.cleanup()
        taxonomy_plugin.cleanup()
        api_plugin.cleanup()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Multi-plugin workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_consistency():
    """Test that all plugins use consistent configuration"""
    print("\n=== TESTING CONFIGURATION CONSISTENCY ===")
    
    try:
        from config.config_manager import QCCleanConfigManager
        
        config_manager = QCCleanConfigManager()
        config = config_manager.load_config()
        
        # Test core configuration
        assert config.system.methodology == "grounded_theory"
        assert config.llm.provider == "gemini"
        
        # Test plugin configurations
        enabled_plugins = config.plugins.enabled_plugins
        expected_plugins = ['qca_analysis', 'api_server', 'ai_taxonomy']
        
        for plugin_name in expected_plugins:
            assert plugin_name in enabled_plugins, f"Plugin {plugin_name} not enabled"
            plugin_config = config_manager.get_plugin_config(plugin_name)
            assert isinstance(plugin_config, dict), f"Invalid config for {plugin_name}"
        
        print("[SUCCESS] Configuration consistency verified")
        print(f"   Core methodology: {config.system.methodology}")
        print(f"   Enabled plugins: {len(enabled_plugins)}")
        print(f"   Plugin configs: All valid")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Configuration consistency test failed: {e}")
        return False


def main():
    """Run all plugin-core integration tests"""
    print("Phase 4: Plugin-Core Integration Testing")
    print("=" * 50)
    
    tests = [
        test_plugin_manager_integration,
        test_qca_plugin_with_mock_gt_data,
        test_taxonomy_plugin_with_gt_codes,
        test_api_plugin_with_gt_workflow,
        test_multi_plugin_workflow,
        test_configuration_consistency
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
    print(f"PLUGIN-CORE INTEGRATION: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] Plugin-Core integration fully functional")
        print("\nIntegration Status:")
        print("  - Plugin manager integrates with core config")
        print("  - QCA plugin processes GT workflow data")
        print("  - Taxonomy plugin enhances GT codes")
        print("  - API plugin can serve GT results")
        print("  - Multi-plugin workflows operational")
        print("  - Configuration system consistent")
        return True
    else:
        print("[ERROR] Some integration tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)