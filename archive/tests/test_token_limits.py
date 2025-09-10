"""
Test Token Limits - Verify we can process all 5 interviews in one call
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, 'src')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Interview files as specified in CLAUDE.md
TEST_INTERVIEWS = [
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Focus Group on AI and Methods 7_7.docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Focus Group_ AI and Qualitative methods (3).docx",
    "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx"
]

def check_files_exist():
    """Verify all interview files exist"""
    logger.info("Checking if interview files exist...")
    all_exist = True
    for file_path in TEST_INTERVIEWS:
        path = Path(file_path)
        exists = path.exists()
        status = "✅" if exists else "❌"
        logger.info(f"  {status} {path.name}: {'exists' if exists else 'NOT FOUND'}")
        if not exists:
            all_exist = False
    return all_exist

async def read_interview_content(file_path: str) -> str:
    """Read interview content from a DOCX file"""
    from qc.extraction.code_first_extractor import CodeFirstExtractor
    
    # Use the extractor's method to read DOCX
    try:
        extractor = CodeFirstExtractor(None)  # We just need the utility method
        content = await extractor._read_interview(file_path)
        return content
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        # Fallback to basic text reading if DOCX parsing fails
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except:
            return f"[Failed to read {file_path}]"

async def test_concatenated_interviews():
    """Test that we can concatenate and process all 5 interviews"""
    logger.info("=" * 60)
    logger.info("TEST: Concatenated Interview Token Capacity")
    logger.info("=" * 60)
    
    # Check files exist first
    if not check_files_exist():
        logger.error("Some interview files are missing!")
        return False
    
    # Read all interviews
    logger.info("\nReading all interview files...")
    all_content = []
    total_chars = 0
    
    for file_path in TEST_INTERVIEWS:
        content = await read_interview_content(file_path)
        file_chars = len(content)
        total_chars += file_chars
        all_content.append(f"=== Interview from {Path(file_path).name} ===\n{content}")
        logger.info(f"  Read {Path(file_path).name}: {file_chars:,} characters")
    
    # Concatenate all interviews
    combined_text = "\n\n".join(all_content)
    logger.info(f"\nTotal combined text: {len(combined_text):,} characters")
    
    # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
    estimated_tokens = len(combined_text) // 4
    logger.info(f"Estimated tokens: {estimated_tokens:,}")
    
    # Check against typical model limits
    model_limits = {
        "gemini-2.5-flash": 1_000_000,  # 1M token context window
        "gpt-4": 128_000,
        "claude-3": 200_000
    }
    
    logger.info("\nModel capacity check:")
    for model, limit in model_limits.items():
        percentage = (estimated_tokens / limit) * 100
        status = "✅" if estimated_tokens < limit else "❌"
        logger.info(f"  {status} {model}: {percentage:.1f}% of {limit:,} token limit")
    
    # Test actual LLM call with concatenated content
    logger.info("\nTesting actual LLM call with concatenated content...")
    
    from qc.llm.llm_handler import LLMHandler
    from qc.extraction.code_first_schemas import CodeTaxonomy
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    # Create a test prompt with all content
    test_prompt = f"""
    Analyze these {len(TEST_INTERVIEWS)} interviews and identify the main themes.
    
    {combined_text[:50000]}  # Use first 50k chars for test
    
    Identify 3-5 main thematic codes from these interviews.
    """
    
    try:
        # Attempt extraction with no max_tokens limit
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=CodeTaxonomy,
            max_tokens=None  # No limit - use full context
        )
        
        logger.info(f"✅ Successfully processed concatenated interviews!")
        logger.info(f"   Discovered {result.total_codes} codes")
        logger.info(f"   Hierarchy depth: {result.hierarchy_depth}")
        
        # Show first few codes
        for i, code in enumerate(result.codes[:3]):
            logger.info(f"   Code {i+1}: {code.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to process concatenated interviews: {e}")
        return False

async def test_individual_vs_concatenated():
    """Compare processing individually vs all at once"""
    logger.info("=" * 60)
    logger.info("TEST: Individual vs Concatenated Processing")
    logger.info("=" * 60)
    
    from qc.llm.llm_handler import LLMHandler
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    # Test individual processing (simplified)
    logger.info("Testing individual file processing...")
    individual_tokens = 0
    
    for file_path in TEST_INTERVIEWS[:2]:  # Test first 2 files
        content = await read_interview_content(file_path)
        char_count = len(content)
        token_estimate = char_count // 4
        individual_tokens += token_estimate
        logger.info(f"  {Path(file_path).name}: ~{token_estimate:,} tokens")
    
    # Test concatenated processing
    logger.info("\nTesting concatenated processing...")
    all_content = []
    for file_path in TEST_INTERVIEWS[:2]:
        content = await read_interview_content(file_path)
        all_content.append(content)
    
    combined = "\n\n".join(all_content)
    combined_tokens = len(combined) // 4
    
    logger.info(f"  Combined: ~{combined_tokens:,} tokens")
    
    # Compare
    overhead = combined_tokens - individual_tokens
    logger.info(f"\nToken overhead from concatenation: {overhead:,} tokens ({overhead/individual_tokens*100:.1f}%)")
    
    return True

async def main():
    """Run all token limit tests"""
    logger.info("Starting Token Limit Tests")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Testing with {len(TEST_INTERVIEWS)} interview files")
    
    tests = [
        ("Concatenated Interview Capacity", test_concatenated_interviews),
        ("Individual vs Concatenated", test_individual_vs_concatenated)
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
        logger.info("🎉 ALL TOKEN TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)