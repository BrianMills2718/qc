"""Simple test of extraction pipeline to identify bottleneck"""
import asyncio
import sys
import time
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def test_extraction():
    """Test extraction with timing"""
    
    config = ExtractionConfig(
        analytic_question="How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?",
        interview_files=[
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx"
        ],
        coding_approach=ExtractionApproach.OPEN,
        speaker_approach=ExtractionApproach.OPEN,
        entity_approach=ExtractionApproach.OPEN,
        output_dir="output_test_simple",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        temperature=0.1
    )
    
    extractor = CodeFirstExtractor(config)
    
    # Test each phase individually
    print("Starting extraction test with 1 interview...")
    
    # Phase 1
    print("\n=== Phase 1: Code Discovery ===")
    start = time.time()
    await extractor._run_phase_1()
    print(f"Phase 1 completed in {time.time() - start:.1f} seconds")
    print(f"Discovered {len(extractor.code_taxonomy.codes)} codes")
    
    # Phase 2
    print("\n=== Phase 2: Speaker Schema Discovery ===")
    start = time.time()
    await extractor._run_phase_2()
    print(f"Phase 2 completed in {time.time() - start:.1f} seconds")
    print(f"Discovered {len(extractor.speaker_schema.properties)} speaker properties")
    
    # Phase 3
    print("\n=== Phase 3: Entity/Relationship Schema Discovery ===")
    start = time.time()
    await extractor._run_phase_3()
    print(f"Phase 3 completed in {time.time() - start:.1f} seconds")
    if extractor.entity_schema:
        print(f"Discovered {len(extractor.entity_schema.entity_types)} entity types")
        print(f"Discovered {len(extractor.entity_schema.relationship_types)} relationship types")
    else:
        print("ERROR: Phase 3 returned None!")
    
    # Phase 4  
    print("\n=== Phase 4: Apply Schemas to Interview ===")
    start = time.time()
    await extractor._run_phase_4()
    print(f"Phase 4 completed in {time.time() - start:.1f} seconds")
    print(f"Processed {len(extractor.coded_interviews)} interviews")
    
    print("\n=== Extraction Complete ===")

if __name__ == "__main__":
    asyncio.run(test_extraction())