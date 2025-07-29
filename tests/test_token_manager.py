"""Unit tests for token manager"""

import pytest
from qc.utils.token_manager import TokenManager, TokenLimitError


class TestTokenManager:
    """Test token management functionality"""
    
    def test_token_counting(self):
        """Test basic token counting"""
        manager = TokenManager()
        
        # Test with simple text
        text = "This is a simple test."
        tokens = manager.count_tokens(text)
        assert tokens > 0
        assert tokens < 10  # Should be around 5-6 tokens
    
    def test_validate_prompt_size(self):
        """Test prompt size validation"""
        manager = TokenManager(max_tokens=100)
        
        # Small prompt should pass
        small_prompt = "Hello world"
        assert manager.validate_prompt_size(small_prompt, max_response_tokens=10)
        
        # Large prompt should raise error
        large_prompt = "x" * 1000  # Will be ~250 tokens
        with pytest.raises(TokenLimitError):
            manager.validate_prompt_size(large_prompt, max_response_tokens=10)
    
    def test_chunk_text(self):
        """Test text chunking"""
        manager = TokenManager(chunk_size=100)
        
        # Text that needs chunking
        long_text = " ".join(["This is a test sentence."] * 50)
        chunks = manager.chunk_text(long_text, overlap=10)
        
        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)
    
    def test_optimize_prompt(self):
        """Test prompt optimization"""
        manager = TokenManager()
        
        # Test with a prompt that's already small enough
        small_prompt = "Analyze this text: Hello world"
        optimized = manager.optimize_prompt(small_prompt, max_size=50)
        assert optimized == small_prompt
        
        # Test with a very large prompt that needs truncation
        large_prompt = "Analyze this text: " + "This is a very long sentence. " * 100
        optimized = manager.optimize_prompt(large_prompt, max_size=50)
        assert len(optimized) < len(large_prompt)
        assert "analyze" in optimized.lower()
    
    def test_estimate_chunks(self):
        """Test chunk estimation"""
        manager = TokenManager(chunk_size=100)
        
        # Small text - 1 chunk
        small_text = "This is a small text."
        assert manager.estimate_interview_chunks(small_text) == 1
        
        # Large text - multiple chunks
        large_text = " ".join(["This is a test sentence."] * 100)
        chunks_needed = manager.estimate_interview_chunks(large_text)
        assert chunks_needed > 1
    
    def test_token_usage_stats(self):
        """Test token usage statistics"""
        manager = TokenManager()
        
        prompts = ["Hello", "World", "Test"]
        responses = ["Hi", "Earth", "Success"]
        
        stats = manager.get_token_usage_stats(prompts, responses)
        
        assert stats["prompts_count"] == 3
        assert stats["responses_count"] == 3
        assert stats["total_tokens"] > 0
        assert stats["avg_prompt_tokens"] > 0
        assert stats["avg_response_tokens"] > 0
        assert 0 <= stats["utilization_percent"] <= 100