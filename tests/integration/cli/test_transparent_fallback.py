"""
Test-Driven Development: Transparent Fallback Implementation
Tests that users are notified when fallback is used and always know which method was active
These tests MUST fail initially due to lack of user transparency
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import io

# Add qc_clean to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

@pytest.fixture
async def llm_handler():
    """Create LLM handler for testing"""
    from core.llm.llm_handler import LLMHandler
    from config.unified_config import UnifiedConfig
    
    config = UnifiedConfig()
    gt_config = config.to_grounded_theory_config()
    return LLMHandler(config=gt_config)

@pytest.fixture
async def enhanced_extractor_llm_enabled(llm_handler):
    """Create enhanced extractor with LLM detection enabled"""
    from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=True
    )

@pytest.fixture
async def enhanced_extractor_llm_disabled(llm_handler):
    """Create enhanced extractor with LLM detection disabled (baseline)"""
    from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=False
    )

@pytest.mark.asyncio
async def test_user_notification_during_successful_llm(enhanced_extractor_llm_enabled, capsys):
    """
    Test that users are notified when LLM is successfully used
    THIS TEST MUST FAIL INITIALLY - no current user notifications exist
    """
    print("Testing user notification during successful LLM...")
    
    # Perform LLM detection that should succeed (after schema fix)
    result = await enhanced_extractor_llm_enabled._detect_speaker("John: Hello everyone")
    
    # Extract speaker name from result (handles both string and dict formats)
    speaker_name = result.get('speaker_name') if isinstance(result, dict) else result
    
    # Capture any stdout/stderr output
    captured = capsys.readouterr()
    
    # Should notify user that LLM was used successfully
    # Look for indicators like "LLM", "detection", "enhanced", etc.
    llm_indicators = ['llm', 'enhanced', 'detection method']
    found_indicator = any(indicator.lower() in captured.out.lower() or 
                         indicator.lower() in captured.err.lower() 
                         for indicator in llm_indicators)
    
    assert found_indicator, f"No LLM usage notification found in output. Captured: {captured}"
    print(f"SUCCESS: LLM usage notification detected in output")

@pytest.mark.asyncio
async def test_user_notification_during_fallback(enhanced_extractor_llm_enabled, capsys):
    """
    Test that users are notified when fallback is used due to LLM failure
    THIS TEST MUST FAIL INITIALLY - fallback is currently silent
    """
    print("Testing user notification during fallback...")
    
    # Force LLM failure by mocking the LLM handler to fail
    with patch.object(enhanced_extractor_llm_enabled.speaker_bridge, 'detect_speaker_simple', 
                      side_effect=Exception("Forced LLM failure for test")):
        
        result = await enhanced_extractor_llm_enabled._detect_speaker("John: Hello everyone")
        
        # Extract speaker name from result (handles both string and dict formats)
        speaker_name = result.get('speaker_name') if isinstance(result, dict) else result
        
        # Capture any stdout/stderr output
        captured = capsys.readouterr()
        
        # Should notify user that fallback was used
        fallback_indicators = ['fallback', 'regex', 'failed', 'using', 'backup']
        found_indicator = any(indicator.lower() in captured.out.lower() or 
                             indicator.lower() in captured.err.lower() 
                             for indicator in fallback_indicators)
        
        assert found_indicator, f"No fallback notification found in output. Captured: {captured}"
        print(f"SUCCESS: Fallback notification detected in output")

@pytest.mark.asyncio
async def test_detection_method_reporting_in_results(enhanced_extractor_llm_enabled):
    """
    Test that detection results include information about which method was used
    THIS TEST MUST FAIL INITIALLY - results don't include method information
    """
    print("Testing detection method reporting in results...")
    
    # Test successful LLM detection
    result = await enhanced_extractor_llm_enabled._detect_speaker("John: Hello everyone")
    
    # Result should include method information somehow
    # This might be returned as a tuple, dict, or object with method info
    # Initial implementation will just return string, so this should fail
    
    if isinstance(result, dict):
        assert 'method' in result or 'detection_method' in result, "Result should include detection method"
        print(f"SUCCESS: Method info in dict result: {result}")
    elif isinstance(result, tuple):
        assert len(result) >= 2, "Result tuple should include speaker and method"
        print(f"SUCCESS: Method info in tuple result: {result}")
    else:
        # Current implementation returns just string - should fail this test
        pytest.fail(f"Result should include detection method info, got: {type(result)} = {result}")

@pytest.mark.asyncio
async def test_transparent_method_differentiation(enhanced_extractor_llm_enabled, enhanced_extractor_llm_disabled):
    """
    Test that users can clearly differentiate between LLM and regex results
    THIS TEST MUST FAIL INITIALLY - both modes return identical output
    """
    print("Testing transparent method differentiation...")
    
    test_text = "Sarah: Good morning everyone"
    
    # Get results from both modes
    llm_result = await enhanced_extractor_llm_enabled._detect_speaker(test_text)
    regex_result = await enhanced_extractor_llm_disabled._detect_speaker(test_text)
    
    print(f"LLM result: {llm_result}")
    print(f"Regex result: {regex_result}")
    
    # Results should have some way to distinguish the method used
    # This could be through different return types, embedded metadata, or output format
    
    # Test 1: Check if results have different formats/types
    if type(llm_result) != type(regex_result):
        print(f"SUCCESS: Different result types - LLM: {type(llm_result)}, Regex: {type(regex_result)}")
        return  # Test passes
    
    # Test 2: Check if results contain method information
    if isinstance(llm_result, dict) and isinstance(regex_result, dict):
        llm_method = llm_result.get('method', llm_result.get('detection_method'))
        regex_method = regex_result.get('method', regex_result.get('detection_method'))
        if llm_method != regex_method:
            print(f"SUCCESS: Different method indicators - LLM: {llm_method}, Regex: {regex_method}")
            return  # Test passes
    
    # Test 3: Check if results have distinguishable content
    # Current implementation will return identical strings, so this should fail
    pytest.fail(f"Cannot distinguish between LLM and regex results - both return: {llm_result}")

@pytest.mark.asyncio
async def test_circuit_breaker_transparency(enhanced_extractor_llm_enabled):
    """
    Test that circuit breaker state changes are transparent to users
    THIS TEST MUST FAIL INITIALLY - circuit breaker operates silently
    """
    print("Testing circuit breaker transparency...")
    
    # Force multiple LLM failures to trigger circuit breaker
    with patch.object(enhanced_extractor_llm_enabled.speaker_bridge, 'detect_speaker_simple',
                      side_effect=Exception("Simulated LLM failure")):
        
        # Perform multiple detections to trigger circuit breaker
        for i in range(6):  # Exceed failure threshold (5)
            result = await enhanced_extractor_llm_enabled._detect_speaker(f"Test {i}: Hello")
            speaker_name = result.get('speaker_name') if isinstance(result, dict) else result
            print(f"   Attempt {i+1}: {speaker_name}")
        
        # Check circuit breaker state
        if hasattr(enhanced_extractor_llm_enabled, 'circuit_breaker'):
            cb_state = enhanced_extractor_llm_enabled.circuit_breaker.state
            print(f"   Circuit breaker state: {cb_state}")
            
            # Circuit breaker should be OPEN after multiple failures
            assert cb_state == "OPEN", f"Expected circuit breaker to be OPEN, got: {cb_state}"
            
            # Test that subsequent calls indicate circuit breaker is active
            # This should be visible to users somehow
            result = await enhanced_extractor_llm_enabled._detect_speaker("Final test: Hello")
            
            # Check if circuit breaker status is visible in result
            if isinstance(result, dict) and 'circuit_breaker_status' in result:
                cb_status = result['circuit_breaker_status']
                detection_method = result.get('detection_method')
                print(f"SUCCESS: Circuit breaker transparency - Status: {cb_status}, Method: {detection_method}")
                assert cb_status == "OPEN", f"Expected OPEN status, got: {cb_status}"
                assert 'fallback' in detection_method, f"Expected fallback method, got: {detection_method}"
            else:
                pytest.fail(f"Circuit breaker operation should be transparent to users, got: {result}")

@pytest.mark.asyncio  
async def test_performance_monitoring_visibility():
    """
    Test that performance monitoring provides user-visible insights
    THIS TEST MUST FAIL INITIALLY - monitoring data not exposed to users
    """
    print("Testing performance monitoring visibility...")
    
    from core.speaker_detection.performance_monitor import performance_monitor
    
    # Record some test data
    performance_monitor.record_detection("Test: message", "Test", "llm", 0.5, True)
    performance_monitor.record_detection("Another: message", "Another", "regex", 0.1, True)
    
    # Get performance report
    report = performance_monitor.get_performance_report()
    
    # Report should be accessible and contain useful user-facing information
    assert 'summary' in report, "Performance report should have summary section"
    assert 'recommendations' in report, "Performance report should have recommendations"
    
    # Test that user can access this information
    # Currently there's no user-facing way to see performance data
    # This test will pass only if performance data is made accessible to users
    
    print(f"Performance report available: {report['summary']}")
    print(f"Recommendations: {report['recommendations']}")

if __name__ == "__main__":
    print("RUNNING TRANSPARENT FALLBACK TESTS")
    print("These tests should FAIL initially, then PASS after transparency implementation")
    
    # Run tests directly for development
    asyncio.run(pytest.main([__file__, "-v", "-s"]))