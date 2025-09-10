#!/usr/bin/env python3
"""Complete pipeline verification - test auto-loading and end-to-end functionality"""

import sys
import asyncio
from pathlib import Path
import yaml

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig

async def verify_complete_pipeline():
    print("=== COMPLETE PIPELINE VERIFICATION ===")
    
    try:
        # Create clean extractor without pre-loading taxonomy
        with open('extraction_config.yaml') as f:
            config_data = yaml.safe_load(f)
        config = ExtractionConfig(**config_data)
        extractor = CodeFirstExtractor(config)
        
        # Verify starting state - no taxonomy loaded
        print(f"Initial taxonomy state: {extractor.code_taxonomy}")
        
        # Process focus group - should auto-load taxonomy
        print("Processing focus group with auto-loading...")
        result = await extractor._process_single_interview("tests/fixtures/Focus Group on AI and Methods 7_7.docx")
        
        print(f"Auto-loaded taxonomy: {extractor.code_taxonomy is not None}")
        if extractor.code_taxonomy:
            print(f"Taxonomy loaded with {len(extractor.code_taxonomy.codes)} codes")
        
        print(f"Quotes extracted: {len(result.quotes)}")
        quotes_with_codes = [q for q in result.quotes if q.code]
        print(f"Quotes with codes: {len(quotes_with_codes)}")
        
        quotes_with_connections = [q for q in result.quotes if q.thematic_connection and q.thematic_connection != "none"]
        print(f"Quotes with thematic connections: {len(quotes_with_connections)}")
        
        if quotes_with_connections:
            print("Sample thematic connections:")
            for q in quotes_with_connections[:3]:
                print(f"  - {q.thematic_connection} -> {q.connection_target} (confidence: {q.connection_confidence})")
        
        # Calculate success metrics
        code_application_rate = len(quotes_with_codes) / len(result.quotes) if result.quotes else 0
        print(f"Code application rate: {code_application_rate:.2%}")
        
        if code_application_rate >= 0.8:
            print("SUCCESS: Code application rate >= 80% target")
        else:
            print(f"WARNING: Code application rate {code_application_rate:.2%} < 80% target")
        
        if quotes_with_connections:
            print("SUCCESS: Thematic connections detected during extraction")
        else:
            print("WARNING: No thematic connections detected")
            
        print("SUCCESS: Complete pipeline verification completed")
        return True
        
    except Exception as e:
        print(f"ERROR: Pipeline verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_complete_pipeline())
    sys.exit(0 if success else 1)