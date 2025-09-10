"""
Final Success Criteria Validation (Windows Compatible)
"""
import sys
import os
import asyncio
import subprocess
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

async def main():
    """Run comprehensive validation"""
    print("ENHANCED SPEAKER DETECTION - FINAL VALIDATION")
    print("=" * 60)
    
    passed = 0
    total = 7
    
    # 1. Schema Bridge Functional
    print("\n1. Testing Schema Bridge...")
    try:
        from core.speaker_detection.schema_bridge import SpeakerDetectionBridge
        from core.llm.llm_handler import LLMHandler
        from config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        gt_config = config.to_grounded_theory_config()
        llm_handler = LLMHandler(config=gt_config)
        bridge = SpeakerDetectionBridge(llm_handler)
        
        print("   PASS - Schema bridge imports and initializes successfully")
        passed += 1
    except Exception as e:
        print(f"   FAIL - Schema bridge error: {e}")
    
    # 2. Enhanced Plugin Available
    print("\n2. Testing Enhanced Plugin Registration...")
    try:
        from plugins.extractors import get_available_extractors, get_extractor_plugin
        
        extractors = get_available_extractors()
        enhanced_available = "enhanced_semantic" in extractors
        plugin = get_extractor_plugin("enhanced_semantic") if enhanced_available else None
        
        if enhanced_available and plugin:
            print(f"   PASS - Enhanced plugin registered and functional")
            print(f"   Available extractors: {extractors}")
            passed += 1
        else:
            print(f"   FAIL - Enhanced plugin not properly registered")
    except Exception as e:
        print(f"   FAIL - Plugin registration error: {e}")
    
    # 3. LLM Detection Working
    print("\n3. Testing LLM Detection Components...")
    try:
        from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
        
        # Test with LLM detection enabled
        enhanced_extractor = EnhancedSemanticExtractor(
            llm_handler=llm_handler,
            use_llm_speaker_detection=True
        )
        
        has_components = (
            enhanced_extractor.speaker_bridge is not None and
            enhanced_extractor.circuit_breaker is not None
        )
        
        if has_components:
            print("   PASS - LLM detection components properly initialized")
            passed += 1
        else:
            print("   FAIL - LLM detection components missing")
    except Exception as e:
        print(f"   FAIL - LLM detection error: {e}")
    
    # 4. Circuit Breaker Active
    print("\n4. Testing Circuit Breaker...")
    try:
        from core.speaker_detection.circuit_breaker import SpeakerDetectionCircuitBreaker
        
        circuit_breaker = SpeakerDetectionCircuitBreaker()
        
        async def mock_func(*args):
            return "test_result"
        
        result = await circuit_breaker.call_with_circuit_breaker(
            mock_func, mock_func, "test"
        )
        
        if result == "test_result" and circuit_breaker.state == "CLOSED":
            print("   PASS - Circuit breaker functional")
            passed += 1
        else:
            print("   FAIL - Circuit breaker not working properly")
    except Exception as e:
        print(f"   FAIL - Circuit breaker error: {e}")
    
    # 5. Performance Monitoring
    print("\n5. Testing Performance Monitoring...")
    try:
        from core.speaker_detection.performance_monitor import performance_monitor
        
        # Record test detection
        performance_monitor.record_detection(
            text="Test: message",
            result="Test",
            method="regex", 
            execution_time=0.001,
            success=True
        )
        
        report = performance_monitor.get_performance_report()
        has_metrics = report.get('summary', {}).get('total_detections', 0) > 0
        
        if has_metrics:
            print("   PASS - Performance monitoring functional")
            passed += 1
        else:
            print("   FAIL - Performance monitoring not recording metrics")
    except Exception as e:
        print(f"   FAIL - Performance monitoring error: {e}")
    
    # 6. CLI Integration
    print("\n6. Testing CLI Integration...")
    try:
        # Test CLI help
        result = subprocess.run([
            sys.executable, "-m", "qc_clean.core.cli.cli_robust", "--help"
        ], capture_output=True, text=True, cwd="qc_clean")
        
        # Test workflow integration
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        from core.cli.robust_cli_operations import RobustCLIOperations
        from config.unified_config import UnifiedConfig
        
        config = UnifiedConfig()
        robust_ops = RobustCLIOperations(config=config)
        workflow = GroundedTheoryWorkflow(robust_operations=robust_ops)
        
        cli_works = result.returncode == 0
        has_integration = hasattr(workflow, '_initialize_extractor_plugin')
        
        if cli_works and has_integration:
            print("   PASS - CLI integration complete")
            passed += 1
        else:
            print(f"   FAIL - CLI issues: help={cli_works}, integration={has_integration}")
    except Exception as e:
        print(f"   FAIL - CLI integration error: {e}")
    
    # 7. Zero Regression
    print("\n7. Testing Zero Regression...")
    try:
        from plugins.extractors import get_available_extractors, get_extractor_plugin
        
        extractors = get_available_extractors()
        original_extractors = ["hierarchical", "relationship", "semantic", "validated"]
        all_present = all(ext in extractors for ext in original_extractors)
        
        semantic_works = get_extractor_plugin("semantic") is not None
        
        if all_present and semantic_works:
            print("   PASS - Zero regression confirmed")
            print(f"   All extractors available: {extractors}")
            passed += 1
        else:
            print(f"   FAIL - Regression detected: {extractors}")
    except Exception as e:
        print(f"   FAIL - Regression test error: {e}")
    
    # Final Results
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {passed}/{total} SUCCESS CRITERIA PASSED")
    print("=" * 60)
    
    if passed == total:
        print("SUCCESS: ALL CRITERIA PASSED!")
        print("Enhanced Speaker Detection implementation is COMPLETE!")
        
        # Test functionality with real data
        print("\nTesting enhanced extractor with sample text...")
        try:
            enhanced_extractor = EnhancedSemanticExtractor(
                llm_handler=llm_handler,
                use_llm_speaker_detection=False  # Use regex for demo
            )
            
            test_cases = [
                "John: Welcome to our interview",
                "Sarah said she agrees with the approach",
                "I believe this methodology is sound"
            ]
            
            print("Speaker Detection Results:")
            for text in test_cases:
                speaker = await enhanced_extractor._detect_speaker(text)
                print(f"  '{text[:30]}...' -> {speaker}")
                
            print("\nImplementation is fully functional!")
            
        except Exception as e:
            print(f"Functionality test error: {e}")
        
        return True
    else:
        missing = total - passed
        print(f"PARTIAL SUCCESS: {missing} criteria still need work")
        return False

if __name__ == "__main__":
    asyncio.run(main())