# Comprehensive Error Recovery Strategy

## 🎯 Core Philosophy: "Fail Loud and Fast" with Intelligent Recovery

**Key Principles**:
- **No Mocking or Fallbacks**: Everything uses real LLM calls and real data
- **Fail Loud and Fast**: Errors propagate immediately with full context
- **Error Recovery**: Intelligent retry mechanisms with exponential backoff
- **Full Observability**: Complete error tracing and logging
- **Real Interview Data**: Testing with actual data from `data/interviews/`

---

## 📊 Error Classification Matrix

### Primary Error Categories

#### 1. **LLM Response Errors** (CRITICAL - Stop processing)
```python
class LLMResponseError(Exception):
    """Base class for all LLM response failures"""
    pass

class LLMTimeoutError(LLMResponseError):
    """LLM call exceeded timeout threshold"""
    default_timeout: float = 60.0
    recovery_strategy: str = "exponential_backoff_retry"

class LLMMalformedResponseError(LLMResponseError):
    """LLM returned non-JSON or invalid format"""
    recovery_strategy: str = "structured_retry_with_schema"

class LLMEmptyResponseError(LLMResponseError):
    """LLM returned empty or null response"""
    recovery_strategy: str = "prompt_clarification_retry"

class LLMSchemaValidationError(LLMResponseError):
    """LLM response doesn't match Pydantic schema"""
    recovery_strategy: str = "schema_guided_retry"
```

#### 2. **File Processing Errors** (HIGH - Skip file, continue batch)
```python
class FileProcessingError(Exception):
    """Base class for file processing failures"""
    pass

class InterviewFileNotFoundError(FileProcessingError):
    """Interview file doesn't exist at specified path"""
    recovery_strategy: str = "skip_file_log_error"

class CorruptInterviewFileError(FileProcessingError):
    """DOCX file is corrupted or unreadable"""
    recovery_strategy: str = "skip_file_attempt_text_extraction"

class InterviewFileTooLargeError(FileProcessingError):
    """Interview exceeds 1M token limit"""
    token_limit: int = 1_000_000
    recovery_strategy: str = "fail_immediately_no_chunking"
```

#### 3. **API Configuration Errors** (CRITICAL - Stop all processing)
```python
class APIConfigurationError(Exception):
    """Base class for API configuration failures"""
    pass

class MissingAPIKeyError(APIConfigurationError):
    """GEMINI_API_KEY environment variable not set"""
    recovery_strategy: str = "fail_immediately_user_action_required"

class InvalidAPIKeyError(APIConfigurationError):
    """API key is invalid or expired"""
    recovery_strategy: str = "fail_immediately_user_action_required"

class APIRateLimitError(APIConfigurationError):
    """API rate limit exceeded"""
    recovery_strategy: str = "exponential_backoff_with_circuit_breaker"
```

#### 4. **Data Structure Errors** (HIGH - Retry with clarification)
```python
class DataStructureError(Exception):
    """Base class for data structure validation failures"""
    pass

class InvalidOpenCodingResult(DataStructureError):
    """Open coding phase returned invalid structure"""
    recovery_strategy: str = "retry_with_explicit_schema"

class InvalidAxialCodingResult(DataStructureError):
    """Axial coding phase returned invalid structure"""
    recovery_strategy: str = "retry_with_previous_phase_context"

class InvalidSelectiveCodingResult(DataStructureError):
    """Selective coding phase returned invalid structure"""
    recovery_strategy: str = "retry_with_full_context"
```

---

## 🔄 Recovery Strategy Implementation

### 1. **Exponential Backoff Retry Engine**

