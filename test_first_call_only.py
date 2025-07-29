#!/usr/bin/env python3
"""
Test just the first call to verify simplified schema works
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_first_call_only():
    """Test just the first LLM call."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Test with just 3 interviews to be fast
    logger.info("Testing first call with 3 interviews...")
    
    try:
        # Just test the first call
        from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata
        
        files_to_analyze = analyzer.interview_files[:3]
        all_interviews_text, total_tokens, metadata = load_all_interviews_with_metadata(files_to_analyze)
        
        logger.info(f"Loaded {len(metadata)} interviews with {total_tokens} tokens")
        
        # Call the comprehensive analysis
        result = await analyzer._comprehensive_global_analysis(
            all_interviews_text,
            len(metadata),
            total_tokens
        )
        
        logger.info(f"SUCCESS! First call completed:")
        logger.info(f"- Themes found: {len(result.themes)}")
        logger.info(f"- Codes found: {len(result.codes)}")
        logger.info(f"- Quote chains: {len(result.quote_chains)}")
        logger.info(f"- Saturation point: {result.saturation_assessment.saturation_point}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_first_call_only()
    if success:
        print("\n✅ First call test PASSED!")
    else:
        print("\n❌ First call test FAILED!")


if __name__ == "__main__":
    asyncio.run(main())