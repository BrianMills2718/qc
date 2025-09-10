"""Test structured output with gemini-2.5-flash"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.llm.llm_handler import LLMHandler
from pydantic import BaseModel
from typing import List

class SimpleTest(BaseModel):
    """Simple test schema"""
    name: str
    age: int
    tags: List[str]
    
async def test_structured_output():
    """Test if structured output works properly with gemini-2.5-flash"""
    
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    prompt = """
    Extract information about this person:
    John Smith is 35 years old. He is a software engineer who likes hiking and reading.
    """
    
    try:
        print("Testing structured output with gemini-2.5-flash...")
        result = await llm.extract_structured(
            prompt=prompt,
            schema=SimpleTest,
            max_tokens=None
        )
        
        print(f"SUCCESS! Got structured output:")
        print(f"  Name: {result.name}")
        print(f"  Age: {result.age}")
        print(f"  Tags: {result.tags}")
        print(f"  Type: {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_structured_output())
    exit(0 if success else 1)