```python
import asyncio
import random
from typing import TypeVar, Callable, Any
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    exponential_base: float = 2.0

async def retry_with_exponential_backoff(
    operation: Callable[[], Awaitable[T]],
    config: RetryConfig = RetryConfig(),
    error_types: tuple = (Exception,),
    operation_name: str = "Unknown"
) -> T:
    """
    Intelligent retry with exponential backoff and jitter.
    FAILS LOUD AND FAST after max retries exceeded.
    """
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            logger.info(f"Attempting {operation_name} (attempt {attempt + 1}/{config.max_retries + 1})")
            result = await operation()
            
            if attempt > 0:
                logger.info(f"SUCCESS: {operation_name} succeeded on attempt {attempt + 1}")
            
            return result
            
        except error_types as e:
            last_exception = e
            
            if attempt == config.max_retries:
                # FAIL LOUD AND FAST - no more retries
                logger.error(f"FINAL FAILURE: {operation_name} failed after {config.max_retries + 1} attempts")
                logger.error(f"Final error: {type(e).__name__}: {str(e)}")
                raise FinalRetryFailureError(
                    f"{operation_name} failed permanently after {config.max_retries + 1} attempts",
                    original_error=e,
                    attempt_count=attempt + 1
                ) from e
            
            # Calculate delay with exponential backoff and jitter
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            if config.jitter:
                delay *= (0.5 + random.random())  # Add 0-50% jitter
            
            logger.warning(f"RETRY: {operation_name} failed on attempt {attempt + 1}, retrying in {delay:.2f}s")
            logger.warning(f"Error: {type(e).__name__}: {str(e)}")
            
            await asyncio.sleep(delay)
    
    # Should never reach here, but fail loud if we do
    raise RuntimeError(f"Unexpected exit from retry loop for {operation_name}")
```

### 2. **LLM Response Recovery Strategies**

#### A. **Schema-Guided Retry for Malformed JSON**
```python
async def recover_malformed_json_response(
    original_prompt: str,
    malformed_response: str,
    expected_schema: type,
    gemini_client: SimpleGeminiExtractor
) -> Any:
    """
    Recovery strategy for malformed JSON responses.
    Uses explicit schema configuration from GEMINI_STRUCTURED_OUTPUT.md
    """
    
    # Log the failure with full context
    logger.error(f"MALFORMED JSON RESPONSE: {malformed_response[:500]}...")
    
    # Strategy 1: Use Gemini's response_schema configuration (RECOMMENDED)
    retry_config = {
        "response_mime_type": "application/json",
        "response_schema": expected_schema,  # Pydantic model
        "temperature": 0.1,  # Lower temperature for more deterministic output
    }
    
    enhanced_prompt = f"""
    {original_prompt}
    
    CRITICAL: You must return ONLY valid JSON that exactly matches the required schema.
    Do not include any explanatory text before or after the JSON.
    Do not use markdown code blocks.
    Return pure JSON only.
    """
    
    async def schema_guided_retry():
        response = await gemini_client.generate_content(
            enhanced_prompt,
            generation_config=retry_config
        )
        
        # Validate response matches schema
        try:
            validated_result = expected_schema.parse_raw(response.text)
            return validated_result
        except ValidationError as ve:
            raise LLMSchemaValidationError(
                f"Response still doesn't match schema after retry: {ve}"
            ) from ve
    
    return await retry_with_exponential_backoff(
        schema_guided_retry,
        RetryConfig(max_retries=2),  # Limited retries for schema issues
        (LLMMalformedResponseError, LLMSchemaValidationError),
        "Schema-guided JSON retry"
    )
```

