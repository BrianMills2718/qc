#!/usr/bin/env python3
"""
Simple end-to-end test to verify the pipeline works
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


async def test_simple_end_to_end():
    """Test the simplest version of the pipeline."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Test with just 3 interviews to be fast
    logger.info("Starting analysis of 3 interviews...")
    
    try:
        # Run global analysis with 3 interviews
        result = await analyzer.analyze_global(sample_size=3)
        
        logger.info(f"SUCCESS! Analysis completed:")
        logger.info(f"- Themes found: {len(result.global_analysis.themes)}")
        logger.info(f"- Codes found: {len(result.global_analysis.codes)}")
        logger.info(f"- Quote chains: {len(result.global_analysis.quote_chains)}")
        logger.info(f"- Saturation point: {result.global_analysis.saturation_assessment.saturation_point}")
        
        # Test Neo4j storage
        neo4j_client = SimpleNeo4jClient()
        await neo4j_client.connect()
        logger.info("Connected to Neo4j")
        
        await neo4j_client.create_schema()
        await neo4j_client.store_global_result(result.global_analysis)
        logger.info("Stored results in Neo4j")
        
        await neo4j_client.close()
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_simple_end_to_end()
    if success:
        print("\n✅ End-to-end test PASSED!")
    else:
        print("\n❌ End-to-end test FAILED!")


if __name__ == "__main__":
    asyncio.run(main())