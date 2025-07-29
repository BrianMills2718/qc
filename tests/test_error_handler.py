"""Unit tests for error handling"""

import pytest
import asyncio
import logging
from qc.utils.error_handler import (
    LLMError, TokenLimitError, RateLimitError, ExtractionError, ValidationError,
    is_retryable_error, retry_with_backoff, ErrorHandler
)


class TestErrorTypes:
    """Test custom error types"""
    
    def test_error_hierarchy(self):
        """Test error class hierarchy"""
        assert issubclass(TokenLimitError, LLMError)
        assert issubclass(RateLimitError, LLMError)
        assert issubclass(ExtractionError, LLMError)
    
    def test_error_creation(self):
        """Test creating custom errors"""
        token_err = TokenLimitError("Too many tokens")
        assert str(token_err) == "Too many tokens"
        assert isinstance(token_err, LLMError)
        
        rate_err = RateLimitError("Rate limited")
        assert isinstance(rate_err, LLMError)


class TestRetryableErrors:
    """Test retryable error detection"""
    
    def test_rate_limit_retryable(self):
        """Rate limit errors should be retryable"""
        assert is_retryable_error(RateLimitError("429 rate limit"))
        assert is_retryable_error(Exception("Error 429: rate_limit exceeded"))
    
    def test_timeout_retryable(self):
        """Timeout errors should be retryable"""
        assert is_retryable_error(Exception("Request timed out"))
        assert is_retryable_error(Exception("Operation timeout"))
    
    def test_connection_retryable(self):
        """Connection errors should be retryable"""
        assert is_retryable_error(Exception("Connection failed"))
        assert is_retryable_error(Exception("Network error"))
    
    def test_server_errors_retryable(self):
        """5xx errors should be retryable"""
        assert is_retryable_error(Exception("500 Internal Server Error"))
        assert is_retryable_error(Exception("502 Bad Gateway"))
        assert is_retryable_error(Exception("503 Service Unavailable"))
    
    def test_non_retryable_errors(self):
        """Some errors should not be retryable"""
        assert not is_retryable_error(TokenLimitError("Token limit exceeded"))
        assert not is_retryable_error(ValidationError("Invalid response"))


class TestRetryDecorator:
    """Test retry decorator functionality"""
    
    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async function retry on success"""
        call_count = 0
        
        @retry_with_backoff(max_tries=3, max_time=5)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 2
    
    def test_sync_retry_success(self):
        """Test sync function retry on success"""
        call_count = 0
        
        @retry_with_backoff(max_tries=3, max_time=5)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RateLimitError("Rate limited")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_non_retryable(self):
        """Test that non-retryable errors are raised immediately"""
        call_count = 0
        
        @retry_with_backoff(max_tries=3)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise TokenLimitError("Token limit exceeded")
        
        with pytest.raises(TokenLimitError):
            await failing_function()
        
        assert call_count == 1  # Should not retry
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry exhaustion"""
        call_count = 0
        
        @retry_with_backoff(max_tries=2, max_time=5)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise RateLimitError("Always fails")
        
        with pytest.raises(RateLimitError):
            await always_fails()
        
        assert call_count == 2  # Should try max_tries times


class TestErrorHandler:
    """Test centralized error handler"""
    
    def test_handle_token_limit_error(self, caplog):
        """Test handling token limit errors"""
        handler = ErrorHandler()
        error = TokenLimitError("Prompt too large: 1000 tokens")
        
        with caplog.at_level(logging.INFO):
            handler.handle_llm_error(error, "test context")
        
        assert "Token limit exceeded in test context" in caplog.text
        assert "Consider chunking the input or reducing prompt size" in caplog.text
    
    def test_handle_rate_limit_error(self, caplog):
        """Test handling rate limit errors"""
        handler = ErrorHandler()
        error = RateLimitError("Rate limit: 429")
        
        with caplog.at_level(logging.INFO):
            handler.handle_llm_error(error, "test context")
        
        assert "Rate limit hit in test context" in caplog.text
        assert "Will retry with backoff" in caplog.text
    
    def test_handle_validation_error(self, caplog):
        """Test handling validation errors"""
        handler = ErrorHandler()
        error = ValidationError("Invalid JSON response")
        
        with caplog.at_level(logging.DEBUG):
            handler.handle_llm_error(error, "test context")
        
        assert "Response validation failed" in caplog.text
        assert "Check if LLM response matches" in caplog.text
    
    def test_handle_generic_error(self, caplog):
        """Test handling generic errors"""
        handler = ErrorHandler()
        error = Exception("Something went wrong")
        
        handler.handle_llm_error(error, "test context")
        
        assert "Unexpected Exception in test context" in caplog.text