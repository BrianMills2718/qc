"""Test just Phase 4 with mock schemas to isolate the issue"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import (
    ExtractionConfig, ExtractionApproach,
    CodeTaxonomy, HierarchicalCode,
    SpeakerPropertySchema, DiscoveredSpeakerProperty,
    EntityRelationshipSchema, DiscoveredEntityType, DiscoveredRelationshipType
)

async def test_phase4_only():
    """Test Phase 4 extraction with minimal schemas"""
    
    # Create minimal schemas for testing
    code_taxonomy = CodeTaxonomy(
        codes=[
            HierarchicalCode(
                id="1", name="AI Benefits", 
                description="Benefits of using AI",
                semantic_definition="Positive aspects of AI use",
                level=1
            ),
            HierarchicalCode(
                id="2", name="AI Challenges",
                description="Challenges with AI",
                semantic_definition="Difficulties and problems with AI",
                level=1
            ),
            HierarchicalCode(
                id="3", name="Human Oversight",
                description="Need for human review",
                semantic_definition="Human involvement required",
                level=1
            )
        ],
        total_codes=3,
        hierarchy_depth=1,
        discovery_method="test",
        analytic_question="Test question"
    )
    
    speaker_schema = SpeakerPropertySchema(
        properties=[
            DiscoveredSpeakerProperty(
                name="role",
                property_type="text",
                frequency=10,
                example_values=["Researcher", "Professor"],
                is_categorical=False
            )
        ],
        total_speakers_found=2,
        discovery_method="test"
    )
    
    entity_schema = EntityRelationshipSchema(
        entity_types=[
            DiscoveredEntityType(
                name="AI_Tool",
                description="AI tools and systems",
                frequency=10,
                example_entities=["ChatGPT", "Claude"],
                common_contexts=["research", "analysis"]
            ),
            DiscoveredEntityType(
                name="Research_Method",
                description="Research methods",
                frequency=5,
                example_entities=["thematic analysis", "coding"],
                common_contexts=["qualitative research"]
            )
        ],
        relationship_types=[
            DiscoveredRelationshipType(
                name="USES",
                description="Using a tool or method",
                frequency=5,
                common_source_types=["Researcher"],
                common_target_types=["AI_Tool", "Research_Method"],
                directional=True,
                example_relationships=[]
            )
        ],
        total_entities_found=15,
        total_relationships_found=5,
        discovery_method="test"
    )
    
    # Configuration
    config = ExtractionConfig(
        analytic_question="What are the key themes in using AI for research?",
        interview_files=[
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx"
        ],
        coding_approach=ExtractionApproach.OPEN,
        output_dir="output_phase4_test",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash"
    )
    
    # Create extractor and set schemas
    extractor = CodeFirstExtractor(config)
    extractor.code_taxonomy = code_taxonomy
    extractor.speaker_schema = speaker_schema
    extractor.entity_schema = entity_schema
    
    try:
        print("Testing Phase 4 extraction only...")
        print("=" * 80)
        
        # Run just Phase 4
        await extractor._run_phase_4()
        
        print("\n" + "=" * 80)
        print("PHASE 4 RESULTS")
        print("=" * 80)
        
        if extractor.coded_interviews:
            interview = extractor.coded_interviews[0]
            print(f"\nInterview processed:")
            print(f"  - Total quotes: {interview.total_quotes}")
            print(f"  - Total code applications: {interview.total_codes_applied}")
            print(f"  - Unique codes used: {len(interview.unique_codes_used)}")
            print(f"  - Total speakers: {interview.total_speakers}")
            print(f"  - Total entities: {interview.total_entities}")
            print(f"  - Total relationships: {interview.total_relationships}")
            
            # Check many-to-many
            if interview.quotes:
                multi_coded = sum(1 for q in interview.quotes if len(q.code_names) > 1)
                avg_codes = sum(len(q.code_names) for q in interview.quotes) / len(interview.quotes)
                
                print(f"\nMany-to-Many Analysis:")
                print(f"  - Quotes with multiple codes: {multi_coded}/{len(interview.quotes)}")
                print(f"  - Average codes per quote: {avg_codes:.2f}")
                
                # Show first few quotes
                print(f"\nFirst 3 quotes:")
                for i, quote in enumerate(interview.quotes[:3], 1):
                    print(f"\n  {i}. Speaker: {quote.speaker.name}")
                    print(f"     Text: '{quote.text[:80]}...'")
                    print(f"     Codes: {', '.join(quote.code_names)}")
            
            return interview
        else:
            print("No interviews coded")
            return None
            
    except Exception as e:
        print(f"\nERROR: Phase 4 test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_phase4_only())
    
    if result and result.total_quotes >= 20:
        print(f"\n[SUCCESS] Extracted {result.total_quotes} quotes!")
    elif result:
        print(f"\n[WARNING] Only extracted {result.total_quotes} quotes")
    else:
        print("\n[FAILURE] No results")