"""
Circuit Breaker for LLM Speaker Detection
Prevents cascading failures and manages fallback behavior
"""
import time
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)

class SpeakerDetectionCircuitBreaker:
    """Circuit breaker for LLM speaker detection with automatic fallback"""
    
    def __init__(self, failure_threshold=5, timeout_seconds=30):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_circuit_open(self) -> bool:
        """Check if circuit is open (should fallback)"""
        if self.state == "OPEN":
            # Check if timeout period has passed
            if time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: HALF_OPEN - attempting LLM retry")
                return False
            return True
        return False
    
    async def call_with_circuit_breaker(
        self,
        llm_func: Callable,
        fallback_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute LLM function with circuit breaker protection"""
        
        if self.is_circuit_open():
            logger.info("Circuit breaker OPEN - using fallback immediately")
            return await fallback_func(*args, **kwargs)
        
        try:
            result = await llm_func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logger.info("Circuit breaker: CLOSED - LLM recovery successful")
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM speaker detection failed: {e}")
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker OPEN - {self.failure_count} failures, using fallback for {self.timeout_seconds}s")
            
            # Use fallback
            return await fallback_func(*args, **kwargs)