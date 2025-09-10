"""
Test schema validation for critical breaking issues
Validates that schema mismatches have been fixed
"""
import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_schemas import (
    SimpleQuote, EnhancedQuote, SpeakerInfo, DiscoveredEntityType, 
    DiscoveredRelationshipType, QuotesAndSpeakers, EntitiesAndRelationships
)

def test_location_field_compatibility():
    """Test that SimpleQuote location fields can be None and work with EnhancedQuote"""
    print("Testing location field compatibility...")
    
    # Create SimpleQuote with None location fields (expected from LLM)
    simple_quote = SimpleQuote(
        text="This is a test quote about AI tools",
        speaker_name="Test Speaker",
        code_ids=["AI_TOOL_USAGE"],
        location_start=None,  # LLM might return None
        location_end=None,    # LLM might return None
        location_type=None
    )
    
    print(f"[PASS] SimpleQuote created with None locations: {simple_quote.location_start}, {simple_quote.location_end}")
    
    # Create EnhancedQuote using SimpleQuote data
    speaker = SpeakerInfo(
        name="Test Speaker",
        confidence=0.8,
        identification_method="test",
        quotes_count=1
    )
    
    enhanced_quote = EnhancedQuote(
        id="TEST_Q001",
        text=simple_quote.text,
        context_summary="Test context",
        code_ids=simple_quote.code_ids,
        code_names=["AI Tool Usage"],
        code_confidence_scores=[0.8],
        speaker=speaker,
        interview_id="test_interview",
        interview_title="Test Interview",
        line_start=simple_quote.location_start,  # Should accept None
        line_end=simple_quote.location_end,      # Should accept None
        quote_entities=[],
        quote_relationships=[],
        extraction_confidence=0.8
    )
    
    print(f"✅ EnhancedQuote created with None locations: {enhanced_quote.line_start}, {enhanced_quote.line_end}")
    return True

def test_required_id_fields():
    """Test that ID fields are properly handled in entity/relationship schemas"""
    print("Testing required ID fields...")
    
    # Test DiscoveredEntityType with required ID
    try:
        entity_type = DiscoveredEntityType(
            id="AI_TOOL",  # Required field
            name="AI Tool",
            description="Artificial intelligence software tools",
            frequency=5,
            example_entities=["ChatGPT", "Claude"],
            common_contexts=["research", "writing"],
            confidence=0.8
        )
        print(f"✅ DiscoveredEntityType created with ID: {entity_type.id}")
    except Exception as e:
        print(f"❌ DiscoveredEntityType failed: {e}")
        return False
    
    # Test DiscoveredRelationshipType with required ID
    try:
        relationship_type = DiscoveredRelationshipType(
            id="USES",  # Required field
            name="Uses",
            description="Entity uses another entity",
            frequency=10,
            common_source_types=["PERSON"],
            common_target_types=["AI_TOOL"],
            directional=True,
            example_relationships=[],
            confidence=0.8
        )
        print(f"✅ DiscoveredRelationshipType created with ID: {relationship_type.id}")
    except Exception as e:
        print(f"❌ DiscoveredRelationshipType failed: {e}")
        return False
    
    return True

def test_quotes_and_speakers_schema():
    """Test QuotesAndSpeakers schema can handle mixed location data"""
    print("Testing QuotesAndSpeakers schema...")
    
    quotes = [
        SimpleQuote(
            text="Quote with line numbers",
            speaker_name="Speaker1", 
            code_ids=["CODE1"],
            location_start=10,
            location_end=12,
            location_type="line"
        ),
        SimpleQuote(
            text="Quote without location",
            speaker_name="Speaker2",
            code_ids=["CODE2"],
            location_start=None,  # No location data
            location_end=None,
            location_type=None
        )
    ]
    
    speakers = [
        SpeakerInfo(name="Speaker1", confidence=0.9, identification_method="label"),
        SpeakerInfo(name="Speaker2", confidence=0.7, identification_method="inference")
    ]
    
    try:
        quotes_and_speakers = QuotesAndSpeakers(
            quotes=quotes,
            speakers=speakers,
            total_quotes=2,
            total_codes_applied=2
        )
        print(f"✅ QuotesAndSpeakers created with {len(quotes_and_speakers.quotes)} quotes")
        return True
    except Exception as e:
        print(f"❌ QuotesAndSpeakers failed: {e}")
        return False

def main():
    """Run all validation tests"""
    print("=" * 60)
    print("SCHEMA VALIDATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_location_field_compatibility,
        test_required_id_fields,
        test_quotes_and_speakers_schema
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED\n")
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED\n")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED with exception: {e}\n")
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Pipeline schemas are ready!")
    else:
        print("🚨 SCHEMA ISSUES DETECTED - Pipeline will fail!")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)