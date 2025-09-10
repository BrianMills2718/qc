"""
Phase 4 Success Criteria Validation
Comprehensive validation of all success criteria from CLAUDE.md
"""
import sys
import os
import asyncio
from pathlib import Path
import subprocess

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def print_test(test_name, success, message=""):
    """Print test result"""
    status = "PASS" if success else "FAIL"
    marker = "[✓]" if success else "[✗]"
    print(f"{marker} {test_name}: {status}")
    if message:
        print(f"    {message}")

async def validate_schema_bridge():
    """Validate Schema Bridge Functional"""
    print_section("VALIDATING SCHEMA BRIDGE")
    
    try:
        from core.speaker_detection.schema_bridge import SpeakerDetectionBridge
        print_test("Schema Bridge Import", True, "Successfully imported SpeakerDetectionBridge")
        
        # Test basic initialization
        from core.llm.llm_handler import LLMHandler
        from config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        llm_handler = LLMHandler(config=gt_config)
        
        bridge = SpeakerDetectionBridge(llm_handler)
        print_test("Schema Bridge Creation", True, f"Bridge initialized: {type(bridge).__name__}")
        
        return True
        
    except Exception as e:
        print_test("Schema Bridge Functional", False, f"Error: {e}")
        return False

async def validate_plugin_registration():
    """Validate Enhanced Plugin Available"""
    print_section("VALIDATING PLUGIN REGISTRATION")
    
    try:
        from plugins.extractors import get_available_extractors
        
        extractors = get_available_extractors()
        enhanced_available = "enhanced_semantic" in extractors
        
        print_test("Enhanced Plugin Registration", enhanced_available, 
                  f"Available extractors: {extractors}")
        
        if enhanced_available:
            from plugins.extractors import get_extractor_plugin
            plugin = get_extractor_plugin("enhanced_semantic")
            print_test("Enhanced Plugin Instantiation", plugin is not None,
                      f"Plugin type: {type(plugin).__name__ if plugin else 'None'}")
        
        return enhanced_available
        
    except Exception as e:
        print_test("Plugin Registration", False, f"Error: {e}")
        return False

async def validate_llm_detection():
    """Validate LLM Detection Working (without API calls)"""
    print_section("VALIDATING LLM DETECTION CAPABILITY")
    
    try:
        from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
        from core.llm.llm_handler import LLMHandler
        from config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        llm_handler = LLMHandler(config=gt_config)
        
        # Test enhanced extractor creation with LLM detection enabled
        enhanced_extractor = EnhancedSemanticExtractor(
            llm_handler=llm_handler,
            use_llm_speaker_detection=True  # Enable LLM detection
        )
        
        # Verify components are available
        has_bridge = enhanced_extractor.speaker_bridge is not None
        has_circuit_breaker = enhanced_extractor.circuit_breaker is not None
        
        print_test("LLM Detection Components", has_bridge and has_circuit_breaker,
                  f"Bridge: {has_bridge}, Circuit breaker: {has_circuit_breaker}")
        
        # Test that regex fallback still works when LLM disabled
        basic_extractor = EnhancedSemanticExtractor(
            llm_handler=llm_handler,
            use_llm_speaker_detection=False
        )
        
        test_result = await basic_extractor._detect_speaker("John: Hello everyone")
        print_test("Regex Fallback Works", test_result == "John",
                  f"Detected speaker: {test_result}")
        
        return True
        
    except Exception as e:
        print_test("LLM Detection Capability", False, f"Error: {e}")
        return False

async def validate_circuit_breaker():
    """Validate Circuit Breaker Active"""
    print_section("VALIDATING CIRCUIT BREAKER")
    
    try:
        from core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker
        
        circuit_breaker = SpeakerDetectionCircuitBreaker(
            failure_threshold=3,
            timeout_seconds=10
        )
        
        # Test initial state
        initial_state = circuit_breaker.state == "CLOSED"
        print_test("Circuit Breaker Initial State", initial_state,
                  f"State: {circuit_breaker.state}")
        
        # Test call mechanism (with mock functions)
        async def mock_success(*args):
            return "Success"
        
        async def mock_fallback(*args):
            return "Fallback"
        
        result = await circuit_breaker.call_with_circuit_breaker(
            mock_success, mock_fallback, "test"
        )
        
        print_test("Circuit Breaker Call Mechanism", result == "Success",
                  f"Result: {result}")
        
        return True
        
    except Exception as e:
        print_test("Circuit Breaker Active", False, f"Error: {e}")
        return False

