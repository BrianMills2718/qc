"""
Test Phase 1 Isolation - Code Discovery
Tests that Phase 1 (code taxonomy discovery) works with real interviews
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import (
    ExtractionConfig,
    ExtractionApproach
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Interview files
TEST_INTERVIEWS = [
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Focus Group on AI and Methods 7_7.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Focus Group_ AI and Qualitative methods (3).docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx"
]

async def test_code_discovery_open():
    """Test Phase 1 with OPEN coding approach"""
    logger.info("=" * 60)
    logger.info("TEST: Phase 1 - Open Code Discovery")
    logger.info("=" * 60)
    
    config = ExtractionConfig(
        interview_files=TEST_INTERVIEWS[:2],  # Use first 2 interviews for speed
        coding_approach=ExtractionApproach.OPEN,
        analytic_question="How is AI impacting qualitative research methods?",
        code_hierarchy_depth=3,
        # Skip other phases
        speaker_approach=ExtractionApproach.CLOSED,
        entity_approach=ExtractionApproach.CLOSED,
        auto_import_neo4j=False
    )
    
    extractor = CodeFirstExtractor(config)
    
    try:
        # Call Phase 1 directly
        logger.info("Running Phase 1: Code Discovery...")
        await extractor._run_phase_1()
        
        # Validate taxonomy
        assert extractor.code_taxonomy is not None, "Code taxonomy should not be None"
        assert len(extractor.code_taxonomy.codes) > 0, "Should discover at least one code"
        assert extractor.code_taxonomy.hierarchy_depth >= 1, "Should have at least 1 hierarchy level"
        
        logger.info(f"✅ Successfully discovered code taxonomy:")
        logger.info(f"   Total codes: {extractor.code_taxonomy.total_codes}")
        logger.info(f"   Hierarchy depth: {extractor.code_taxonomy.hierarchy_depth}")
        
        # Show top-level codes
        root_codes = [c for c in extractor.code_taxonomy.codes if c.level == 1]
        logger.info(f"   Root codes ({len(root_codes)}):")
        for code in root_codes[:5]:
            logger.info(f"     - {code.name}: {code.description[:50]}...")
        
        # Check for child codes
        child_codes = [c for c in extractor.code_taxonomy.codes if c.level > 1]
        if child_codes:
            logger.info(f"   Child codes found: {len(child_codes)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_code_discovery_all_interviews():
    """Test Phase 1 with ALL 5 interviews"""
    logger.info("=" * 60)
    logger.info("TEST: Phase 1 - All Interviews Code Discovery")
    logger.info("=" * 60)
    
    config = ExtractionConfig(
        interview_files=TEST_INTERVIEWS,  # All 5 interviews
        coding_approach=ExtractionApproach.OPEN,
        analytic_question="What are the key themes regarding AI and qualitative research methods?",
        code_hierarchy_depth=3,
        # Skip other phases
        speaker_approach=ExtractionApproach.CLOSED,
        entity_approach=ExtractionApproach.CLOSED,
        auto_import_neo4j=False
    )
    
    extractor = CodeFirstExtractor(config)
    
    try:
        # Call Phase 1 directly
        logger.info(f"Running Phase 1 with {len(TEST_INTERVIEWS)} interviews...")
        start_time = datetime.now()
        
        await extractor._run_phase_1()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Phase 1 completed in {elapsed:.1f} seconds")
        
        # Validate taxonomy
        assert extractor.code_taxonomy is not None
        assert extractor.code_taxonomy.total_codes >= 5, "Should discover at least 5 codes from 5 interviews"
        
        logger.info(f"✅ Successfully processed all interviews:")
        logger.info(f"   Total codes: {extractor.code_taxonomy.total_codes}")
        logger.info(f"   Hierarchy depth: {extractor.code_taxonomy.hierarchy_depth}")
        logger.info(f"   Processing time: {elapsed:.1f}s")
        
        # Analyze code distribution
        level_counts = {}
        for code in extractor.code_taxonomy.codes:
            level_counts[code.level] = level_counts.get(code.level, 0) + 1
        
        logger.info("   Code distribution by level:")
        for level in sorted(level_counts.keys()):
            logger.info(f"     Level {level}: {level_counts[level]} codes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed with all interviews: {e}")
        return False

async def test_code_persistence():
    """Test that discovered codes are saved correctly"""
    logger.info("=" * 60)
    logger.info("TEST: Phase 1 - Code Persistence")
    logger.info("=" * 60)
    
    config = ExtractionConfig(
        interview_files=TEST_INTERVIEWS[:1],  # Just one interview for speed
        coding_approach=ExtractionApproach.OPEN,
        analytic_question="AI and qualitative research",
        output_dir="test_output",
        auto_import_neo4j=False
    )
    
    extractor = CodeFirstExtractor(config)
    
    try:
        # Run Phase 1
        await extractor._run_phase_1()
        
        # Check if taxonomy was saved
        output_dir = Path(config.output_dir)
        taxonomy_file = output_dir / "phase_1_code_taxonomy.json"
        
        assert taxonomy_file.exists(), f"Taxonomy file should exist at {taxonomy_file}"
        
        # Load and validate saved taxonomy
        import json
        with open(taxonomy_file, 'r') as f:
            saved_data = json.load(f)
        
        assert "codes" in saved_data
        assert "total_codes" in saved_data
        assert saved_data["total_codes"] == extractor.code_taxonomy.total_codes
        
        logger.info(f"✅ Code taxonomy successfully saved to {taxonomy_file}")
        logger.info(f"   File size: {taxonomy_file.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Persistence test failed: {e}")
        return False

async def main():
    """Run all Phase 1 tests"""
    logger.info("Starting Phase 1 Isolation Tests")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"API Key present: {bool(os.getenv('GEMINI_API_KEY'))}")
    
    tests = [
        ("Open Code Discovery (2 interviews)", test_code_discovery_open),
        ("All Interviews Code Discovery", test_code_discovery_all_interviews),
        ("Code Persistence", test_code_persistence)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL PHASE 1 TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)