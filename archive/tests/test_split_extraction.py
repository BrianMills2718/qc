"""Test the split Phase 4 extraction approach"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def test_split_extraction():
    """Test split Phase 4 extraction with real interview"""
    
    # Configuration
    config = ExtractionConfig(
        analytic_question="What are the key themes and challenges in using AI for qualitative research?",
        interview_files=[
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx"
        ],
        coding_approach=ExtractionApproach.OPEN,
        speaker_approach=ExtractionApproach.OPEN,
        entity_approach=ExtractionApproach.OPEN,
        output_dir="output_split_test",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        temperature=0.1
    )
    
    # Run extraction
    extractor = CodeFirstExtractor(config)
    
    try:
        print("Starting split extraction test...")
        print("=" * 80)
        
        # Run all phases
        results = await extractor.run_extraction()
        
        print("\n" + "=" * 80)
        print("EXTRACTION RESULTS SUMMARY")
        print("=" * 80)
        
        # Phase 1-3 results
        print(f"\nPhase 1 (Codes): {len(results.code_taxonomy.codes)} codes discovered")
        print(f"Phase 2 (Speakers): {len(results.speaker_schema.properties)} speaker properties")
        print(f"Phase 3 (Entities): {len(results.entity_relationship_schema.entity_types)} entity types, "
              f"{len(results.entity_relationship_schema.relationship_types)} relationship types")
        
        # Phase 4 results
        if results.coded_interviews:
            interview = results.coded_interviews[0]
            print(f"\nPhase 4 Results for Interview:")
            print(f"  - Total quotes extracted: {interview.total_quotes}")
            print(f"  - Total code applications: {interview.total_codes_applied}")
            print(f"  - Unique codes used: {len(interview.unique_codes_used)}")
            print(f"  - Total speakers: {interview.total_speakers}")
            print(f"  - Total entities: {interview.total_entities}")
            print(f"  - Total relationships: {interview.total_relationships}")
            
            # Check many-to-many coding
            multi_coded = sum(1 for q in interview.quotes if len(q.code_names) > 1)
            avg_codes = sum(len(q.code_names) for q in interview.quotes) / len(interview.quotes) if interview.quotes else 0
            
            print(f"\nMany-to-Many Coding Analysis:")
            print(f"  - Quotes with multiple codes: {multi_coded}/{len(interview.quotes)} "
                  f"({multi_coded/len(interview.quotes)*100:.1f}%)" if interview.quotes else "No quotes")
            print(f"  - Average codes per quote: {avg_codes:.2f}")
            
            # Sample quotes
            print(f"\nSample Quotes (first 3):")
            for i, quote in enumerate(interview.quotes[:3], 1):
                print(f"\n  Quote {i}:")
                print(f"    Text: '{quote.text[:100]}...'")
                print(f"    Speaker: {quote.speaker.name}")
                print(f"    Codes ({len(quote.code_names)}): {', '.join(quote.code_names)}")
                print(f"    Entities: {len(quote.quote_entities)}")
                print(f"    Relationships: {len(quote.quote_relationships)}")
        
        print("\n" + "=" * 80)
        print("SUCCESS: Split extraction test completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"\nERROR: Split extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = asyncio.run(test_split_extraction())
    
    # Final validation
    if results and results.coded_interviews:
        interview = results.coded_interviews[0]
        if interview.total_quotes >= 20:
            print(f"\n[SUCCESS] Extracted {interview.total_quotes} quotes (target was 20-30)")
        else:
            print(f"\n[WARNING] Only extracted {interview.total_quotes} quotes (target was 20-30)")