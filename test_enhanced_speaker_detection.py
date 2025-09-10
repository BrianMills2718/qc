"""
Test framework for enhanced speaker detection
Following Test-Driven Development principles
"""
import pytest
import asyncio
import sys
import os

# Add qc_clean to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qc_clean'))

from plugins.extractors.enhanced_semantic_extractor import EnhancedSemanticExtractor
from core.llm.llm_handler import LLMHandler
from config.unified_config import UnifiedConfig

@pytest.fixture
async def enhanced_extractor():
    """Create enhanced extractor for testing"""
    config = UnifiedConfig()
    llm_handler = LLMHandler(config=config.to_grounded_theory_config())
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=True
    )

@pytest.fixture  
async def regex_extractor():
    """Create regex-only extractor for comparison"""
    config = UnifiedConfig()
    llm_handler = LLMHandler(config=config.to_grounded_theory_config())
    return EnhancedSemanticExtractor(
        llm_handler=llm_handler,
        use_llm_speaker_detection=False
    )

class TestSpeakerDetectionBaseline:
    """Baseline tests - these must pass before LLM implementation"""
    
    @pytest.mark.asyncio
    async def test_regex_baseline_accuracy(self, regex_extractor):
        """Test current regex accuracy - establish baseline"""
        test_cases = [
            ("John: Hello everyone", "John"),
            ("Sarah said we should proceed", "Sarah"), 
            ("I think that's correct", "Participant"),
            ("We believe this is right", "Participant"),
            ("The system shows error", None)
        ]
        
        passed = 0
        for text, expected in test_cases:
            result = await regex_extractor._detect_speaker(text)
            if result == expected:
                passed += 1
            print(f"'{text}' -> Expected: {expected}, Got: {result}")
        
        baseline_accuracy = passed / len(test_cases)
        print(f"Regex baseline accuracy: {baseline_accuracy:.2%}")
        assert baseline_accuracy >= 0.6  # Minimum acceptable baseline
        return baseline_accuracy

class TestLLMSpeakerDetection:
    """LLM speaker detection tests - must meet or exceed baseline"""
    
    @pytest.mark.asyncio
    async def test_llm_speaker_accuracy(self, enhanced_extractor, regex_extractor):
        """LLM detection must match or exceed regex accuracy"""
        test_cases = [
            ("John: Hello everyone", "John"),
            ("Sarah said we should proceed", "Sarah"),
            ("I think that's correct", "Participant"), 
            ("We believe this is right", "Participant"),
            ("The system shows error", None)
        ]
        
        # Get baseline accuracy
        regex_passed = 0
        llm_passed = 0
        
        for text, expected in test_cases:
            regex_result = await regex_extractor._detect_speaker(text)
            llm_result = await enhanced_extractor._detect_speaker(text)
            
            if regex_result == expected:
                regex_passed += 1
            if llm_result == expected:
                llm_passed += 1
                
            print(f"'{text}':")
            print(f"  Expected: {expected}")
            print(f"  Regex: {regex_result}")  
            print(f"  LLM: {llm_result}")
        
        regex_accuracy = regex_passed / len(test_cases)
        llm_accuracy = llm_passed / len(test_cases)
        
        print(f"Regex accuracy: {regex_accuracy:.2%}")
        print(f"LLM accuracy: {llm_accuracy:.2%}")
        
        # LLM must match or exceed regex performance
        assert llm_accuracy >= regex_accuracy
    
    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self, enhanced_extractor):
        """When LLM fails, must fallback to regex successfully"""
        # This tests the fail-fast with fallback behavior
        text = "John: This should work even if LLM fails"
        
        # Test that fallback actually works by patching LLM to fail
        import unittest.mock
        with unittest.mock.patch.object(
            enhanced_extractor.speaker_bridge, 
            'detect_speaker_simple',
            side_effect=Exception("Simulated LLM failure")
        ):
            result = await enhanced_extractor._detect_speaker(text)
            # Should fallback to regex and return "John"
            assert result == "John"
    
    @pytest.mark.asyncio
    async def test_performance_acceptable(self, enhanced_extractor, regex_extractor):
        """LLM detection must complete within acceptable time"""
        import time
        text = "Sarah: Performance test text"
        
        # Measure regex performance
        start_time = time.time()
        regex_result = await regex_extractor._detect_speaker(text) 
        regex_time = time.time() - start_time
        
        # Measure LLM performance
        start_time = time.time()
        llm_result = await enhanced_extractor._detect_speaker(text)
        llm_time = time.time() - start_time
        
        print(f"Regex time: {regex_time:.3f}s")
        print(f"LLM time: {llm_time:.3f}s")
        
        # Accept 10x performance degradation as maximum acceptable
        assert llm_time < (regex_time * 10) or llm_time < 10.0  # Max 10 seconds

if __name__ == "__main__":
    # Run tests directly for development
    asyncio.run(pytest.main([__file__, "-v"]))