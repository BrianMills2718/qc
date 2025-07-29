#!/usr/bin/env python3
"""
Run full AI interviews analysis (all 18 files)
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.better_global_analyzer import BetterGlobalAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('full_ai_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def run_full_analysis():
    """Run analysis on all 18 AI interviews."""
    logger.info("="*60)
    logger.info("Starting FULL AI Interviews Analysis")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("="*60)
    
    analyzer = BetterGlobalAnalyzer()
    
    try:
        # Run full analysis (no sample_size parameter)
        logger.info(f"Analyzing all {len(analyzer.interview_files)} AI interviews...")
        result = await analyzer.analyze_global()
        
        # Export results
        output_dir = project_root / "output" / f"full_ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        analyzer.export_results(result, output_dir)
        
        # Print detailed summary
        print(f"\n{'='*60}")
        print("FULL AI INTERVIEWS ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"\nINTERVIEWS ANALYZED: {result['metadata']['interviews_analyzed']}")
        print(f"TOTAL TOKENS: {result['metadata']['total_tokens']:,}")
        print(f"PROCESSING TIME: {result['metadata']['processing_time_seconds']:.1f} seconds")
        
        print(f"\nTHEMES FOUND: {len(result['global_analysis'].themes)}")
        for theme in result['global_analysis'].themes:
            print(f"  - {theme.theme_id}: {theme.name} (prevalence: {theme.prevalence:.0%})")
        
        print(f"\nCODES IDENTIFIED: {len(result['global_analysis'].codes)}")
        print(f"TOP 10 CODES BY FREQUENCY:")
        sorted_codes = sorted(result['global_analysis'].codes, 
                            key=lambda c: c.frequency, reverse=True)[:10]
        for code in sorted_codes:
            print(f"  - {code.name}: {code.frequency} occurrences")
        
        print(f"\nQUOTES EXTRACTED: {len(result['quote_inventory'])}")
        print(f"QUOTE CHAINS: {len(result['global_analysis'].quote_chains)}")
        
        saturation = result['global_analysis'].saturation_assessment
        print(f"\nTHEORETICAL SATURATION:")
        print(f"  - Reached at: Interview {saturation.interview_number}")
        print(f"  - Evidence: {saturation.evidence}")
        
        print(f"\nEMERGENT THEORY:")
        print(f"{result['global_analysis'].emergent_theory}")
        
        print(f"\n{'='*60}")
        print(f"Results exported to: {output_dir}")
        print(f"{'='*60}\n")
        
        # Create summary report
        summary_path = output_dir / "SUMMARY.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"AI INTERVIEWS ANALYSIS SUMMARY\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"{'='*60}\n\n")
            f.write(f"Interviews Analyzed: {result['metadata']['interviews_analyzed']}\n")
            f.write(f"Total Tokens: {result['metadata']['total_tokens']:,}\n")
            f.write(f"Processing Time: {result['metadata']['processing_time_seconds']:.1f} seconds\n")
            f.write(f"Themes: {len(result['global_analysis'].themes)}\n")
            f.write(f"Codes: {len(result['global_analysis'].codes)}\n")
            f.write(f"Quotes: {len(result['quote_inventory'])}\n")
            f.write(f"\nResearch Question:\n{analyzer.research_question}\n")
            f.write(f"\nEmergent Theory:\n{result['global_analysis'].emergent_theory}\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await run_full_analysis()
    
    if success:
        print("\n[SUCCESS] FULL AI INTERVIEWS ANALYSIS COMPLETED SUCCESSFULLY!")
    else:
        print("\n[FAILED] ANALYSIS FAILED - Check logs for details")


if __name__ == "__main__":
    asyncio.run(main())