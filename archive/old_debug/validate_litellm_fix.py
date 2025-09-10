import asyncio
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode

async def validate_litellm_fix():
    """Validate that LiteLLM integration is working correctly"""
    
    print("=== LiteLLM Fix Validation ===")
    
    llm = LLMHandler(temperature=0.0)
    
    # Test case 1: Simple extraction
    test_prompt = """
    Analyze: "Participants expressed concern about AI impact"
    Extract one code with description and frequency.
    """
    
    try:
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=OpenCode
        )
        print(f"PASS: Simple extraction successful: {result}")
        
        # Validate required fields
        assert hasattr(result, 'code_name'), "Missing 'code_name' field"
        assert hasattr(result, 'description'), "Missing 'description' field" 
        assert hasattr(result, 'properties'), "Missing 'properties' field"
        assert hasattr(result, 'dimensions'), "Missing 'dimensions' field"
        assert hasattr(result, 'supporting_quotes'), "Missing 'supporting_quotes' field"
        assert hasattr(result, 'frequency'), "Missing 'frequency' field"
        assert hasattr(result, 'confidence'), "Missing 'confidence' field"
        
        # Validate field types
        assert isinstance(result.code_name, str), "code_name must be string"
        assert isinstance(result.description, str), "description must be string"
        assert isinstance(result.properties, list), "properties must be list"
        assert isinstance(result.dimensions, list), "dimensions must be list"
        assert isinstance(result.supporting_quotes, list), "supporting_quotes must be list"
        assert isinstance(result.frequency, int), "frequency must be integer"
        assert isinstance(result.confidence, float), "confidence must be float"
        
        print("PASS: All field validation passed")
        
        # Test case 2: Multiple extraction attempts for consistency
        print("\n=== Testing Consistency ===")
        for i in range(3):
            result2 = await llm.extract_structured(
                prompt=test_prompt,
                schema=OpenCode
            )
            print(f"PASS: Extraction {i+1} successful: {result2.code_name}")
        
        print("PASS: Multiple extractions successful")
        return True
        
    except Exception as e:
        print(f"FAIL: LiteLLM fix validation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_litellm_fix())
    exit(0 if success else 1)