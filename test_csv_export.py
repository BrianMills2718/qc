#!/usr/bin/env python3
"""
Test CSV export functionality
"""
import asyncio
import logging
import sys
from pathlib import Path
import csv
import io

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_csv_string(csv_string: str) -> list:
    """Parse CSV string into list of dicts."""
    if not csv_string.strip():
        return []
    reader = csv.DictReader(io.StringIO(csv_string))
    return list(reader)


async def test_csv_export():
    """Test CSV export functionality."""
    analyzer = GlobalQualitativeAnalyzer()
    
    logger.info("Starting CSV export test...")
    
    try:
        # Run analysis with 3 interviews
        result = await analyzer.analyze_global(sample_size=3)
        
        logger.info("Analysis completed, checking CSV exports...")
        
        # Check if we have CSV data
        if hasattr(result, 'csv_export_data') and result.csv_export_data:
            csv_data = result.csv_export_data
            
            # Test themes CSV
            if hasattr(csv_data, 'themes_csv'):
                themes = parse_csv_string(csv_data.themes_csv)
                logger.info(f"Themes CSV: {len(themes)} rows")
                if themes:
                    logger.info(f"Columns: {list(themes[0].keys())}")
                    logger.info(f"First theme: {themes[0]['name'] if 'name' in themes[0] else 'N/A'}")
            
            # Test codes CSV
            if hasattr(csv_data, 'codes_csv'):
                codes = parse_csv_string(csv_data.codes_csv)
                logger.info(f"Codes CSV: {len(codes)} rows")
                if codes:
                    logger.info(f"Columns: {list(codes[0].keys())}")
            
            # Test quotes CSV
            if hasattr(csv_data, 'quotes_csv'):
                quotes = parse_csv_string(csv_data.quotes_csv)
                logger.info(f"Quotes CSV: {len(quotes)} rows")
                if quotes:
                    logger.info(f"Columns: {list(quotes[0].keys())}")
                    # Check if quotes have proper interview IDs
                    unique_interviews = set(q.get('interview_id', '') for q in quotes)
                    logger.info(f"Unique interview IDs in quotes: {unique_interviews}")
            
            # Save CSV files
            output_dir = project_root / "output" / "csv_test"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save each CSV
            csv_files = [
                ('themes', csv_data.themes_csv if hasattr(csv_data, 'themes_csv') else ''),
                ('codes', csv_data.codes_csv if hasattr(csv_data, 'codes_csv') else ''),
                ('quotes', csv_data.quotes_csv if hasattr(csv_data, 'quotes_csv') else ''),
                ('quote_chains', csv_data.quote_chains_csv if hasattr(csv_data, 'quote_chains_csv') else ''),
                ('contradictions', csv_data.contradictions_csv if hasattr(csv_data, 'contradictions_csv') else ''),
                ('stakeholder_positions', csv_data.stakeholder_positions_csv if hasattr(csv_data, 'stakeholder_positions_csv') else '')
            ]
            
            for name, content in csv_files:
                if content:
                    file_path = output_dir / f"{name}.csv"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Saved {name}.csv")
            
            return True
        else:
            logger.error("No CSV export data found in result")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_csv_export()
    if success:
        print("\n✅ CSV export test PASSED!")
    else:
        print("\n❌ CSV export test FAILED!")


if __name__ == "__main__":
    asyncio.run(main())