"""
Test Enhanced Extractor Integration Without Neo4j
Tests the enhanced semantic extractor integration directly
"""
import sys
import os
import asyncio
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

async def test_enhanced_extractor_direct():
    """Test enhanced extractor directly without full CLI stack"""
    print("Testing Enhanced Semantic Extractor Integration...")
    
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
        print("✅ LLM handler initialized successfully")
        
        # Test enhanced extractor with LLM detection DISABLED (to avoid API calls)
        enhanced_extractor = EnhancedSemanticExtractor(
            llm_handler=llm_handler,
            use_llm_speaker_detection=False  # Disable for testing
        )
        print("✅ Enhanced semantic extractor created successfully")
        
        # Verify extractor properties
        print(f"✅ Extractor name: {enhanced_extractor.get_name()}")
        print(f"✅ Extractor version: {enhanced_extractor.get_version()}")
        print(f"✅ Extractor description: {enhanced_extractor.get_description()}")
        
        # Test speaker detection (regex fallback)
        test_texts = [
            "John: Hello everyone",
            "Sarah said we should proceed",
            "I think that's correct",
            "The system shows error"
        ]
        
        print("\nTesting speaker detection (regex mode):")
        for text in test_texts:
            speaker = await enhanced_extractor._detect_speaker(text)
            print(f"  '{text}' → Speaker: {speaker}")
        
        print("✅ Enhanced extractor integration test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced extractor integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_plugin_registration():
    """Test that enhanced extractor is properly registered"""
    print("\nTesting plugin registration...")
    
    try:
        from plugins.extractors import get_extractor_registry
        
        # Get registry
        registry = get_extractor_registry()
        print(f"✅ Registry loaded with {len(registry)} extractors")
        
        # Check if enhanced_semantic is registered
        if "enhanced_semantic" in registry:
            print("✅ enhanced_semantic extractor is registered")
            
            # Get the extractor class
            extractor_class = registry["enhanced_semantic"]
            print(f"✅ Extractor class: {extractor_class.__name__}")
            
            return True
        else:
            print("❌ enhanced_semantic extractor is NOT registered")
            print(f"Available extractors: {list(registry.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Plugin registration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_circuit_breaker_integration():
    """Test circuit breaker functionality"""
    print("\nTesting circuit breaker integration...")
    
    try:
        from core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker
        
        # Create circuit breaker
        circuit_breaker = SpeakerDetectionCircuitBreaker(
            failure_threshold=3,
            timeout_seconds=10
        )
        print("✅ Circuit breaker created successfully")
        
        # Test circuit breaker state
        print(f"✅ Circuit breaker state: {circuit_breaker.state}")
        print(f"✅ Circuit breaker is open: {circuit_breaker.is_circuit_open()}")
        
        # Test basic functionality (without actual LLM calls)
        async def mock_llm_func(*args):
            return "MockedSpeaker"
        
        async def mock_fallback_func(*args):
            return "FallbackSpeaker"
        
        result = await circuit_breaker.call_with_circuit_breaker(
            mock_llm_func,
            mock_fallback_func,
            "test text"
        )
        print(f"✅ Circuit breaker call result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Circuit breaker integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_monitor():
    """Test performance monitoring integration"""
    print("\nTesting performance monitor integration...")
    
    try:
        from core.speaker_detection.performance_monitor import performance_monitor
        
        # Test recording a detection
        performance_monitor.record_detection(
            text="John: Test message",
            result="John",
            method="regex",
            execution_time=0.001,
            success=True
        )
        print("✅ Performance detection recorded")
        
        # Get performance report
        report = performance_monitor.get_performance_report()
        print(f"✅ Performance report generated: {report['summary']['total_detections']} detections")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitor integration test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("ENHANCED SPEAKER DETECTION INTEGRATION TESTS")
    print("=" * 60)
    
    tests = [
        ("Enhanced Extractor Direct", test_enhanced_extractor_direct),
        ("Plugin Registration", test_plugin_registration),
        ("Circuit Breaker Integration", test_circuit_breaker_integration),
        ("Performance Monitor", test_performance_monitor)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        print("-" * 40)
        
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"[RESULT] ✅ {test_name} PASSED")
            else:
                print(f"[RESULT] ❌ {test_name} FAILED")
        except Exception as e:
            print(f"[RESULT] ❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        return True
    else:
        print("❌ Some integration tests failed")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())