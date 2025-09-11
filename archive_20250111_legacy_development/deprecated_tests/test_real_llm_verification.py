#!/usr/bin/env python3
"""
Test that LLM is actually working and generating real codes (not fallback)
"""
import asyncio
from src.qc.llm.llm_handler import LLMHandler

async def test_llm_connectivity():
    """Quick test to verify LLM is responding"""
    print("=" * 60)
    print("TESTING REAL LLM CONNECTIVITY")
    print("=" * 60)
    
    # Initialize LLM handler
    llm = LLMHandler(
        model_name="gemini/gemini-2.5-flash",
        temperature=0.1,
        max_retries=3
    )
    
    # Simple test prompt
    test_prompt = "Generate a JSON with one field 'status' set to 'working'. Return only valid JSON."
    
    try:
        response = await llm.complete_raw(test_prompt)
        print(f"\n[OK] LLM Response received: {response[:100]}...")
        
        # Check if it's actual LLM response or fallback
        if "working" in response.lower():
            print("[SUCCESS] Real LLM is responding correctly")
            return True
        else:
            print("[WARNING] Unexpected response - might be fallback")
            return False
            
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_connectivity())
    if success:
        print("\nLLM is ready for testing the analyze command")
    else:
        print("\nLLM is not available - tests will use fallback data")
    exit(0 if success else 1)