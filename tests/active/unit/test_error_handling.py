"""
Test LiteLLM Error Handling
Tests the new error classification and handling system.
"""

from pydantic import BaseModel
from typing import List, Dict, Any
from src.qc.core.native_gemini_client import NativeGeminiClient
from src.qc.utils.error_handler import LiteLLMError, LiteLLMSchemaError, is_retryable_error

class BadSchema(BaseModel):
    """Schema that will cause LiteLLM errors"""
    themes: List[Dict[str, Any]]  # This causes schema validation error
    
class GoodSchema(BaseModel):
    """Valid schema"""
    message: str
    count: int

def test_schema_error():
    """Test schema validation error handling"""
    print("Testing LiteLLM Schema Error Handling")
    print("=" * 50)
    
    client = NativeGeminiClient()
    
    try:
        # This should trigger a LiteLLMSchemaError
        result = client.structured_output(
            "Create a test response",
            BadSchema
        )
        print(f"FAIL: Expected error but got result: {result}")
    except LiteLLMSchemaError as e:
        print(f"PASS: Successfully caught LiteLLMSchemaError: {e}")
        print(f"   Is retryable: {is_retryable_error(e)}")
    except Exception as e:
        print(f"FAIL: Got unexpected error type {type(e)}: {e}")

def test_good_schema():
    """Test successful schema validation"""
    print(f"\nTesting Good Schema")
    print("-" * 30)
    
    client = NativeGeminiClient()
    
    try:
        result = client.structured_output(
            "Create a test message with count 42",
            GoodSchema
        )
        print(f"PASS: Good schema worked: {result['response']}")
    except Exception as e:
        print(f"FAIL: Good schema failed: {type(e)} - {e}")

def test_error_classification():
    """Test error classification logic"""
    print(f"\nTesting Error Classification")
    print("-" * 30)
    
    # Test different error types
    test_errors = [
        ("Rate limit error", "litellm.RateLimitError: quota exceeded", True),
        ("Schema error", "response_schema properties error", False),
        ("Bad request", "litellm.BadRequestError: 400", False),
        ("Server error", "litellm.InternalServerError: 500", True),
        ("Timeout", "Request timed out", True),
        ("Connection", "Connection error", True)
    ]
    
    for name, error_msg, expected_retryable in test_errors:
        error = Exception(error_msg)
        is_retryable = is_retryable_error(error)
        status = "PASS" if is_retryable == expected_retryable else "FAIL"
        print(f"  {status} {name}: {'Retryable' if is_retryable else 'Not retryable'}")

if __name__ == "__main__":
    test_schema_error()
    test_good_schema() 
    test_error_classification()
    print(f"\nError handling tests complete!")