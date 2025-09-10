"""
Test LiteLLM Integration with Structured Output
Tests that LiteLLM works correctly with Pydantic models for structured extraction
"""
import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
import sys
sys.path.insert(0, 'src')

from src.qc.llm.llm_handler import LLMHandler
from src.qc.extraction.code_first_schemas import (
    HierarchicalCode,
    CodeTaxonomy,
    DiscoveredSpeakerProperty,
    SpeakerPropertySchema
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_basic_structured_extraction():
    """Test that LiteLLM can extract structured data using Pydantic models"""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Structured Extraction")
    logger.info("=" * 60)
    
    # Initialize LLM handler
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    # Test with a simple code extraction
    test_prompt = """
    Extract a hierarchical code from this interview excerpt:
    
    "I believe that AI will fundamentally change how we do qualitative research. 
    The ability to process large amounts of text data and identify patterns is 
    revolutionary. However, we must be careful not to lose the human insight 
    and interpretation that makes qualitative research valuable."
    
    Create a code that captures the main theme about AI's impact on research.
    """
    
    try:
        # Extract a single hierarchical code
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=HierarchicalCode,
            instructions="Extract ONE main thematic code with appropriate hierarchy"
        )
        
        logger.info(f"✅ Successfully extracted HierarchicalCode")
        logger.info(f"   Code Name: {result.name}")
        logger.info(f"   Description: {result.description}")
        logger.info(f"   Level: {result.level}")
        if result.parent_id:
            logger.info(f"   Parent ID: {result.parent_id}")
        if result.example_quotes:
            logger.info(f"   Example quotes: {len(result.example_quotes)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to extract structured data: {e}")
        return False

async def test_complex_taxonomy_extraction():
    """Test extraction of a complete code taxonomy"""
    logger.info("=" * 60)
    logger.info("TEST 2: Complex Taxonomy Extraction")
    logger.info("=" * 60)
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    test_prompt = """
    Analyze these interview excerpts and create a code taxonomy:
    
    1. "AI tools help us analyze data faster, but we need to validate the results carefully."
    2. "The cost of AI tools is a barrier for many researchers."
    3. "Training is essential - not everyone knows how to use these tools effectively."
    4. "I worry about the ethical implications of automated analysis."
    5. "The time savings are incredible - what took weeks now takes hours."
    
    Create a hierarchical taxonomy with at least 2 levels capturing these themes.
    """
    
    try:
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=CodeTaxonomy,
            instructions="Create a complete hierarchical taxonomy with parent and child codes"
        )
        
        logger.info(f"✅ Successfully extracted CodeTaxonomy")
        logger.info(f"   Total codes: {result.total_codes}")
        logger.info(f"   Hierarchy depth: {result.hierarchy_depth}")
        logger.info(f"   Number of root codes: {len([c for c in result.codes if c.level == 1])}")
        
        # Display first few codes
        for i, code in enumerate(result.codes[:3]):
            logger.info(f"   Code {i+1}: {code.name} (Level {code.level})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to extract taxonomy: {e}")
        return False

async def test_speaker_schema_extraction():
    """Test extraction of speaker property schema"""
    logger.info("=" * 60)
    logger.info("TEST 3: Speaker Schema Extraction")
    logger.info("=" * 60)
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    test_prompt = """
    From these interview introductions, identify speaker properties to track:
    
    1. "I'm Dr. Smith, I've been a professor here for 15 years in the Computer Science department."
    2. "My name is Jane, I'm a PhD student in my third year studying qualitative methods."
    3. "I'm the Director of Research at TechCorp, with expertise in AI and machine learning."
    4. "As someone with 20 years in the field and experience with both qual and quant methods..."
    
    What properties should we track for speakers in this study?
    """
    
    try:
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=SpeakerPropertySchema,
            instructions="Identify relevant speaker properties based on what's mentioned"
        )
        
        logger.info(f"✅ Successfully extracted SpeakerPropertySchema")
        logger.info(f"   Number of properties: {len(result.properties)}")
        
        for prop in result.properties[:5]:
            logger.info(f"   - {prop.name} ({prop.property_type}): {prop.frequency} occurrences")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to extract speaker schema: {e}")
        return False

async def test_no_max_tokens():
    """Test that we can process without max_tokens limit"""
    logger.info("=" * 60)
    logger.info("TEST 4: No Max Tokens Limit")
    logger.info("=" * 60)
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    # Create a longer prompt to test token handling
    test_prompt = """
    Extract a simple code from this text:
    """ + ("This is a test sentence about AI and qualitative research methods. " * 50)
    
    try:
        # Call without max_tokens (should use None by default)
        result = await llm.extract_structured(
            prompt=test_prompt,
            schema=HierarchicalCode,
            max_tokens=None  # Explicitly None
        )
        
        logger.info(f"✅ Successfully processed without max_tokens limit")
        logger.info(f"   Extracted code: {result.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed without max_tokens: {e}")
        return False

async def test_raw_completion():
    """Test raw completion functionality"""
    logger.info("=" * 60)
    logger.info("TEST 5: Raw Completion")
    logger.info("=" * 60)
    
    llm = LLMHandler(model_name="gemini-2.5-flash", temperature=0.1)
    
    test_prompt = "Complete this: The main benefit of using AI in qualitative research is"
    
    try:
        result = await llm.complete_raw(
            prompt=test_prompt,
            max_tokens=50  # Limit for testing
        )
        
        logger.info(f"✅ Raw completion successful")
        if result:
            logger.info(f"   Response: {result[:100] if len(result) > 100 else result}")
        else:
            logger.info(f"   Response was empty or None: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Raw completion failed: {e}")
        return False

async def main():
    """Run all tests"""
    logger.info("Starting LiteLLM Integration Tests")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"API Key present: {bool(os.getenv('GEMINI_API_KEY'))}")
    
    tests = [
        ("Basic Structured Extraction", test_basic_structured_extraction),
        ("Complex Taxonomy Extraction", test_complex_taxonomy_extraction),
        ("Speaker Schema Extraction", test_speaker_schema_extraction),
        ("No Max Tokens", test_no_max_tokens),
        ("Raw Completion", test_raw_completion)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
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
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)