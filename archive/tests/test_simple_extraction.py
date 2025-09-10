"""Test with a much simpler extraction to isolate the issue"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.llm.llm_handler import LLMHandler
from pydantic import BaseModel
from typing import List

class SimpleQuote(BaseModel):
    text: str
    codes: List[str]

class SimpleExtraction(BaseModel):
    quotes: List[SimpleQuote]
    
async def test_simple():
    """Test simple extraction on interview content"""
    
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    # Take a small chunk of the interview
    interview_chunk = """
    Todd Helmus: How do you use AI in your research?
    
    Joie Acosta: I use AI for transcription mostly. It saves me a lot of time compared to manual transcription. 
    But I worry about accuracy sometimes, especially with technical terms.
    
    Todd Helmus: What about for analysis?
    
    Joie Acosta: I've tried using it for thematic coding, but it misses nuance. The AI doesn't understand 
    context the way a human researcher does. It's good for initial passes but needs human review.
    """
    
    prompt = f"""
    Extract quotes from this interview about AI in research.
    
    Available codes:
    - AI for Transcription
    - Efficiency Benefits
    - Accuracy Concerns
    - AI for Analysis
    - Loss of Nuance
    - Human Review Needed
    
    For each quote, assign ALL relevant codes (quotes often relate to multiple codes).
    
    Interview:
    {interview_chunk}
    """
    
    try:
        print("Testing simple extraction...")
        result = await llm.extract_structured(
            prompt=prompt,
            schema=SimpleExtraction,
            max_tokens=None
        )
        
        print(f"\nExtracted {len(result.quotes)} quotes:")
        for i, quote in enumerate(result.quotes, 1):
            print(f"\n{i}. '{quote.text[:50]}...'")
            print(f"   Codes: {quote.codes}")
            print(f"   Number of codes: {len(quote.codes)}")
        
        # Check for many-to-many
        multi_code = sum(1 for q in result.quotes if len(q.codes) > 1)
        print(f"\nQuotes with multiple codes: {multi_code}/{len(result.quotes)}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())