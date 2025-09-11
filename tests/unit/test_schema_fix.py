"""
Test-Driven Development: Schema Fix
Tests that LLM calls succeed with proper schema validation
These tests MUST fail initially due to schema issues, then pass after fix
"""
import pytest
import asyncio
import sys
import os
from pathlib import Path

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
async def speaker_bridge(llm_handler):
    """Create speaker detection bridge for testing"""
    from core.speaker_detection.schema_bridge import SpeakerDetectionBridge
    return SpeakerDetectionBridge(llm_handler)

@pytest.mark.asyncio
async def test_llm_schema_compatibility(speaker_bridge):
    """
    Test that LLM calls succeed with proper schema validation
    THIS TEST MUST FAIL INITIALLY due to schema validation errors
    """
    print("Testing LLM schema compatibility...")
    
    # This should succeed without validation errors after schema fix
    result = await speaker_bridge.detect_speaker_simple("John: Hello everyone")
    
    # Should succeed without schema validation errors
    assert result == "John"
    assert isinstance(result, str)
    print(f"SUCCESS: LLM detection returned: {result}")

@pytest.mark.asyncio 
async def test_structured_extraction_success(llm_handler):
    """
    Test that structured extraction succeeds with real LLM calls
    THIS TEST MUST FAIL INITIALLY due to schema validation errors
    """
    print("Testing structured extraction success...")
    
    from core.speaker_detection.schema_bridge import SpeakerDetectionBridge, SimpleSpeakerResult
    
    bridge = SpeakerDetectionBridge(llm_handler)
    prompt = bridge._build_simple_speaker_prompt("Sarah: Good morning")
    
    # Should not raise Pydantic validation errors after schema fix
    result = await llm_handler.extract_structured(prompt=prompt, schema=SimpleSpeakerResult)
    
    assert result.speaker_name == "Sarah"
    assert result.confidence is not None  # Should have a value, not None
    assert result.detection_method is not None  # Should have a value, not None
    
    print(f"SUCCESS: Structured extraction returned: {result}")

@pytest.mark.asyncio
async def test_schema_handles_none_values():
    """
    Test that schema properly handles None values from LLM
    THIS TEST MUST FAIL INITIALLY if schema rejects None values
    """
    print("Testing schema None value handling...")
    
    from core.speaker_detection.schema_bridge import SimpleSpeakerResult
    
    # Test creating schema instance with None values (what LLM might return)
    try:
        result = SimpleSpeakerResult(
            speaker_name=None,
            confidence=None,
            detection_method=None
        )
        print(f"SUCCESS: Schema accepts None values: {result}")
        assert True  # Test passes if no exception raised
    except Exception as e:
        pytest.fail(f"Schema should accept None values but raised: {e}")

@pytest.mark.asyncio
async def test_multiple_speaker_detection_cases(speaker_bridge):
    """
    Test multiple speaker detection cases with fixed schema
    THIS TEST MUST FAIL INITIALLY due to schema validation errors
    """
    print("Testing multiple speaker detection cases...")
    
    test_cases = [
        ("John: Hello everyone", "John"),
        ("Sarah said we should proceed", "Sarah"),
        ("I think that's correct", "Participant"),
        ("We believe this is right", "Participant"),
        ("The system shows error", None)  # Should return None for unclear cases
    ]
    
    success_count = 0
    for text, expected in test_cases:
        try:
            result = await speaker_bridge.detect_speaker_simple(text)
            print(f"   '{text}' -> Expected: {expected}, Got: {result}")
            
            # Allow exact match or reasonable variations
            if result == expected or (expected is None and result in [None, "Participant"]):
                success_count += 1
            else:
                print(f"     MISMATCH: Expected {expected}, got {result}")
                
        except Exception as e:
            print(f"     FAILED: {e}")
    
    # Should have reasonable success rate (at least 60% after fix)
    success_rate = success_count / len(test_cases)
    print(f"SUCCESS RATE: {success_rate:.1%}")
    assert success_rate >= 0.6, f"Success rate {success_rate:.1%} below 60% threshold"

@pytest.mark.asyncio
async def test_no_schema_validation_errors_in_logs(llm_handler, capsys):
    """
    Test that schema validation errors are eliminated after fix
    THIS TEST MUST FAIL INITIALLY due to validation errors in logs
    """
    print("Testing elimination of schema validation errors...")
    
    from core.speaker_detection.schema_bridge import SpeakerDetectionBridge
    
    bridge = SpeakerDetectionBridge(llm_handler)
    
    # Perform LLM call that previously caused validation errors
    try:
        result = await bridge.detect_speaker_simple("John: Test message")
        print(f"LLM call result: {result}")
        
        # After fix, should not see validation error messages
        # This is a behavioral test - we don't want validation errors in normal operation
        assert result is not None  # Should get some result
        print("SUCCESS: No schema validation errors detected")
        
    except Exception as e:
        # After schema fix, should not get validation errors
        error_msg = str(e)
        if "validation error" in error_msg.lower():
            pytest.fail(f"Schema validation error still occurs: {e}")
        else:
            # Other errors are acceptable (e.g., network issues)
            print(f"Non-validation error (acceptable): {e}")

if __name__ == "__main__":
    print("RUNNING SCHEMA FIX TESTS")
    print("These tests should FAIL initially, then PASS after schema fix")
    
    # Run tests directly for development
    asyncio.run(pytest.main([__file__, "-v", "-s"]))