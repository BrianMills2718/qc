"""
Error Handling and Retry Logic for LLM Operations

Provides robust error handling with exponential backoff for transient failures.
"""

import logging
import asyncio
import time
from typing import TypeVar, Callable
from functools import wraps
import backoff

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LLMError(Exception):
    """Base exception for LLM-related errors"""
    pass


class TokenLimitError(LLMError):
    """Raised when token limit is exceeded"""
    pass


class RateLimitError(LLMError):
    """Raised when rate limited by API"""
    pass


class ExtractionError(LLMError):
    """Raised when extraction fails"""
    pass


class ValidationError(LLMError):
    """Raised when response validation fails"""
    pass


class ProcessingError(LLMError):
    """Raised when CLI processing fails"""
    pass


class QueryError(LLMError):
    """Raised when database query fails"""
    pass


class TokenizationError(LLMError):
    """Raised when token processing fails"""
    pass


class LiteLLMError(LLMError):
    """Raised when LiteLLM-specific errors occur"""
    pass


class LiteLLMSchemaError(LiteLLMError):
    """Raised when LiteLLM schema validation fails"""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is retryable
    """
    error_str = str(error).lower()
    
    # Rate limit errors are always retryable
    if isinstance(error, RateLimitError) or 'rate_limit' in error_str or '429' in error_str:
        return True
    
    # Timeout errors are retryable
    if 'timeout' in error_str or 'timed out' in error_str:
        return True
    
    # Connection errors are retryable
    if 'connection' in error_str or 'network' in error_str:
        return True
    
    # Server errors (5xx) are retryable
    if '500' in error_str or '502' in error_str or '503' in error_str:
        return True
    
    # LiteLLM transient errors are retryable
    if 'litellm.RateLimitError' in str(error) or 'quota' in error_str:
        return True
    
    # LiteLLM server errors are retryable
    if 'litellm.InternalServerError' in str(error):
        return True
    
    # Token limit errors are NOT retryable (need different approach)
    if isinstance(error, TokenLimitError):
        return False
    
    # Validation errors are NOT retryable
    if isinstance(error, ValidationError):
        return False
    
    # LiteLLM schema errors are NOT retryable (need schema fix)
    if isinstance(error, LiteLLMSchemaError) or 'response_schema' in error_str:
        return False
    
    # LiteLLM bad request errors (400) are NOT retryable
    if 'litellm.BadRequestError' in str(error) and '400' in error_str:
        return False
    
    return False


def retry_with_backoff(
    max_tries: int = 3,
    max_time: int = 60,
    backoff_factor: float = 2.0,
    exceptions: tuple = (LLMError,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_tries: Maximum number of retry attempts
        max_time: Maximum time to spend retrying (seconds)
        backoff_factor: Exponential backoff factor
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            last_error = None
            
            for attempt in range(max_tries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    # Check if we've exceeded max time
                    elapsed = time.time() - start_time
                    if elapsed >= max_time:
                        logger.error(f"Max retry time exceeded for {func.__name__}")
                        raise
                    
                    # Calculate backoff time
                    wait_time = min(backoff_factor ** attempt, max_time - elapsed)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_tries} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    
                    await asyncio.sleep(wait_time)
            
            # All retries exhausted
            logger.error(f"All {max_tries} attempts failed for {func.__name__}")
            raise last_error or LLMError(f"All retry attempts failed for {func.__name__}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            last_error = None
            
            for attempt in range(max_tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise
                    
                    elapsed = time.time() - start_time
                    if elapsed >= max_time:
                        logger.error(f"Max retry time exceeded for {func.__name__}")
                        raise
                    
                    wait_time = min(backoff_factor ** attempt, max_time - elapsed)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_tries} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    
                    time.sleep(wait_time)
            
            logger.error(f"All {max_tries} attempts failed for {func.__name__}")
            raise last_error or LLMError(f"All retry attempts failed for {func.__name__}")
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class ErrorHandler:
    """
    Centralized error handling for the application.
    """
    
    @staticmethod
    def handle_llm_error(error: Exception, context: str = "") -> None:
        """
        Handle LLM-specific errors with appropriate logging and context.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        if isinstance(error, TokenLimitError):
            logger.error(f"Token limit exceeded in {context}: {error_msg}")
            logger.info("Consider chunking the input or reducing prompt size")
        
        elif isinstance(error, RateLimitError):
            logger.warning(f"Rate limit hit in {context}: {error_msg}")
            logger.info("Will retry with backoff")
        
        elif isinstance(error, ValidationError):
            logger.error(f"Response validation failed in {context}: {error_msg}")
            logger.debug("Check if LLM response matches expected schema")
        
        elif isinstance(error, ExtractionError):
            logger.error(f"Extraction failed in {context}: {error_msg}")
        
        elif isinstance(error, LiteLLMSchemaError):
            logger.error(f"LiteLLM schema validation failed in {context}: {error_msg}")
            logger.info("Check Pydantic model schema compatibility with LiteLLM")
        
        elif isinstance(error, LiteLLMError):
            logger.error(f"LiteLLM error in {context}: {error_msg}")
            if 'quota' in error_msg.lower():
                logger.info("API quota exceeded - consider rate limiting")
        
        else:
            logger.error(f"Unexpected {error_type} in {context}: {error_msg}")
    
    @staticmethod
    def wrap_extraction_errors(func: Callable) -> Callable:
        """
        Decorator to wrap extraction functions with proper error handling.
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, LLMError):
                    raise
                
                # Wrap unexpected errors
                raise ExtractionError(f"Extraction failed in {func.__name__}: {str(e)}") from e
        
        return wrapper if asyncio.iscoroutinefunction(func) else func


# Backoff decorator using the backoff library for specific patterns
rate_limit_backoff = backoff.on_exception(
    backoff.expo,
    RateLimitError,
    max_tries=5,
    max_time=300,
    jitter=backoff.full_jitter
)

# Custom giveup function for token limit errors
def should_giveup(e):
    """Don't retry on token limit errors"""
    return isinstance(e, TokenLimitError)

llm_backoff = backoff.on_exception(
    backoff.expo,
    LLMError,
    max_tries=3,
    max_time=60,
    giveup=should_giveup
)