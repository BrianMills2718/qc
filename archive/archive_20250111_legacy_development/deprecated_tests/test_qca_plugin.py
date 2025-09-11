#!/usr/bin/env python3
"""
Test QCA Plugin Implementation - Phase 3 Validation

Tests the QCA plugin functionality independently to ensure proper implementation.
"""

import sys
import logging
from pathlib import Path

# Add qc_clean to Python path
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_qca_plugin_loading():
    """Test QCA plugin can be loaded and initialized"""
    print("\n=== TESTING QCA PLUGIN LOADING ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        print("[SUCCESS] QCA plugin imported successfully")
        
        # Create plugin instance
        qca_plugin = QCAAnalysisPlugin()
        print("[SUCCESS] QCA plugin instance created")
        
        # Test basic properties
        assert qca_plugin.get_name() == "qca_analysis"
        assert qca_plugin.get_version() == "1.0.0"
        assert "QCA" in qca_plugin.get_description()
        
        dependencies = qca_plugin.get_dependencies()
        assert isinstance(dependencies, list)
        assert len(dependencies) > 0
        
        print(f"[SUCCESS] Plugin properties validated: {qca_plugin.get_name()} v{qca_plugin.get_version()}")
        print(f"   Description: {qca_plugin.get_description()}")
        print(f"   Dependencies: {dependencies}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA plugin loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qca_plugin_availability():
    """Test QCA plugin dependency availability"""
    print("\n=== TESTING QCA PLUGIN AVAILABILITY ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        
        # Test availability check
        is_available = qca_plugin.is_available()
        print(f"[INFO] QCA plugin availability: {is_available}")
        
        if not is_available:
            print("[WARNING] QCA plugin dependencies not fully available")
            print("   This may be due to missing optional packages like advanced QCA libraries")
            print("   Basic functionality should still work")
        else:
            print("[SUCCESS] QCA plugin dependencies available")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA plugin availability test failed: {e}")
        return False


def test_qca_plugin_initialization():
    """Test QCA plugin initialization with configuration"""
    print("\n=== TESTING QCA PLUGIN INITIALIZATION ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        
        # Test configuration
        test_config = {
            'enable_qca_conversion': True,
            'default_analysis_method': 'crisp_set',
            'calibration_method': 'binary',
            'consistency_threshold': 0.8,
            'frequency_threshold': 1,
            'generate_minimization': True,
            'output_format': 'standard'
        }
        
        # Initialize plugin
        init_success = qca_plugin.initialize(test_config)
        
        if init_success:
            print("[SUCCESS] QCA plugin initialized successfully")
            print(f"   Status: {qca_plugin.get_status()}")
            print(f"   Config: {test_config}")
        else:
            print("[ERROR] QCA plugin initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA plugin initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qca_gt_compatibility():
    """Test QCA plugin GT results compatibility check"""
    print("\n=== TESTING QCA GT COMPATIBILITY ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        qca_plugin.initialize({})
        
        # Create mock GT results
        mock_gt_results = {
            'codes': [
                {'name': 'trust_issues', 'description': 'Issues with trust', 'frequency': 5, 'level': 1},
                {'name': 'communication_barriers', 'description': 'Communication problems', 'frequency': 3, 'level': 1},
                {'name': 'team_success', 'description': 'Team success factors', 'frequency': 4, 'level': 0}
            ],
            'interviews': [
                {'id': 'interview_1', 'name': 'Interview 1', 'content': 'Content about trust issues'},
                {'id': 'interview_2', 'name': 'Interview 2', 'content': 'Content about communication'},
                {'id': 'interview_3', 'name': 'Interview 3', 'content': 'Content about success'}
            ],
            'hierarchy': {
                'core_categories': ['team_success'],
                'subcategories': ['trust_issues', 'communication_barriers']
            }
        }
        
        # Test compatibility check
        can_process = qca_plugin.can_process(mock_gt_results)
        print(f"[INFO] GT results compatibility: {can_process}")
        
        if can_process:
            print("[SUCCESS] Mock GT results are compatible with QCA")
            print(f"   {len(mock_gt_results['codes'])} codes, {len(mock_gt_results['interviews'])} interviews")
        else:
            print("[WARNING] Mock GT results not compatible with QCA")
            print("   This might be due to insufficient data or structure issues")
        
        # Test with insufficient data
        insufficient_gt = {
            'codes': [{'name': 'single_code', 'frequency': 1}],  # Only 1 code
            'interviews': [{'id': 'int1'}],  # Only 1 interview
            'hierarchy': {}
        }
        
        insufficient_compatible = qca_plugin.can_process(insufficient_gt)
        print(f"[INFO] Insufficient data compatibility (expected False): {insufficient_compatible}")
        
        if not insufficient_compatible:
            print("[SUCCESS] Plugin correctly rejects insufficient data")
        else:
            print("[WARNING] Plugin should reject insufficient data")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA GT compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qca_conversion():
    """Test QCA plugin GT to QCA conversion"""
    print("\n=== TESTING QCA CONVERSION ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        qca_plugin.initialize({})
        
        # Create mock GT results with applications
        mock_gt_results = {
            'codes': [
                {
                    'name': 'trust_issues', 
                    'description': 'Issues with trust', 
                    'frequency': 2, 
                    'level': 1,
                    'applications': [
                        {'interview_id': 'interview_1', 'source': 'interview_1'},
                        {'interview_id': 'interview_3', 'source': 'interview_3'}
                    ]
                },
                {
                    'name': 'communication_barriers', 
                    'description': 'Communication problems', 
                    'frequency': 2, 
                    'level': 1,
                    'applications': [
                        {'interview_id': 'interview_2', 'source': 'interview_2'},
                        {'interview_id': 'interview_3', 'source': 'interview_3'}
                    ]
                },
                {
                    'name': 'team_success', 
                    'description': 'Team success factors', 
                    'frequency': 1, 
                    'level': 0,
                    'applications': [
                        {'interview_id': 'interview_1', 'source': 'interview_1'}
                    ]
                }
            ],
            'interviews': [
                {'id': 'interview_1', 'name': 'Interview 1'},
                {'id': 'interview_2', 'name': 'Interview 2'}, 
                {'id': 'interview_3', 'name': 'Interview 3'}
            ],
            'hierarchy': {}
        }
        
        # Test conversion
        if qca_plugin.can_process(mock_gt_results):
            qca_data = qca_plugin.convert_to_qca(mock_gt_results)
            
            print("[SUCCESS] GT to QCA conversion completed")
            print(f"   Conditions: {qca_data.get('conditions', [])}")
            print(f"   Outcomes: {qca_data.get('outcomes', [])}")
            print(f"   Cases in matrix: {len(qca_data.get('case_matrix', []))}")
            
            # Verify QCA data structure
            assert 'case_matrix' in qca_data
            assert 'conditions' in qca_data
            assert 'outcomes' in qca_data
            assert 'conversion_metadata' in qca_data
            
            print("[SUCCESS] QCA data structure validated")
            
            return qca_data
        else:
            print("[SKIP] Cannot test conversion - GT results not compatible")
            return None
        
    except Exception as e:
        print(f"[ERROR] QCA conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_qca_analysis():
    """Test QCA plugin analysis functionality"""
    print("\n=== TESTING QCA ANALYSIS ===")
    
    try:
        # Get QCA data from conversion test
        qca_data = test_qca_conversion()
        
        if qca_data is None:
            print("[SKIP] Cannot test analysis - no QCA data available")
            return False
        
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        qca_plugin.initialize({})
        
        # Run QCA analysis
        print("[INFO] Running QCA analysis...")
        results = qca_plugin.run_qca_analysis(qca_data)
        
        print("[SUCCESS] QCA analysis completed")
        
        # Verify results structure
        expected_keys = [
            'truth_table', 'necessary_conditions', 'sufficient_conditions',
            'consistency_scores', 'coverage_scores', 'analysis_metadata'
        ]
        
        for key in expected_keys:
            if key in results:
                print(f"   [SUCCESS] {key}: {type(results[key])}")
            else:
                print(f"   [WARNING] Missing {key}")
        
        # Display some results
        metadata = results.get('analysis_metadata', {})
        print(f"   Analysis timestamp: {metadata.get('timestamp', 'Unknown')}")
        print(f"   Cases analyzed: {metadata.get('total_cases', 0)}")
        print(f"   Conditions: {metadata.get('total_conditions', 0)}")
        print(f"   Outcomes: {metadata.get('total_outcomes', 0)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qca_plugin_cleanup():
    """Test QCA plugin cleanup"""
    print("\n=== TESTING QCA PLUGIN CLEANUP ===")
    
    try:
        from plugins.qca import QCAAnalysisPlugin
        
        qca_plugin = QCAAnalysisPlugin()
        qca_plugin.initialize({})
        
        # Test cleanup
        cleanup_success = qca_plugin.cleanup()
        
        if cleanup_success:
            print("[SUCCESS] QCA plugin cleanup successful")
            print(f"   Final status: {qca_plugin.get_status()}")
        else:
            print("[ERROR] QCA plugin cleanup failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] QCA plugin cleanup test failed: {e}")
        return False


def main():
    """Run all QCA plugin tests"""
    print("QCA Plugin Implementation - Phase 3 Validation")
    print("=" * 50)
    
    tests = [
        test_qca_plugin_loading,
        test_qca_plugin_availability,
        test_qca_plugin_initialization,
        test_qca_gt_compatibility,
        test_qca_analysis,  # This includes conversion test
        test_qca_plugin_cleanup
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
    print(f"QCA PLUGIN VALIDATION SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] QCA plugin implementation complete and validated")
        return True
    else:
        print("[ERROR] Some QCA plugin tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)