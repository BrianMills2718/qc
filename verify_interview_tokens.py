#!/usr/bin/env python3
"""
Verify all 103 interviews fit within 1M token context window for LLM-native approach.
Tests the feasibility of global analysis.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from qc.parsing.docx_parser import DOCXParser
from qc.utils.token_counter import TokenCounter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_global_analysis_feasibility():
    """
    Load all 103 interviews and verify they fit in 1M token context.
    """
    print("=" * 80)
    print("VERIFYING GLOBAL ANALYSIS FEASIBILITY FOR 103 INTERVIEWS")
    print("=" * 80)
    print()
    
    # Initialize components
    parser = DOCXParser()
    counter = TokenCounter()
    
    # Find all interview directories
    interview_base = Path("C:/Users/Brian/projects/qualitative_coding_clean/data/interviews")
    
    if not interview_base.exists():
        print(f"ERROR: Interview directory not found: {interview_base}")
        return
    
    # Collect all DOCX files
    all_interview_files = []
    
    # AI Interviews
    ai_path = interview_base / "AI_Interviews_all_2025.0728" / "Interviews"
    if ai_path.exists():
        ai_files = list(ai_path.glob("*.docx"))
        all_interview_files.extend(ai_files)
        print(f"Found {len(ai_files)} AI interview files")
    
    # Africa Interviews
    africa_path = interview_base / "africa_interveiws_alll_2025.0728" / "For Brian_cleaned notes"
    if africa_path.exists():
        africa_files = list(africa_path.glob("*.docx"))
        all_interview_files.extend(africa_files)
        print(f"Found {len(africa_files)} Africa interview files")
    
    print(f"\nTotal interview files found: {len(all_interview_files)}")
    print("-" * 80)
    
    # Parse all interviews and count tokens
    total_tokens = 0
    total_words = 0
    successful_parses = 0
    failed_parses = 0
    interview_tokens = []
    
    print("\nProcessing interviews...")
    
    for i, file_path in enumerate(all_interview_files, 1):
        try:
            # Parse the interview
            result = parser.parse_interview_file(file_path)
            
            if result['parsing_info']['success']:
                # Get accurate token count
                actual_tokens = counter.count_tokens(result['content'])
                
                # Add metadata markers (as shown in llm_native_approach.md)
                metadata_prefix = f"""
=== INTERVIEW {i:03d}: {result['metadata']['file_name']} ===
WORD_COUNT: {result['metadata']['word_count']}
SOURCE: {result['metadata']['file_path']}

