"""
Test LLM Integration - Basic Functionality Validation
"""

import asyncio
from qc_clean.core.llm.llm_handler import LLMHandler

async def test_basic_llm():
    """Test basic LLM functionality with complete_raw method"""
    print("Testing basic LLM integration...")
    
    try:
        llm = LLMHandler(model_name='gpt-4o-mini')
        response = await llm.complete_raw('Generate Cypher: MATCH (p:Person) RETURN p LIMIT 5')
        
        print(f'[SUCCESS] LLM Response: {response}')
        
        # Validation assertions
        assert response is not None, "LLM must return non-null response"
        assert len(response.strip()) > 0, "LLM must return non-empty response"
        
        print("[SUCCESS] Basic LLM integration test PASSED")
        return True
        
    except Exception as e:
        print(f"[FAILED] Basic LLM integration test FAILED: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_llm())
    exit(0 if success else 1)