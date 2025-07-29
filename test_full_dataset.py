#!/usr/bin/env python3
"""
Test loading all 103 interviews and verify token count for LLM-native approach
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from qc.parsing.docx_parser import DOCXParser
from qc.utils.token_counter import TokenCounter


def test_full_dataset():
    """Load all 103 interviews and verify total tokens < 900K"""
    parser = DOCXParser()
    counter = TokenCounter()
    
    # Load AI interviews
    ai_path = Path("data/interviews/AI_Interviews_all_2025.0728/Interviews")
    africa_path = Path("data/interviews/africa_interveiws_alll_2025.0728/For Brian_cleaned notes")
    
    all_interview_texts = []
    total_files = 0
    
    print("=== Loading All 103 Interviews ===")
    
    # Load AI interviews
    if ai_path.exists():
        ai_results = parser.parse_directory(ai_path)
        ai_successful = [r for r in ai_results if r['parsing_info']['success']]
        ai_texts = [r['content'] for r in ai_successful]
        all_interview_texts.extend(ai_texts)
        total_files += len(ai_successful)
        print(f"SUCCESS: AI Interviews: {len(ai_successful)} files loaded")
    else:
        print(f"ERROR: AI Interviews directory not found: {ai_path}")
    
    # Load Africa interviews  
    if africa_path.exists():
        africa_results = parser.parse_directory(africa_path)
        africa_successful = [r for r in africa_results if r['parsing_info']['success']]
        africa_texts = [r['content'] for r in africa_successful]
        all_interview_texts.extend(africa_texts)
        total_files += len(africa_successful)
        print(f"SUCCESS: Africa Interviews: {len(africa_successful)} files loaded")
    else:
        print(f"ERROR: Africa Interviews directory not found: {africa_path}")
    
    print(f"\nTotal files loaded: {total_files}")
    
    if total_files != 103:
        print(f"WARNING: Expected 103 files, got {total_files}")
    
    # Create combined content with metadata markers for LLM-native approach
    print("\n=== Creating Combined Content for LLM-Native Analysis ===")
    
    all_content = []
    for i, text in enumerate(all_interview_texts):
        # Add metadata markers for traceability
        content_with_metadata = f"""
=== INTERVIEW {i+1:03d} ===
WORD_COUNT: {len(text.split())}
TOKEN_ESTIMATE: {counter.count_tokens(text)}

{text}

=== END INTERVIEW {i+1:03d} ===
"""
        all_content.append(content_with_metadata)
    
    # Combine all content
    full_text = "\n\n".join(all_content)
    
    # Count total tokens
    print("Counting tokens...")
    total_tokens = counter.count_tokens(full_text)
    
    print(f"\n=== Token Analysis Results ===")
    print(f"Total characters: {len(full_text):,}")
    print(f"Total words: {len(full_text.split()):,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Available context: 1,000,000 tokens")
    print(f"Remaining for prompts: {1_000_000 - total_tokens:,} tokens")
    
    # Check if it fits in context
    if total_tokens < 900_000:
        print(f"SUCCESS: Dataset fits in context window!")
        print(f"LLM-native global analysis is FEASIBLE with {900_000 - total_tokens:,} tokens to spare")
        
        # Calculate percentage of context used
        context_usage = (total_tokens / 1_000_000) * 100
        print(f"Context usage: {context_usage:.1f}%")
        
        return True, total_tokens, total_files
    else:
        print(f"FAILURE: Dataset too large for single context window")
        print(f"Exceeds limit by {total_tokens - 900_000:,} tokens")
        print(f"Will need to fall back to systematic three-phase approach")
        
        return False, total_tokens, total_files


if __name__ == "__main__":
    success, tokens, files = test_full_dataset()
    
    if success:
        print(f"\nREADY FOR DAY 1 LLM-NATIVE TESTING!")
        print(f"Next steps:")
        print(f"   1. Create comprehensive analysis models")
        print(f"   2. Implement global qualitative analyzer")
        print(f"   3. Test with 2 LLM calls total")
    else:
        print(f"\nFALLBACK TO SYSTEMATIC APPROACH REQUIRED")