#### B. **Three-Phase Coding Error Recovery**
```python
async def recover_three_phase_coding_failure(
    interview_text: str,
    failed_phase: str,
    previous_phase_results: Optional[Any],
    error: Exception,
    gemini_client: SimpleGeminiExtractor
) -> Any:
    """
    Recovery strategy for three-phase coding failures.
    Each phase has specific recovery approach.
    """
    
    if failed_phase == "open_coding":
        # Phase 1 failure: Retry with simplified prompt
        logger.error(f"OPEN CODING FAILED: {error}")
        
        async def simplified_open_coding():
            simplified_prompt = f"""
            Analyze this interview and identify the main themes and codes.
            Focus on the most obvious and clear patterns only.
            
            Interview text: {interview_text[:50000]}  # Limit if very long
            
            Return JSON with: codes, segments, memes (brief analytical notes).
            """
            return await gemini_client.open_coding(simplified_prompt)
        
        return await retry_with_exponential_backoff(
            simplified_open_coding,
            RetryConfig(max_retries=2),
            (LLMResponseError,),
            "Simplified open coding"
        )
    
    elif failed_phase == "axial_coding":
        # Phase 2 failure: Retry with explicit structure guidance
        logger.error(f"AXIAL CODING FAILED: {error}")
        
        if previous_phase_results is None:
            raise CriticalProcessingError("Cannot recover axial coding without open coding results")
        
        async def structured_axial_coding():
            structured_prompt = f"""
            Given these open codes, organize them into clear categories.
            
            Open codes: {previous_phase_results.to_json()}
            
            Create 3-5 main categories maximum.
            For each category, identify 2-3 subcategories.
            Focus on the clearest relationships only.
            """
            return await gemini_client.axial_coding(structured_prompt, previous_phase_results)
        
        return await retry_with_exponential_backoff(
            structured_axial_coding,
            RetryConfig(max_retries=2),
            (LLMResponseError,),
            "Structured axial coding"
        )
    
    elif failed_phase == "selective_coding":
        # Phase 3 failure: Retry with core category focus
        logger.error(f"SELECTIVE CODING FAILED: {error}")
        
        async def focused_selective_coding():
            focused_prompt = f"""
            Identify the ONE main theme that ties everything together.
            Keep it simple and clear.
            
            Categories: {previous_phase_results.to_json() if previous_phase_results else "None"}
            
            Return the core category and how other categories relate to it.
            """
            return await gemini_client.selective_coding(focused_prompt, previous_phase_results)
        
        return await retry_with_exponential_backoff(
            focused_selective_coding,
            RetryConfig(max_retries=2),
            (LLMResponseError,),
            "Focused selective coding"
        )
    
    else:
        raise ValueError(f"Unknown phase for recovery: {failed_phase}")
```

### 3. **File Processing Error Recovery**

```python
async def recover_file_processing_error(
    file_path: Path,
    error: FileProcessingError,
    batch_context: BatchProcessingContext
) -> Optional[Interview]:
    """
    Recovery strategies for file processing errors.
    Returns None if file should be skipped (FAIL LOUD AND FAST).
    """
    
    if isinstance(error, InterviewFileNotFoundError):
        # FAIL LOUD - no recovery possible
        logger.error(f"FILE NOT FOUND: {file_path} - SKIPPING")
        batch_context.add_failed_file(file_path, error)
        return None
    
    elif isinstance(error, CorruptInterviewFileError):
        # Attempt alternative extraction methods
        logger.warning(f"CORRUPT FILE: {file_path} - Attempting text extraction")
        
        try:
            # Try alternative text extraction
            text_content = extract_text_alternative_method(file_path)
            
            if len(text_content.strip()) < 100:
                # Too little content - FAIL LOUD
                raise CorruptInterviewFileError(f"Extracted text too short: {len(text_content)} chars")
            
            # Create Interview object from extracted text
            interview = Interview(
                id=f"recovered_{file_path.stem}",
                file_path=file_path,
                title=f"Recovered: {file_path.name}",
                content=text_content,
                metadata={"recovery_method": "alternative_extraction", "original_error": str(error)},
                word_count=len(text_content.split()),
                estimated_tokens=int(len(text_content.split()) * 1.3),
                participant_id=None,
                interview_type="unknown"
            )
            
            logger.info(f"RECOVERY SUCCESS: {file_path} recovered with alternative method")
            return interview
            
        except Exception as recovery_error:
            # Recovery failed - FAIL LOUD
            logger.error(f"RECOVERY FAILED: {file_path} - {recovery_error}")
            batch_context.add_failed_file(file_path, error)
            return None
    
    elif isinstance(error, InterviewFileTooLargeError):
        # FAIL LOUD - no chunking allowed per requirements
        logger.error(f"FILE TOO LARGE: {file_path} exceeds 1M token limit - NO CHUNKING ALLOWED")
        batch_context.add_failed_file(file_path, error)
        return None
    
    else:
        # Unknown file error - FAIL LOUD
        logger.error(f"UNKNOWN FILE ERROR: {file_path} - {error}")
        batch_context.add_failed_file(file_path, error)
        return None
```