"""
                metadata_suffix = f"\n\n=== END INTERVIEW {i:03d} ===\n"
                
                # Count tokens including metadata
                metadata_tokens = counter.count_tokens(metadata_prefix + metadata_suffix)
                total_interview_tokens = actual_tokens + metadata_tokens
                
                total_tokens += total_interview_tokens
                total_words += result['metadata']['word_count']
                successful_parses += 1
                
                interview_tokens.append({
                    'file': file_path.name,
                    'words': result['metadata']['word_count'],
                    'tokens': total_interview_tokens
                })
                
                # Progress indicator
                if i % 10 == 0:
                    print(f"  Processed {i}/{len(all_interview_files)} interviews...")
                    
            else:
                failed_parses += 1
                logger.warning(f"Failed to parse: {file_path.name}")
                
        except Exception as e:
            failed_parses += 1
            logger.error(f"Error processing {file_path.name}: {str(e)}")
    
    print(f"\nProcessing complete!")
    print("-" * 80)
    
    # Analysis results
    print("\n📊 GLOBAL ANALYSIS FEASIBILITY REPORT")
    print("=" * 80)
    
    print(f"\n✅ Successfully parsed: {successful_parses} interviews")
    print(f"❌ Failed to parse: {failed_parses} interviews")
    
    print(f"\n📝 Content Statistics:")
    print(f"   Total words: {total_words:,}")
    print(f"   Total tokens (with metadata): {total_tokens:,}")
    print(f"   Average tokens per interview: {total_tokens/successful_parses:,.0f}")
    
    # Check feasibility
    print(f"\n🎯 Global Analysis Feasibility:")
    
    # Account for prompt overhead
    prompt_overhead = 5000  # Conservative estimate for comprehensive prompt
    total_with_prompt = total_tokens + prompt_overhead
    
    print(f"   Total tokens with prompt: {total_with_prompt:,}")
    print(f"   Gemini 2.5 Flash limit: 1,048,576 tokens")
    print(f"   Conservative limit (900K): 900,000 tokens")
    
    if total_with_prompt < 900_000:
        print(f"\n✅ FEASIBLE: All {successful_parses} interviews fit within 900K token limit!")
        print(f"   Remaining capacity: {900_000 - total_with_prompt:,} tokens ({((900_000 - total_with_prompt)/900_000)*100:.1f}%)")
    else:
        print(f"\n❌ NOT FEASIBLE: Exceeds 900K token limit by {total_with_prompt - 900_000:,} tokens")
        print(f"   Would need to process in batches or use systematic approach")
    
    # Find largest interviews
    if interview_tokens:
        interview_tokens.sort(key=lambda x: x['tokens'], reverse=True)
        
        print(f"\n📈 Largest Interviews:")
        for i, interview in enumerate(interview_tokens[:5], 1):
            print(f"   {i}. {interview['file']}: {interview['tokens']:,} tokens ({interview['words']:,} words)")
        
        print(f"\n📉 Smallest Interviews:")
        for i, interview in enumerate(interview_tokens[-5:], 1):
            print(f"   {i}. {interview['file']}: {interview['tokens']:,} tokens ({interview['words']:,} words)")
    
    # Estimate LLM costs
    print(f"\n💰 Cost Estimates (Gemini 2.5 Flash):")
    input_cost_per_million = 0.30  # $0.30 per 1M input tokens
    output_cost_per_million = 2.50  # $2.50 per 1M output tokens
    
    # For 2-call global analysis
    call1_input = total_with_prompt
    call1_output = 60_000  # Max output for comprehensive analysis
    call2_input = call1_output + 5_000  # Previous result + refinement prompt
    call2_output = 60_000  # Max output for enhanced traceability
    
    total_input_tokens = call1_input + call2_input
    total_output_tokens = call1_output + call2_output
    
    input_cost = (total_input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (total_output_tokens / 1_000_000) * output_cost_per_million
    total_cost = input_cost + output_cost
    
    print(f"   Input tokens: {total_input_tokens:,} (${input_cost:.3f})")
    print(f"   Output tokens: {total_output_tokens:,} (${output_cost:.3f})")
    print(f"   Total estimated cost: ${total_cost:.2f}")
    
    # Compare with systematic approach
    print(f"\n📊 Comparison with Systematic Three-Phase Approach:")
    systematic_calls = successful_parses * 3  # 3 phases per interview
    systematic_input = total_tokens * 3  # Same content processed 3 times
    systematic_output = successful_parses * 60_000  # Conservative output estimate
    
    systematic_input_cost = (systematic_input / 1_000_000) * input_cost_per_million
    systematic_output_cost = (systematic_output / 1_000_000) * output_cost_per_million
    systematic_total_cost = systematic_input_cost + systematic_output_cost
    
    print(f"   Systematic approach: {systematic_calls} LLM calls")
    print(f"   Systematic cost: ${systematic_total_cost:.2f}")
    print(f"   Global approach: 2 LLM calls")
    print(f"   Global cost: ${total_cost:.2f}")
    print(f"   Savings: ${systematic_total_cost - total_cost:.2f} ({((systematic_total_cost - total_cost)/systematic_total_cost)*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    if total_with_prompt < 900_000:
        print("✅ Proceed with LLM-native global analysis approach (2 calls total)")
        print("   - All interviews fit comfortably within context window")
        print("   - Significant cost and time savings vs systematic approach")
        print("   - Can leverage LLM's global pattern recognition")
    else:
        print("⚠️  Consider batched approach or systematic three-phase methodology")
        print("   - Content exceeds conservative token limits")
        print("   - Would need to split into multiple batches")
    
    print("=" * 80)


if __name__ == "__main__":
    verify_global_analysis_feasibility()