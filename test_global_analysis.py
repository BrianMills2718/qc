"""
Test script for LLM-native global analysis approach.

Tests with 10 interviews first, then optionally with full dataset.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import (
    GlobalQualitativeAnalyzer,
    test_with_sample,
    analyze_full_dataset
)


async def main():
    """Run tests for global analysis."""
    print("=== Testing LLM-Native Global Analysis ===\n")
    
    # Test 1: Small sample (10 interviews)
    print("Test 1: Analyzing 10 interview sample...")
    print("-" * 50)
    
    try:
        sample_result = await test_with_sample()
        
        print(f"\nSample Analysis Results:")
        print(f"- Themes found: {len(sample_result.global_analysis.themes)}")
        print(f"- Codes identified: {len(sample_result.global_analysis.codes)}")
        print(f"- Quote chains: {len(sample_result.global_analysis.quote_chains)}")
        print(f"- Contradictions: {len(sample_result.global_analysis.contradictions)}")
        print(f"- Traceability: {sample_result.traceability_completeness:.1%}")
        print(f"- Processing time: {sample_result.global_analysis.processing_metadata['processing_time_seconds']:.1f}s")
        
        # Show some themes
        print(f"\nTop 3 Themes:")
        for i, theme in enumerate(sample_result.global_analysis.themes[:3], 1):
            print(f"{i}. {theme.name} (prevalence: {theme.prevalence:.1%})")
            print(f"   {theme.description}")
        
        print(f"\nResults exported to: output/global_analysis_sample/")
        
    except Exception as e:
        print(f"ERROR in sample analysis: {str(e)}")
        return
    
    # Ask if user wants to run full analysis
    print("\n" + "=" * 50)
    response = input("\nRun full analysis on all 103 interviews? (y/n): ")
    
    if response.lower() == 'y':
        print("\nTest 2: Analyzing all 103 interviews...")
        print("-" * 50)
        
        try:
            full_result = await analyze_full_dataset()
            
            print(f"\nFull dataset analysis complete!")
            print(f"Results exported to: output/global_analysis_full/")
            
        except Exception as e:
            print(f"ERROR in full analysis: {str(e)}")
    else:
        print("\nSkipping full analysis.")
    
    print("\n=== Testing Complete ===")


if __name__ == "__main__":
    # Check for API key
    import os
    if not os.getenv('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("Please set it before running: set GEMINI_API_KEY=your-key-here")
        sys.exit(1)
    
    # Run the tests
    asyncio.run(main())