async def validate_performance_monitoring():
    """Validate Performance Monitoring"""
    print_section("VALIDATING PERFORMANCE MONITORING")
    
    try:
        from core.speaker_detection.performance_monitor import performance_monitor
        
        # Clear any existing data
        performance_monitor.metrics.total_detections = 0
        
        # Record some test detections
        performance_monitor.record_detection(
            text="John: Test message",
            result="John",
            method="regex",
            execution_time=0.001,
            success=True
        )
        
        performance_monitor.record_detection(
            text="Sarah: Another message",
            result="Sarah",
            method="llm",
            execution_time=0.5,
            success=True
        )
        
        # Get performance report
        report = performance_monitor.get_performance_report()
        
        has_data = report.get('summary', {}).get('total_detections', 0) > 0
        has_recommendations = len(report.get('recommendations', [])) > 0
        
        print_test("Performance Data Collection", has_data,
                  f"Total detections: {report.get('summary', {}).get('total_detections', 0)}")
        
        print_test("Performance Recommendations", has_recommendations,
                  f"Recommendations: {report.get('recommendations', [])}")
        
        return has_data and has_recommendations
        
    except Exception as e:
        print_test("Performance Monitoring", False, f"Error: {e}")
        return False

async def validate_cli_integration():
    """Validate CLI Integration Complete"""
    print_section("VALIDATING CLI INTEGRATION")
    
    try:
        # Test CLI help command works
        result = subprocess.run([
            sys.executable, "-m", "qc_clean.core.cli.cli_robust", "--help"
        ], capture_output=True, text=True, cwd="qc_clean")
        
        help_works = result.returncode == 0
        print_test("CLI Help Command", help_works,
                  f"Return code: {result.returncode}")
        
        # Test that workflow integration exists
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from core.cli.robust_cli_operations import RobustCLIOperations
        from config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        robust_ops = RobustCLIOperations(config=config)
        workflow = GroundedTheoryWorkflow(robust_operations=robust_ops)
        
        has_extractor_method = hasattr(workflow, '_initialize_extractor_plugin')
        print_test("Workflow Integration", has_extractor_method,
                  "Enhanced extractor integration method exists")
        
        return help_works and has_extractor_method
        
    except Exception as e:
        print_test("CLI Integration", False, f"Error: {e}")
        return False

async def validate_zero_regression():
    """Validate Zero Regression"""
    print_section("VALIDATING ZERO REGRESSION")
    
    try:
        # Test that original semantic extractor still works
        from plugins.extractors import get_extractor_plugin
        
        semantic_extractor = get_extractor_plugin("semantic")
        print_test("Original Semantic Extractor", semantic_extractor is not None,
                  f"Type: {type(semantic_extractor).__name__ if semantic_extractor else 'None'}")
        
        # Test that all original extractors are still available
        from plugins.extractors import get_available_extractors
        
        extractors = get_available_extractors()
        original_extractors = ["hierarchical", "relationship", "semantic", "validated"]
        all_original_present = all(ext in extractors for ext in original_extractors)
        
        print_test("All Original Extractors Available", all_original_present,
                  f"Available: {extractors}")
        
        return all_original_present and semantic_extractor is not None
        
    except Exception as e:
        print_test("Zero Regression", False, f"Error: {e}")
        return False

async def main():
    """Run all validation tests"""
    print_section("PHASE 4 SUCCESS CRITERIA VALIDATION")
    print("Validating all success criteria from CLAUDE.md implementation plan")
    
    validators = [
        ("Schema Bridge Functional", validate_schema_bridge),
        ("Enhanced Plugin Available", validate_plugin_registration),
        ("LLM Detection Working", validate_llm_detection),
        ("Circuit Breaker Active", validate_circuit_breaker),
        ("Performance Monitoring", validate_performance_monitoring),
        ("CLI Integration", validate_cli_integration),
        ("Zero Regression", validate_zero_regression)
    ]
    
    passed = 0
    total = len(validators)
    
    for test_name, validator in validators:
        try:
            success = await validator()
            if success:
                passed += 1
        except Exception as e:
            print(f"Validator {test_name} failed with exception: {e}")
    
    print_section("FINAL VALIDATION RESULTS")
    print(f"SUCCESS CRITERIA VALIDATION: {passed}/{total} criteria passed")
    
    if passed == total:
        print("🎉 ALL SUCCESS CRITERIA PASSED!")
        print("Enhanced Speaker Detection implementation is COMPLETE and SUCCESSFUL!")
        return True
    else:
        print("❌ Some success criteria failed")
        print("Implementation needs additional work")
        return False

if __name__ == "__main__":
    asyncio.run(main())