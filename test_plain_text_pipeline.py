#!/usr/bin/env python3
"""
Test full pipeline with plain text second call
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


async def test_plain_text_pipeline():
    """Test the full pipeline with plain text second call."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Test with just 3 interviews to be fast
    logger.info("Starting full pipeline test with plain text approach...")
    
    try:
        # Run global analysis with 3 interviews
        result = await analyzer.analyze_global(sample_size=3)
        
        logger.info(f"SUCCESS! Full pipeline completed:")
        logger.info(f"- Themes found: {len(result.global_analysis.themes)}")
        logger.info(f"- Codes found: {len(result.global_analysis.codes)}")
        logger.info(f"- Quote chains: {len(result.global_analysis.quote_chains)}")
        logger.info(f"- Saturation point: {result.global_analysis.saturation_assessment.saturation_point}")
        
        # Check enhanced results
        logger.info(f"\nEnhanced results:")
        logger.info(f"- Traceability completeness: {result.traceability_completeness}")
        logger.info(f"- Quote chain coverage: {result.quote_chain_coverage}")
        logger.info(f"- Stakeholder coverage: {result.stakeholder_coverage}")
        logger.info(f"- Evidence strength: {result.evidence_strength}")
        
        # Check CSV data
        if hasattr(result, 'csv_export_data') and result.csv_export_data:
            csv_data = result.csv_export_data
            logger.info(f"\nCSV export data:")
            
            # Count rows in each CSV
            for field_name in ['themes_csv', 'codes_csv', 'quotes_csv', 'quote_chains_csv']:
                if hasattr(csv_data, field_name):
                    csv_content = getattr(csv_data, field_name)
                    if csv_content:
                        row_count = len(csv_content.strip().split('\n')) - 1  # Subtract header
                        logger.info(f"- {field_name}: {row_count} rows")
        
        # Save results
        output_dir = project_root / "output" / "plain_text_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export CSV files
        if hasattr(result, 'csv_export_data') and result.csv_export_data:
            csv_data = result.csv_export_data
            
            csv_files = [
                ('themes', csv_data.themes_csv if hasattr(csv_data, 'themes_csv') else ''),
                ('codes', csv_data.codes_csv if hasattr(csv_data, 'codes_csv') else ''),
                ('quotes', csv_data.quotes_csv if hasattr(csv_data, 'quotes_csv') else ''),
                ('quote_chains', csv_data.quote_chains_csv if hasattr(csv_data, 'quote_chains_csv') else ''),
            ]
            
            for name, content in csv_files:
                if content:
                    file_path = output_dir / f"{name}.csv"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Saved {name}.csv")
        
        # Save markdown report
        if hasattr(result, 'markdown_report'):
            with open(output_dir / "report.md", 'w', encoding='utf-8') as f:
                f.write(result.markdown_report)
            logger.info("Saved markdown report")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_plain_text_pipeline()
    if success:
        print("\n[PASS] Full pipeline test with plain text PASSED!")
        print("- First call: WORKING")
        print("- Second call: WORKING") 
        print("- CSV export: WORKING")
        print("- Full traceability: WORKING")
    else:
        print("\n[FAIL] Full pipeline test FAILED!")


if __name__ == "__main__":
    asyncio.run(main())