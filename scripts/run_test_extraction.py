"""
Run the code-first extraction pipeline on 5 test interviews
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'extraction_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_extraction():
    """Run the extraction pipeline"""
    
    print("="*80)
    print("CODE-FIRST EXTRACTION PIPELINE - TEST RUN")
    print("="*80)
    
    # Load configuration from YAML
    config_file = "extraction_config_test.yaml"
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Create extraction config
    config = ExtractionConfig(
        analytic_question=config_data['analytic_question'],
        interview_files=config_data['interview_files'],
        coding_approach=ExtractionApproach[config_data['coding_approach'].upper()],
        speaker_approach=ExtractionApproach[config_data['speaker_approach'].upper()],
        entity_approach=ExtractionApproach[config_data['entity_approach'].upper()],
        output_dir=config_data['output_dir'],
        code_hierarchy_depth=config_data['code_hierarchy_depth'],
        llm_model=config_data['llm_model'],
        max_concurrent_interviews=config_data.get('max_concurrent_interviews', 3),
        auto_import_neo4j=config_data['auto_import_neo4j']
    )
    
    print(f"\n[CONFIG] Configuration:")
    print(f"  - Analytic Question: {config.analytic_question}")
    print(f"  - Number of Interviews: {len(config.interview_files)}")
    print(f"  - Coding Approach: {config.coding_approach.value}")
    print(f"  - Output Directory: {config.output_dir}")
    print(f"  - LLM Model: {config.llm_model}")
    print(f"  - Max Concurrent: {config.max_concurrent_interviews}")
    
    print("\n[FILES] Interview Files:")
    for i, file in enumerate(config.interview_files, 1):
        filename = Path(file).name
        print(f"  {i}. {filename}")
    
    print("\n" + "="*80)
    print("STARTING EXTRACTION PIPELINE")
    print("="*80)
    
    try:
        # Create extractor
        extractor = CodeFirstExtractor(config)
        
        # Run extraction
        print("\n[START] Starting 4-phase extraction process...")
        start_time = datetime.now()
        
        results = await extractor.run_extraction()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "="*80)
        print("EXTRACTION COMPLETE")
        print("="*80)
        
        print(f"\n[RESULTS] Results Summary:")
        print(f"  - Total Codes Discovered: {results.code_taxonomy.total_codes}")
        print(f"  - Code Hierarchy Depth: {results.code_taxonomy.hierarchy_depth}")
        print(f"  - Speaker Properties Discovered: {len(results.speaker_schema.properties)}")
        print(f"  - Entity Types Discovered: {len(results.entity_schema.entity_types)}")
        print(f"  - Relationship Types Discovered: {len(results.entity_schema.relationship_types)}")
        print(f"  - Total Interviews Processed: {len(results.coded_interviews)}")
        
        # Count total quotes
        total_quotes = sum(interview.total_quotes for interview in results.coded_interviews)
        print(f"  - Total Quotes Extracted: {total_quotes}")
        
        # Count quotes with codes
        quotes_with_codes = 0
        for interview in results.coded_interviews:
            for quote in interview.quotes:
                if quote.code_ids:
                    quotes_with_codes += 1
        print(f"  - Quotes with Codes: {quotes_with_codes}/{total_quotes}")
        
        print(f"\n[TIME] Processing Time: {duration}")
        print(f"  - Average per interview: {duration.total_seconds()/len(config.interview_files):.1f} seconds")
        
        print(f"\n[SAVED] Results saved to: {config.output_dir}/")
        
        # Show sample codes
        print("\n[CODES] Sample Codes Discovered:")
        for i, code in enumerate(results.code_taxonomy.codes[:5], 1):
            indent = "  " * code.level
            print(f"  {i}. {indent}[{code.id}] {code.name}")
        if len(results.code_taxonomy.codes) > 5:
            print(f"  ... and {len(results.code_taxonomy.codes) - 5} more codes")
        
        return results
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        print(f"\nERROR: ERROR: {e}")
        return None

def main():
    """Main entry point"""
    print("\n[CHECK] Checking configuration file...")
    
    config_file = Path("extraction_config_test.yaml")
    if not config_file.exists():
        print("ERROR: ERROR: extraction_config_test.yaml not found!")
        print("Please ensure the configuration file exists.")
        return
    
    print("OK: Configuration file found")
    
    # Check for environment variables
    import os
    if not os.getenv('GEMINI_API_KEY'):
        print("\nWARNING: WARNING: GEMINI_API_KEY not found in environment variables")
        print("Please ensure you have set: export GEMINI_API_KEY='your-key-here'")
        print("Or add it to your .env file")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run the extraction
    results = asyncio.run(run_extraction())
    
    if results:
        print("\nOK: Extraction completed successfully!")
        print(f"Check the {results.output_dir}/ directory for:")
        print("  - taxonomy.json (code structure)")
        print("  - speaker_schema.json (speaker properties)")
        print("  - entity_schema.json (entity/relationship types)")
        print("  - coded_interviews/ (individual interview results)")
    else:
        print("\nERROR: Extraction failed. Check the log file for details.")

if __name__ == "__main__":
    main()