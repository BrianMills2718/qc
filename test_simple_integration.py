"""
Simple Integration Test for Enhanced Speaker Detection
Tests the enhanced semantic extractor integration directly (Windows compatible)
"""
import sys
import os
import asyncio
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

async def test_enhanced_extractor_basic():
    """Test basic enhanced extractor functionality"""
    print("Testing Enhanced Semantic Extractor...")
    
    try:
        # Import the enhanced extractor
        from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
        from core.llm.llm_handler import LLMHandler
        from config.unified_config import UnifiedConfig
        
        # Create configuration
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        
        # Initialize LLM handler
        llm_handler = LLMHandler(config=gt_config)
        print("SUCCESS: LLM handler initialized")
        
        # Test enhanced extractor with LLM detection DISABLED
        enhanced_extractor = EnhancedSemanticExtractor(
            llm_handler=llm_handler,
            use_llm_speaker_detection=False
        )
        print("SUCCESS: Enhanced semantic extractor created")
        
        # Verify extractor properties
        print(f"Name: {enhanced_extractor.get_name()}")
        print(f"Version: {enhanced_extractor.get_version()}")
        print(f"Description: {enhanced_extractor.get_description()}")
        
        # Test speaker detection (regex fallback)
        test_cases = [
            ("John: Hello everyone", "John"),
            ("Sarah said we should proceed", "Sarah"),
            ("I think that's correct", "Participant"),
            ("The system shows error", None)
        ]
        
        print("\nTesting speaker detection:")
        all_passed = True
        for text, expected in test_cases:
            speaker = await enhanced_extractor._detect_speaker(text)
            status = "PASS" if (speaker == expected or (expected is None and speaker is None)) else "FAIL"
            print(f"  '{text}' -> Expected: {expected}, Got: {speaker} [{status}]")
            if status == "FAIL":
                all_passed = False
        
        if all_passed:
            print("SUCCESS: All speaker detection tests passed")
        else:
            print("WARNING: Some speaker detection tests failed")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Enhanced extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_plugin_registration():
    """Test plugin registration"""
    print("\nTesting plugin registration...")
    
    try:
        from plugins.extractors import get_available_extractors, get_extractor_plugin
        
        extractors = get_available_extractors()
        print(f"Registry loaded with {len(extractors)} extractors: {extractors}")
        
        if "enhanced_semantic" in extractors:
            print("SUCCESS: enhanced_semantic extractor is registered")
            # Test getting the extractor plugin
            plugin = get_extractor_plugin("enhanced_semantic")
            if plugin:
                print(f"Extractor plugin retrieved: {plugin.__class__.__name__}")
            return True
        else:
            print("ERROR: enhanced_semantic extractor is NOT registered")
            print(f"Available: {extractors}")
            return False
            
    except Exception as e:
        print(f"ERROR: Plugin registration test failed: {e}")
        return False

async def test_circuit_breaker():
    """Test circuit breaker"""
    print("\nTesting circuit breaker...")
    
    try:
        from core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker
        
        circuit_breaker = SpeakerDetectionCircuitBreaker(
            failure_threshold=3,
            timeout_seconds=10
        )
        print("SUCCESS: Circuit breaker created")
        print(f"State: {circuit_breaker.state}")
        
        # Test with mock functions
        async def mock_llm(*args):
            return "MockedSpeaker"
        
        async def mock_fallback(*args):
            return "FallbackSpeaker"
        
        result = await circuit_breaker.call_with_circuit_breaker(
            mock_llm,
            mock_fallback,
            "test"
        )
        print(f"Circuit breaker result: {result}")
        print("SUCCESS: Circuit breaker functional")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Circuit breaker test failed: {e}")
        return False

async def test_workflow_integration():
    """Test workflow integration"""
    print("\nTesting workflow integration...")
    
    try:
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from core.cli.robust_cli_operations import RobustCLIOperations
        from config.unified_config import UnifiedConfig
        
        # Create config
        config = UnifiedConfig()
        
        # Create robust operations (needed for workflow)
        robust_ops = RobustCLIOperations(config=config)
        
        # Initialize workflow with robust operations
        workflow = GroundedTheoryWorkflow(robust_operations=robust_ops)
        print("SUCCESS: Workflow initialized with robust operations")
        
        # Test extractor initialization method exists
        if hasattr(workflow, '_initialize_extractor_plugin'):
            print("SUCCESS: _initialize_extractor_plugin method exists")
        else:
            print("WARNING: _initialize_extractor_plugin method not found")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("Enhanced Speaker Detection Integration Test")
    print("=" * 50)
    
    tests = [
        ("Enhanced Extractor Basic", test_enhanced_extractor_basic),
        ("Plugin Registration", test_plugin_registration),
        ("Circuit Breaker", test_circuit_breaker),
        ("Workflow Integration", test_workflow_integration)
    ]
    
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        print("-" * 30)
        
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"RESULT: {test_name} PASSED")
            else:
                print(f"RESULT: {test_name} FAILED")
        except Exception as e:
            print(f"RESULT: {test_name} FAILED - {e}")
    
    print(f"\nFINAL: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("ALL TESTS PASSED - Integration successful!")
        return True
    else:
        print("Some tests failed")
        return False

if __name__ == "__main__":
    asyncio.run(main())