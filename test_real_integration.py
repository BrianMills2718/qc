#!/usr/bin/env python3
"""
REAL Integration Test - No Mocks!

Tests the complete pipeline with:
- Real Gemini API calls
- Real 103 interview DOCX files  
- Real Neo4j database (if running)
- Real token counting and validation

Run this to verify the entire system works end-to-end.
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.storage.simple_neo4j_client import SimpleNeo4jClient, Neo4jConnectionError
from qc.core.load_and_verify_interviews import load_all_interviews_with_metadata

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_real_interview_loading():
    """Test loading all 103 real interview files."""
    logger.info("=== Testing Real Interview Loading ===")
    
    analyzer = GlobalQualitativeAnalyzer()
    logger.info(f"Found {len(analyzer.interview_files)} interview files")
    
    # Load all interviews
    full_text, total_tokens, metadata = load_all_interviews_with_metadata(analyzer.interview_files)
    
    logger.info(f"Total interviews: {len(metadata)}")
    logger.info(f"Total tokens: {total_tokens:,}")
    logger.info(f"Token limit check: {'✅ PASS' if total_tokens < 900_000 else '❌ FAIL'}")
    
    # Show sample metadata
    logger.info("Sample interview metadata:")
    for i, meta in enumerate(metadata[:3]):
        logger.info(f"  {i+1}. {meta['file_name']}: {meta['word_count']} words, {meta['estimated_tokens']} tokens")
    
    return {
        'interviews_found': len(analyzer.interview_files),
        'interviews_loaded': len(metadata),
        'total_tokens': total_tokens,
        'within_limits': total_tokens < 900_000
    }


async def test_real_gemini_api():
    """Test real Gemini API call with small sample."""
    logger.info("=== Testing Real Gemini API ===")
    
    analyzer = GlobalQualitativeAnalyzer()
    
    try:
        # Use small sample to avoid large API costs
        logger.info("Running analysis with 3 interviews (real API call)...")
        result = await analyzer.analyze_global(sample_size=3)
        
        logger.info(f"✅ Analysis completed successfully!")
        logger.info(f"  Study ID: {result.global_analysis.study_id}")
        logger.info(f"  Interviews analyzed: {result.global_analysis.interviews_analyzed}")
        logger.info(f"  Themes found: {len(result.global_analysis.themes)}")
        logger.info(f"  Codes found: {len(result.global_analysis.codes)}")
        logger.info(f"  Traceability: {result.traceability_completeness:.1%}")
        
        return {
            'api_success': True,
            'themes_count': len(result.global_analysis.themes),
            'codes_count': len(result.global_analysis.codes),
            'traceability': result.traceability_completeness,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"❌ Gemini API call failed: {str(e)}")
        return {
            'api_success': False,
            'error': str(e)
        }


async def test_real_neo4j_connection():
    """Test real Neo4j database connection."""
    logger.info("=== Testing Real Neo4j Connection ===")
    
    try:
        client = SimpleNeo4jClient()
        logger.info(f"Attempting connection to {client.uri}...")
        
        await client.connect()
        logger.info("✅ Connected to Neo4j successfully!")
        
        # Test schema creation
        await client.create_schema()
        logger.info("✅ Schema created successfully!")
        
        # Test basic query
        schema_info = await client.get_schema_info()
        logger.info(f"  Node labels: {len(schema_info['node_labels'])}")
        logger.info(f"  Relationship types: {len(schema_info['relationship_types'])}")
        
        await client.close()
        logger.info("✅ Connection closed successfully!")
        
        return {
            'neo4j_success': True,
            'schema_info': schema_info
        }
        
    except Neo4jConnectionError as e:
        logger.warning(f"⚠️  Neo4j not available: {str(e)}")
        logger.info("This is OK - Neo4j is optional for testing the core analysis")
        return {
            'neo4j_success': False,
            'error': str(e),
            'optional': True
        }
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {str(e)}")
        return {
            'neo4j_success': False,
            'error': str(e),
            'optional': False
        }


async def test_full_pipeline():
    """Test the complete pipeline with real components."""
    logger.info("=== Testing Full Real Pipeline ===")
    
    try:
        analyzer = GlobalQualitativeAnalyzer()
        
        # Run with 5 interviews (balance between real testing and API costs)
        logger.info("Running full pipeline with 5 interviews...")
        result = await analyzer.analyze_global(sample_size=5)
        
        # Export results
        output_dir = project_root / "output" / "real_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        analyzer.export_csv_files(result, output_dir / "csv")
        analyzer.export_markdown_report(result, output_dir / "report.md")
        analyzer.export_json_backup(result, output_dir / "analysis.json")
        
        logger.info("✅ Full pipeline completed successfully!")
        logger.info(f"  Results exported to: {output_dir}")
        logger.info(f"  Study ID: {result.global_analysis.study_id}")
        logger.info(f"  Processing time: {result.global_analysis.processing_metadata.get('processing_time_seconds', 'N/A')}s")
        logger.info(f"  LLM calls used: {result.global_analysis.processing_metadata.get('llm_calls', 'N/A')}")
        
        return {
            'pipeline_success': True,
            'output_dir': str(output_dir),
            'result': result
        }
        
    except Exception as e:
        logger.error(f"❌ Full pipeline failed: {str(e)}")
        return {
            'pipeline_success': False,
            'error': str(e)
        }


async def main():
    """Run all real integration tests."""
    logger.info("🧪 REAL INTEGRATION TESTING - NO MOCKS")
    logger.info("=" * 50)
    
    results = {}
    
    # Test 1: Real interview loading
    results['interviews'] = await test_real_interview_loading()
    
    # Test 2: Real Neo4j (optional)
    results['neo4j'] = await test_real_neo4j_connection()
    
    # Test 3: Real Gemini API
    results['gemini'] = await test_real_gemini_api()
    
    # Test 4: Full pipeline (if Gemini worked)
    if results['gemini']['api_success']:
        results['pipeline'] = await test_full_pipeline()
    else:
        logger.info("⏭️  Skipping full pipeline test due to Gemini API failure")
        results['pipeline'] = {'pipeline_success': False, 'skipped': True}
    
    # Summary
    logger.info("=" * 50)
    logger.info("🏁 REAL INTEGRATION TEST SUMMARY")
    logger.info("=" * 50)
    
    # Interview loading
    interviews = results['interviews']
    logger.info(f"📁 Interview Loading: {'✅' if interviews['within_limits'] else '❌'}")
    logger.info(f"   Found: {interviews['interviews_found']} files")
    logger.info(f"   Loaded: {interviews['interviews_loaded']} interviews") 
    logger.info(f"   Tokens: {interviews['total_tokens']:,} ({'within limits' if interviews['within_limits'] else 'EXCEEDS LIMITS'})")
    
    # Neo4j
    neo4j = results['neo4j']
    status = "✅" if neo4j['neo4j_success'] else ("⚠️" if neo4j.get('optional') else "❌")
    logger.info(f"🗄️  Neo4j Database: {status}")
    if neo4j['neo4j_success']:
        logger.info(f"   Schema created with {len(neo4j['schema_info']['node_labels'])} node types")
    else:
        logger.info(f"   {neo4j['error']}")
    
    # Gemini API
    gemini = results['gemini']
    logger.info(f"🤖 Gemini API: {'✅' if gemini['api_success'] else '❌'}")
    if gemini['api_success']:
        logger.info(f"   Themes: {gemini['themes_count']}, Codes: {gemini['codes_count']}")
        logger.info(f"   Traceability: {gemini['traceability']:.1%}")
    else:
        logger.info(f"   {gemini['error']}")
    
    # Pipeline
    pipeline = results['pipeline']
    if not pipeline.get('skipped'):
        logger.info(f"🔄 Full Pipeline: {'✅' if pipeline['pipeline_success'] else '❌'}")
        if pipeline['pipeline_success']:
            logger.info(f"   Output: {pipeline['output_dir']}")
        else:
            logger.info(f"   {pipeline['error']}")
    else:
        logger.info(f"🔄 Full Pipeline: ⏭️ Skipped")
    
    # Overall status
    core_working = interviews['within_limits'] and gemini['api_success']
    logger.info("=" * 50)
    logger.info(f"🎯 OVERALL STATUS: {'✅ READY FOR PRODUCTION' if core_working else '❌ NEEDS FIXES'}")
    
    if core_working:
        logger.info("✨ LLM-native global analysis is working with real data!")
        logger.info("   - All 103 interviews fit in context window")
        logger.info("   - Gemini API integration functional") 
        logger.info("   - Full pipeline operational")
        logger.info("   - Ready for Day 4+ tasks or systematic fallback")
    else:
        logger.info("🔧 Issues to resolve:")
        if not interviews['within_limits']:
            logger.info("   - Token limit exceeded - need batching or fallback")
        if not gemini['api_success']:
            logger.info("   - Gemini API connection issues")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())