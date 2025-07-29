#!/usr/bin/env python3
"""
Test Gemini structured output directly
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.simple_gemini_client import SimpleGeminiClient
from qc.models.comprehensive_analysis_models import GlobalCodingResult

async def test_structured_output():
    """Test if Gemini structured output works correctly"""
    
    client = SimpleGeminiClient()
    
    # Simple test prompt
    prompt = """Analyze this simple interview excerpt about AI methods in qualitative research:

Interview 001: "I think AI could be really helpful for coding qualitative data. We spend so much time doing manual coding, and AI could speed that up. But I'm worried about accuracy - can AI really understand the nuances of human experience?"

Create a GlobalCodingResult with at least one theme about AI assistance in qualitative research."""
    
    # Configure for structured output
    generation_config = {
        'temperature': 0.3,
        'max_output_tokens': 10000,
        'response_mime_type': 'application/json',
        'response_schema': GlobalCodingResult
    }
    
    try:
        print("Testing structured output...")
        response = await client.extract_themes(
            prompt,
            generation_config=generation_config
        )
        
        print(f"Response type: {type(response)}")
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")
        
        # Handle case where LLM wraps response in extra layer
        if isinstance(response, dict) and 'GlobalCodingResult' in response:
            print("WARNING: Response wrapped in extra layer, unwrapping...")
            response = response['GlobalCodingResult']
        
        # Try to create GlobalCodingResult
        result = GlobalCodingResult(**response)
        print(f"SUCCESS: Created GlobalCodingResult with {len(result.themes)} themes")
        print(f"First theme: {result.themes[0].name if result.themes else 'No themes'}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_structured_output())
    if success:
        print("\nStructured output is working correctly!")
    else:
        print("\nStructured output has issues")