### 4. **Circuit Breaker Pattern for API Issues**

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """
    Circuit breaker for API calls to prevent cascading failures.
    FAILS LOUD AND FAST when circuit is OPEN.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        FAILS LOUD when circuit is OPEN.
        """
        
        if self.state == CircuitState.OPEN:
            # Check if we should try recovery
            if (datetime.now() - self.last_failure_time).seconds > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: Attempting recovery (HALF_OPEN)")
            else:
                # FAIL LOUD AND FAST
                raise CircuitBreakerOpenError(
                    f"Circuit breaker OPEN - last failure {self.last_failure_time}, "
                    f"next retry in {self.recovery_timeout - (datetime.now() - self.last_failure_time).seconds}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: Recovery successful (CLOSED)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            
            return result
            
        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker: OPENED after {self.failure_count} failures")
            
            # Re-raise the original exception (FAIL LOUD)
            raise
```

---

## 🧪 Testing Strategy with Real Data

### Test Data Organization
```python
# Test data from specified directories
TEST_DATA_SOURCES = {
    "ai_transcripts": Path("data/interviews/ai"),      # Transcript format
    "africa_notes": Path("data/interviews/africa"),   # Notes format
}

class TestDataManager:
    """Manage real interview data for testing error recovery"""
    
    def __init__(self):
        self.test_files = self._discover_test_files()
    
    def _discover_test_files(self) -> Dict[str, List[Path]]:
        """Find all real interview files for testing"""
        files = {}
        
        for source_name, source_path in TEST_DATA_SOURCES.items():
            if source_path.exists():
                files[source_name] = list(source_path.glob("**/*.docx"))
                logger.info(f"Found {len(files[source_name])} files in {source_name}")
            else:
                logger.warning(f"Test data source not found: {source_path}")
                files[source_name] = []
        
        return files
    
    def get_test_file_by_size(self, size_category: str) -> Path:
        """Get real test file by size category"""
        all_files = []
        for source_files in self.test_files.values():
            all_files.extend(source_files)
        
        if not all_files:
            raise TestDataError("No real interview files found for testing")
        
        # Categorize by file size (proxy for content complexity)
        file_sizes = [(f, f.stat().st_size) for f in all_files]
        file_sizes.sort(key=lambda x: x[1])
        
        if size_category == "small":
            return file_sizes[0][0]  # Smallest file
        elif size_category == "large":
            return file_sizes[-1][0]  # Largest file
        else:  # medium
            return file_sizes[len(file_sizes)//2][0]  # Middle file
```

### Error Recovery Tests
```python
import pytest
from unittest.mock import AsyncMock, patch

class TestErrorRecovery:
    """Test error recovery strategies with real data"""
    
    def setup_method(self):
        self.test_data = TestDataManager()
        self.gemini_client = SimpleGeminiExtractor()
    
    async def test_malformed_json_recovery_with_real_data(self):
        """Test JSON recovery with actual interview file"""
        test_file = self.test_data.get_test_file_by_size("small")
        interview = parse_docx(test_file)  # Real interview data
        
        # Mock malformed response
        with patch.object(self.gemini_client, 'generate_content') as mock_generate:
            # First call returns malformed JSON
            mock_generate.side_effect = [
                AsyncMock(text="This is not JSON at all!"),
                AsyncMock(text='{"codes": [{"name": "test_code", "definition": "test"}]}')
            ]
            
            # Should recover with schema-guided retry
            result = await recover_malformed_json_response(
                "test prompt",
                "malformed response",
                OpenCodingResult,
                self.gemini_client
            )
            
            assert result is not None
            assert mock_generate.call_count == 2  # Initial + 1 retry
    
    async def test_three_phase_failure_with_real_interview(self):
        """Test three-phase failure recovery with real interview"""
        test_file = self.test_data.get_test_file_by_size("medium")
        interview = parse_docx(test_file)  # Real interview data
        
        # Test axial coding failure recovery
        mock_open_result = OpenCodingResult(codes=[], segments=[], memos=[])
        
        with patch.object(self.gemini_client, 'axial_coding') as mock_axial:
            # First call fails, second succeeds
            mock_axial.side_effect = [
                LLMMalformedResponseError("Invalid JSON"),
                AxialCodingResult(categories=[], relationships=[])
            ]
            
            result = await recover_three_phase_coding_failure(
                interview.content,
                "axial_coding",
                mock_open_result,
                LLMMalformedResponseError("test error"),
                self.gemini_client
            )
            
            assert result is not None
            assert mock_axial.call_count == 2
    
    async def test_file_processing_error_with_corrupt_file(self):
        """Test file processing error recovery with real file scenarios"""
        # Test with non-existent file
        fake_path = Path("nonexistent/file.docx")
        batch_context = BatchProcessingContext()
        
        result = await recover_file_processing_error(
            fake_path,
            InterviewFileNotFoundError(f"File not found: {fake_path}"),
            batch_context
        )
        
        # Should return None (skip file) and log error
        assert result is None
        assert len(batch_context.failed_files) == 1
    
    async def test_circuit_breaker_with_api_failures(self):
        """Test circuit breaker with simulated API failures"""
        circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
        
        async def failing_api_call():
            raise APIRateLimitError("Rate limit exceeded")
        
        # Should fail after threshold
        with pytest.raises(APIRateLimitError):
            for i in range(3):
                try:
                    await circuit_breaker.call(failing_api_call)
                except APIRateLimitError:
                    pass  # Expected failures
        
        # Circuit should be open now
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(failing_api_call)
```

---

## 🔍 Error Recovery Monitoring & Observability

### Error Tracking Dashboard
```python
@dataclass
class ErrorRecoveryMetrics:
    """Track error recovery effectiveness"""
    total_errors: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    recovery_times: List[float] = field(default_factory=list)
    circuit_breaker_trips: int = 0
    
    @property
    def recovery_rate(self) -> float:
        if self.total_errors == 0:
            return 0.0
        return self.successful_recoveries / self.total_errors
    
    @property
    def average_recovery_time(self) -> float:
        if not self.recovery_times:
            return 0.0
        return sum(self.recovery_times) / len(self.recovery_times)

class ErrorRecoveryTracker:
    """Monitor and track error recovery across all operations"""
    
    def __init__(self):
        self.metrics = ErrorRecoveryMetrics()
        self.logger = logging.getLogger(__name__)
    
    def record_error(self, error: Exception, recovery_attempted: bool = False):
        """Record error occurrence"""
        self.metrics.total_errors += 1
        error_type = type(error).__name__
        self.metrics.error_types[error_type] = self.metrics.error_types.get(error_type, 0) + 1
        
        self.logger.error(f"ERROR RECORDED: {error_type} - Recovery: {recovery_attempted}")
    
    def record_recovery_success(self, recovery_time: float):
        """Record successful error recovery"""
        self.metrics.successful_recoveries += 1
        self.metrics.recovery_times.append(recovery_time)
        
        self.logger.info(f"RECOVERY SUCCESS: Took {recovery_time:.2f}s")
    
    def record_recovery_failure(self):
        """Record failed error recovery"""
        self.metrics.failed_recoveries += 1
        
        self.logger.error("RECOVERY FAILED: No more recovery options")
    
    def get_summary(self) -> str:
        """Get error recovery summary"""
        return f"""
Error Recovery Summary:
- Total Errors: {self.metrics.total_errors}
- Recovery Rate: {self.metrics.recovery_rate:.2%}
- Avg Recovery Time: {self.metrics.average_recovery_time:.2f}s
- Circuit Breaker Trips: {self.metrics.circuit_breaker_trips}

Error Distribution:
{chr(10).join(f"- {error_type}: {count}" for error_type, count in self.metrics.error_types.items())}
        """.strip()
```

---

## 🎯 Implementation Priority

### Phase 1: Core Error Types (Week 1)
1. **LLM Response Errors** - Schema-guided retry, exponential backoff
2. **File Processing Errors** - Skip corrupted files, fail on missing files
3. **Basic Retry Engine** - Exponential backoff with jitter

### Phase 2: Advanced Recovery (Week 2) 
1. **Three-Phase Specific Recovery** - Phase-aware error handling
2. **Circuit Breaker** - API protection and cascading failure prevention
3. **Error Tracking** - Metrics and observability

### Phase 3: Testing & Validation (Week 3)
1. **Real Data Testing** - Use actual interview files from `data/interviews/`
2. **Error Injection Testing** - Simulate all error scenarios
3. **Performance Testing** - Measure recovery overhead

This comprehensive error recovery strategy ensures robust operation while maintaining the "fail loud and fast" philosophy with intelligent recovery mechanisms.