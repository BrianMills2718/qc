#!/usr/bin/env python3
"""
Test script to reproduce Pydantic validation issues in analytical memo generation
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.analysis.analytical_memos import AnalyticalMemoGenerator, MemoType
from src.qc.llm.llm_handler import LLMHandler

async def test_memo_validation():
    """Test analytical memo generation and capture validation errors"""
    
    print("Testing Analytical Memo Generation...")
    print("=" * 50)
    
    # Initialize LLM handler
    try:
        llm_handler = LLMHandler()
        print("[OK] LLM Handler initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize LLM Handler: {e}")
        return False
    
    # Initialize memo generator
    memo_generator = AnalyticalMemoGenerator(llm_handler)
    
    # Test with minimal sample data (correct format for memo generator)
    sample_data = [
        {
            "interview_id": "test_interview_1",
            "quotes": [
                {
                    "id": "test_quote_1", 
                    "text": "This is a test quote about project management challenges",
                    "code_names": ["project_management", "challenges"]
                },
                {
                    "id": "test_quote_2",
                    "text": "Another quote about team collaboration issues",
                    "code_names": ["collaboration", "issues"]
                }
            ]
        }
    ]
    
    try:
        # Test pattern analysis memo generation
        print(f"Generating memo: {MemoType.PATTERN_ANALYSIS.value}")
        
        memo = await memo_generator.generate_pattern_analysis_memo(
            interview_data=sample_data,
            focus_codes=["project_management", "challenges"],
            memo_title="Test Pattern Analysis"
        )
        
        print("[SUCCESS] Memo generated successfully!")
        print(f"Memo type: {memo.memo_type}")
        print(f"Title: {memo.title}")
        print(f"Patterns found: {len(memo.patterns)}")
        
    except Exception as e:
        print(f"[ERROR] Error during memo generation: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Print more detailed error info
        import traceback
        print("\nDetailed error trace:")
        traceback.print_exc()
        
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_memo_validation())
    exit(0 if success else 1)