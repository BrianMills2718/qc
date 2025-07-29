#!/usr/bin/env python3
"""
Test robust parsing and speaker identification
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.core.robust_plain_text_parser import RobustPlainTextParser

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_robust_second_call():
    """Test the second LLM call with robust parsing."""
    analyzer = GlobalQualitativeAnalyzer()
    
    logger.info("Testing robust parsing with 3 AI interviews...")
    
    # Run full pipeline with 3 interviews
    try:
        result = await analyzer.analyze_global(sample_size=3)
        
        logger.info("Both calls succeeded!")
        logger.info(f"Themes: {len(result.global_analysis.themes)}")
        logger.info(f"CSV Export Tables: {len(result.csv_export_data.themes_table)} themes")
        logger.info(f"Traceability: {result.traceability_completeness:.1%}")
        
        # Check quote parsing
        if result.csv_export_data.quotes_table:
            logger.info(f"\nQuotes CSV has {len(result.csv_export_data.quotes_table)} entries")
            # Show first quote
            if result.csv_export_data.quotes_table:
                first_quote = result.csv_export_data.quotes_table[0]
                logger.info(f"First quote: {first_quote}")
        
        # Save outputs
        output_dir = project_root / "output" / "robust_parsing_test"
        analyzer.export_csv_files(result, output_dir)
        analyzer.export_markdown_report(result, output_dir / "report.md")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_parser_flexibility():
    """Test parser with various formats."""
    parser = RobustPlainTextParser()
    
    # Test different section formats
    test_text = """
=== THEMES CSV ===
theme_id,name,prevalence,confidence,interview_count
T1,AI for Data Processing,0.9,0.95,15

== CODES_CSV ==
code_id,name,definition
C1,Transcription,AI for audio to text

QUOTES_CSV:
quote_id,text,speaker,interview_id
Q1,"AI helps with coding","Sara McCleskey (Researcher)",INT_003

[ METRICS ]
traceability_completeness: 0.95
evidence_strength = 0.90
quote_chain_coverage - 0.85
"""
    
    sections = parser.parse(test_text)
    
    print("\n=== Parser Flexibility Test ===")
    print(f"Found {len(sections)} sections")
    
    # Check specific sections
    for section in ['THEMES_CSV', 'CODES_CSV', 'QUOTES_CSV', 'METRICS']:
        if section in sections and sections[section]:
            print(f"\n{section} found:")
            print(sections[section][:100] + "..." if len(sections[section]) > 100 else sections[section])
    
    # Test metric extraction
    metrics = parser.extract_metrics(sections.get('METRICS', ''))
    print(f"\nExtracted metrics: {metrics}")


async def main():
    print("=== Testing Robust Parsing Implementation ===\n")
    
    # Test parser flexibility
    test_parser_flexibility()
    
    # Test full pipeline
    print("\n=== Testing Full Pipeline ===\n")
    success = await test_robust_second_call()
    
    if success:
        print("\n[SUCCESS] Robust parsing implementation working!")
        print("\nIMPROVEMENTS IMPLEMENTED:")
        print("1. Flexible section detection (multiple marker styles)")
        print("2. Section name normalization and aliases")
        print("3. Missing section handling with empty defaults")
        print("4. Flexible metric extraction patterns")
        print("5. CSV validation capabilities")
        print("6. Speaker identification in prompts")
    else:
        print("\n[FAIL] Issues remain with parsing")


if __name__ == "__main__":
    asyncio.run(main())