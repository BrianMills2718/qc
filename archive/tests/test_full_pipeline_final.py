"""Final test of the complete pipeline with split Phase 4"""
import asyncio
import sys
sys.path.insert(0, 'src')
import os

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def test_full_pipeline():
    """Test complete pipeline with all phases"""
    
    # Test with just 2 interviews to save time
    test_interviews = [
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx"
    ]
    
    # Configuration
    config = ExtractionConfig(
        analytic_question="What are the key themes and challenges in using AI for qualitative research?",
        interview_files=test_interviews,
        coding_approach=ExtractionApproach.OPEN,
        speaker_approach=ExtractionApproach.OPEN,
        entity_approach=ExtractionApproach.OPEN,
        output_dir="output_final_test",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        temperature=0.1
    )
    
    try:
        print("=" * 80)
        print("FULL PIPELINE TEST WITH SPLIT PHASE 4")
        print("=" * 80)
        print(f"Testing with {len(test_interviews)} interviews")
        print(f"Model: {config.llm_model}")
        print()
        
        # Run complete pipeline
        extractor = CodeFirstExtractor(config)
        results = await extractor.run_extraction()
        
        print("\n" + "=" * 80)
        print("PIPELINE RESULTS SUMMARY")
        print("=" * 80)
        
        # Phase results
        print(f"\nPhase 1 - Codes: {results.code_taxonomy.total_codes} discovered")
        print(f"Phase 2 - Speaker Properties: {len(results.speaker_schema.properties)} discovered")
        print(f"Phase 3 - Entity Types: {len(results.entity_relationship_schema.entity_types)}")
        print(f"Phase 3 - Relationship Types: {len(results.entity_relationship_schema.relationship_types)}")
        
        # Phase 4 results per interview
        print(f"\nPhase 4 - Interviews Processed: {len(results.coded_interviews)}")
        
        total_quotes = 0
        total_multi_coded = 0
        total_entities = 0
        total_relationships = 0
        
        for i, interview in enumerate(results.coded_interviews, 1):
            print(f"\n  Interview {i}: {os.path.basename(interview.interview_file)[:40]}...")
            print(f"    - Quotes extracted: {interview.total_quotes}")
            print(f"    - Code applications: {interview.total_codes_applied}")
            print(f"    - Unique codes used: {len(interview.unique_codes_used)}")
            print(f"    - Speakers: {interview.total_speakers}")
            print(f"    - Entities: {interview.total_entities}")
            print(f"    - Relationships: {interview.total_relationships}")
            
            # Many-to-many analysis
            if interview.quotes:
                multi = sum(1 for q in interview.quotes if len(q.code_names) > 1)
                avg_codes = sum(len(q.code_names) for q in interview.quotes) / len(interview.quotes)
                print(f"    - Multi-coded quotes: {multi}/{interview.total_quotes} ({multi/interview.total_quotes*100:.1f}%)")
                print(f"    - Avg codes per quote: {avg_codes:.2f}")
                
                total_quotes += interview.total_quotes
                total_multi_coded += multi
                total_entities += interview.total_entities
                total_relationships += interview.total_relationships
        
        # Overall statistics
        print(f"\n" + "=" * 80)
        print("OVERALL STATISTICS")
        print("=" * 80)
        print(f"Total quotes extracted: {total_quotes}")
        print(f"Total multi-coded quotes: {total_multi_coded} ({total_multi_coded/total_quotes*100:.1f}%)" if total_quotes else "No quotes")
        print(f"Total entities: {total_entities}")
        print(f"Total relationships: {total_relationships}")
        print(f"Processing time: {results.total_processing_time_seconds:.1f} seconds")
        print(f"Tokens used: {results.llm_tokens_used}")
        
        # Sample quotes from first interview
        if results.coded_interviews and results.coded_interviews[0].quotes:
            print(f"\n" + "=" * 80)
            print("SAMPLE QUOTES (First 3)")
            print("=" * 80)
            
            for i, quote in enumerate(results.coded_interviews[0].quotes[:3], 1):
                print(f"\nQuote {i}:")
                print(f"  Speaker: {quote.speaker.name}")
                print(f"  Text: '{quote.text[:100]}...'")
                print(f"  Codes ({len(quote.code_names)}): {', '.join(quote.code_names)}")
                if quote.quote_entities:
                    print(f"  Entities: {', '.join([e.name for e in quote.quote_entities[:3]])}")
        
        # Validation
        print(f"\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)
        
        success_criteria = [
            ("Phase 1 completed", results.code_taxonomy.total_codes > 0),
            ("Phase 2 completed", len(results.speaker_schema.properties) > 0),
            ("Phase 3 completed", len(results.entity_relationship_schema.entity_types) > 0),
            ("Phase 4 completed", len(results.coded_interviews) == len(test_interviews)),
            ("Adequate quotes extracted", total_quotes >= 20 * len(test_interviews)),
            ("Many-to-many coding", total_multi_coded > total_quotes * 0.3),
            ("Entities extracted", total_entities > 0),
            ("Relationships extracted", total_relationships > 0)
        ]
        
        passed = 0
        for criterion, result in success_criteria:
            status = "PASS" if result else "FAIL"
            print(f"  [{status}] {criterion}")
            if result:
                passed += 1
        
        print(f"\nResult: {passed}/{len(success_criteria)} criteria passed")
        
        if passed == len(success_criteria):
            print("\n" + "=" * 80)
            print("SUCCESS: FULL PIPELINE WORKING WITH SPLIT PHASE 4!")
            print("=" * 80)
        
        return results
        
    except Exception as e:
        print(f"\nERROR: Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = asyncio.run(test_full_pipeline())
    
    if results:
        print("\n[FINAL] Pipeline execution completed successfully")
    else:
        print("\n[FINAL] Pipeline execution failed")