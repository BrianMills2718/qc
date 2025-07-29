#!/usr/bin/env python3
"""
Minimal end-to-end test focusing on just the first call
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.storage.simple_neo4j_client import SimpleNeo4jClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_minimal_end_to_end():
    """Test minimal pipeline with just first call."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Test with just 3 interviews to be fast
    logger.info("Starting minimal test with 3 interviews...")
    
    try:
        # Just do the first analysis call
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
        
        logger.info(f"SUCCESS! Analysis completed:")
        logger.info(f"- Themes found: {len(result.themes)}")
        logger.info(f"- Codes found: {len(result.codes)}")
        logger.info(f"- Quote chains: {len(result.quote_chains)}")
        logger.info(f"- Saturation point: {result.saturation_assessment.saturation_point}")
        
        # Test Neo4j storage
        neo4j_client = SimpleNeo4jClient()
        await neo4j_client.connect()
        logger.info("Connected to Neo4j")
        
        await neo4j_client.create_schema()
        await neo4j_client.store_global_result(result)
        logger.info("Stored results in Neo4j")
        
        await neo4j_client.close()
        
        # Create minimal CSV export for testing
        output_dir = project_root / "output" / "minimal_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export basic JSON
        import json
        with open(output_dir / "result.json", 'w', encoding='utf-8') as f:
            json.dump(result.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Exported results to {output_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_minimal_end_to_end()
    if success:
        print("\n[PASS] Minimal end-to-end test completed!")
        print("- Real interview loading: WORKING")
        print("- Real Gemini API: WORKING")
        print("- Real Neo4j storage: WORKING")
        print("- Simplified schema: WORKING")
    else:
        print("\n[FAIL] Minimal end-to-end test failed!")


if __name__ == "__main__":
    asyncio.run(main())