"""Run only Phase 4 using existing schemas"""
import asyncio
import sys
import json
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import (
    ExtractionConfig, ExtractionApproach, 
    CodeTaxonomy, SpeakerPropertySchema, EntityRelationshipSchema
)

async def run_phase4_only():
    """Run Phase 4 using existing schemas from output_single_test"""
    
    config = ExtractionConfig(
        analytic_question="How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?",
        interview_files=[
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx",
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx",
            "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx"
        ],
        coding_approach=ExtractionApproach.OPEN,
        output_dir="output_single_test",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        max_concurrent_interviews=3  # Process 3 interviews in parallel
    )
    
    extractor = CodeFirstExtractor(config)
    
    # Load existing schemas
    print("Loading existing schemas...")
    
    with open("output_single_test/taxonomy.json", "r", encoding="utf-8") as f:
        taxonomy_data = json.load(f)
    extractor.code_taxonomy = CodeTaxonomy(**taxonomy_data)
    print(f"Loaded {extractor.code_taxonomy.total_codes} codes")
    
    with open("output_single_test/speaker_schema.json", "r", encoding="utf-8") as f:
        speaker_data = json.load(f)
    extractor.speaker_schema = SpeakerPropertySchema(**speaker_data)
    print(f"Loaded {len(extractor.speaker_schema.properties)} speaker properties")
    
    with open("output_single_test/entity_schema.json", "r", encoding="utf-8") as f:
        entity_data = json.load(f)
    extractor.entity_schema = EntityRelationshipSchema(**entity_data)
    print(f"Loaded {len(extractor.entity_schema.entity_types)} entity types and {len(extractor.entity_schema.relationship_types)} relationship types")
    
    # Run Phase 4 only
    print("\nRunning Phase 4 with relationship fixer...")
    await extractor._run_phase_4()
    
    print(f"\nPhase 4 complete: {len(extractor.coded_interviews)} interviews processed")
    
    if extractor.coded_interviews:
        # Save the results
        from qc.extraction.code_first_schemas import ExtractionResults
        from datetime import datetime
        
        # Aggregate global data
        global_entities, global_relationships = extractor._aggregate_global_data()
        
        results = ExtractionResults(
            config=config,
            code_taxonomy=extractor.code_taxonomy,
            speaker_schema=extractor.speaker_schema,
            entity_relationship_schema=extractor.entity_schema,
            coded_interviews=extractor.coded_interviews,
            global_entities=global_entities,
            global_relationships=global_relationships,
            total_interviews_processed=len(extractor.coded_interviews),
            total_quotes_extracted=sum(ci.total_quotes for ci in extractor.coded_interviews),
            total_unique_speakers=len(set(
                speaker.name for ci in extractor.coded_interviews 
                for speaker in ci.speakers
            )),
            total_unique_entities=len(global_entities),
            total_unique_relationships=len(global_relationships),
            extraction_timestamp=datetime.now().isoformat(),
            total_processing_time_seconds=0.0,
            llm_tokens_used=extractor.total_tokens_used,
            overall_confidence=0.8
        )
        
        # Save outputs
        await extractor._save_outputs(results)
        
        print(f"\nExtraction results saved to {config.output_dir}/")
        print(f"Total quotes extracted: {results.total_quotes_extracted}")
        print(f"Total unique entities: {results.total_unique_entities}")
        print(f"Total unique relationships: {results.total_unique_relationships}")
        
        # Show sample results
        if extractor.coded_interviews[0].quotes:
            first_quote = extractor.coded_interviews[0].quotes[0]
            print(f"\nSample quote:")
            print(f"  Text: {first_quote.text[:100]}...")
            print(f"  Speaker: {first_quote.speaker.name}")
            print(f"  Codes: {first_quote.code_names}")
    else:
        print("\nNo interviews were successfully processed")

if __name__ == "__main__":
    asyncio.run(run_phase4_only())