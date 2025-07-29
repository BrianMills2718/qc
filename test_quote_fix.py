#!/usr/bin/env python3
"""
Quick test of the quote extraction fix
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from qc.core.simple_gemini_client import SimpleGeminiClient

async def test_simple_extraction():
    """Test the simple text generation approach."""
    client = SimpleGeminiClient()
    
    # Test with a simple prompt
    test_prompt = """Find quotes about AI challenges in this text:

"We're using AI for transcription but the accuracy isn't perfect. Sometimes it misses technical terms." - John Smith

"The main challenge is getting buy-in from leadership. They worry about data security with AI tools." - Sarah Jones

"I love how AI speeds up literature reviews, but I worry we're losing critical thinking skills." - Mike Chen

List 2 quotes about challenges:

1. First quote about AI challenges:
"[copy exact quote]"
Speaker: [name]

2. Second quote:
"[copy exact quote]"
Speaker: [name]"""

    print("Testing simple text generation...")
    response = await client.generate_text(test_prompt, temperature=0.1, max_tokens=500)
    print(f"Response:\n{response}")
    print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_simple_extraction())