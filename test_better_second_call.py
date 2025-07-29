#!/usr/bin/env python3
"""
Test a better second call approach - ask for structured data, generate CSV programmatically
"""
import asyncio
import logging
import sys
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.core.enhanced_logging import llm_logger
from qc.core.programmatic_csv_generator import CSVGenerator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_better_second_call():
    """Test second call asking for structured data instead of CSV strings."""
    analyzer = GlobalQualitativeAnalyzer()
    csv_gen = CSVGenerator()
    
    logger.info("Testing better second call approach...")
    
    # Load real data
    from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata
    files_to_analyze = analyzer.interview_files[:3]
    all_interviews_text, total_tokens, metadata = load_all_interviews_with_metadata(files_to_analyze)
    
    logger.info(f"Loaded {len(metadata)} interviews with {total_tokens} tokens")
    
    # First call
    logger.info("Running first call...")
    call_id = "call_1_comprehensive"
    start_time = llm_logger.log_call_start(call_id, "Comprehensive analysis prompt", {
        "max_output_tokens": 60000,
        "temperature": 0.3
    })
    
    initial_result = await analyzer._comprehensive_global_analysis(
        all_interviews_text,
        len(metadata),
        total_tokens
    )
    
    llm_logger.log_call_end(call_id, start_time, initial_result)
    logger.info(f"First call complete: {len(initial_result.themes)} themes, {len(initial_result.codes)} codes")
    
    # Better second call - ask for quote inventory only
    better_prompt = f"""Based on this analysis, provide a complete quote inventory.

ANALYSIS SUMMARY:
- {len(initial_result.themes)} themes found
- {len(initial_result.codes)} codes identified  
- {len(metadata)} interviews analyzed

For EACH theme and code from the analysis, provide 2-3 exemplar quotes with:
- Exact quote text including speaker identification (e.g., "Sara McCleskey (Researcher): quote here")
- Which theme(s) and code(s) the quote supports
- Brief context

Return as JSON with this structure:
{{
  "quote_inventory": [
    {{
      "quote_id": "Q001",
      "text": "Full quote with speaker identification",
      "speaker_role": "Researcher/Analyst/etc",
      "theme_ids": ["T1"],
      "code_ids": ["C001"],
      "context": "Brief context"
    }}
  ],
  "metadata": {{
    "total_quotes": 15,
    "quotes_per_theme": 3,
    "coverage": "high"
  }}
}}

Focus on quality over quantity - we need traceable, meaningful quotes."""

    generation_config = {
        'temperature': 0.2,
        'max_output_tokens': 15000,  # Much more reasonable
        'response_mime_type': 'application/json'
    }
    
    try:
        logger.info("Running better second call...")
        call_id = "call_2_quotes"
        start_time = llm_logger.log_call_start(call_id, better_prompt, generation_config)
        
        response = await analyzer.gemini_client.extract_themes(
            better_prompt,
            generation_config=generation_config
        )
        
        llm_logger.log_call_end(call_id, start_time, response)
        llm_logger.save_full_response(call_id, response)
        
        logger.info("Second call complete!")
        
        # Generate CSVs programmatically
        analysis_data = {
            'themes': [t.model_dump() for t in initial_result.themes],
            'codes': [c.model_dump() for c in initial_result.codes],
            'complete_quote_inventory': response.get('quote_inventory', [])
        }
        
        csvs = csv_gen.generate_all_csvs(analysis_data)
        
        # Save outputs
        output_dir = project_root / "output" / "better_approach"
        csv_gen.save_csvs_to_disk(csvs, output_dir)
        
        # Save the quote inventory
        with open(output_dir / "quote_inventory.json", 'w') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"\nSUCCESS! Generated {len(csvs)} CSV files programmatically")
        logger.info("This approach is much cleaner than asking LLM to generate CSV strings")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=== Testing Better Second Call Approach ===\n")
    
    success = await test_better_second_call()
    
    if success:
        print("\n[SUCCESS] Better approach works!")
        print("\nKEY IMPROVEMENTS:")
        print("1. Ask for structured data (JSON), not CSV strings")
        print("2. Generate CSVs programmatically - cleaner and more reliable")
        print("3. Reasonable output token limits (15K vs 60K)")
        print("4. Enhanced logging shows exactly what's happening")
        print("5. Focused prompts - ask for what we need, not everything")
    else:
        print("\n[FAIL] Issues with better approach")


if __name__ == "__main__":
    asyncio.run(main())