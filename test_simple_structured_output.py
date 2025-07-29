#!/usr/bin/env python3
"""
Test with a simpler Pydantic model to isolate the structured output issue
"""
import asyncio
import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.simple_gemini_client import SimpleGeminiClient

class SimpleTheme(BaseModel):
    """Simple theme model for testing structured output"""
    theme_id: str = Field(description="Unique theme identifier")
    name: str = Field(description="Theme name")
    description: str = Field(description="Theme description")
    prevalence: float = Field(description="Proportion of interviews (0.0-1.0)")

class SimpleResult(BaseModel):
    """Simple result model for testing"""
    research_question: str = Field(description="The research question")
    themes: List[SimpleTheme] = Field(description="List of themes found")
    total_interviews: int = Field(description="Number of interviews analyzed")

async def test_simple_structured_output():
    """Test structured output with a simple model"""
    
    client = SimpleGeminiClient()
    
    # Simple test prompt
    prompt = """Analyze this interview excerpt about AI methods in qualitative research:

Interview 001: "I think AI could be really helpful for coding qualitative data. We spend so much time doing manual coding, and AI could speed that up. But I'm worried about accuracy - can AI really understand the nuances of human experience?"

Create a SimpleResult analyzing this interview for themes about AI assistance in qualitative research."""
    
    # Configure for structured output
    generation_config = {
        'temperature': 0.3,
        'max_output_tokens': 5000,
        'response_mime_type': 'application/json',
        'response_schema': SimpleResult
    }
    
    try:
        print("Testing simple structured output...")
        response = await client.extract_themes(
            prompt,
            generation_config=generation_config
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        
        # Handle case where LLM wraps response in extra layer
        if isinstance(response, dict) and 'SimpleResult' in response:
            print("WARNING: Response wrapped in extra layer, unwrapping...")
            response = response['SimpleResult']
        
        # Try to create SimpleResult
        result = SimpleResult(**response)
        print(f"SUCCESS: Created SimpleResult with {len(result.themes)} themes")
        print(f"Research question: {result.research_question}")
        print(f"First theme: {result.themes[0].name if result.themes else 'No themes'}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_structured_output())
    if success:
        print("\nSimple structured output is working correctly!")
    else:
        print("\nSimple structured output has issues")