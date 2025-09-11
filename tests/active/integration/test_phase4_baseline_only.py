"""Focused Phase 4 baseline test using existing schemas"""
import asyncio
import time
import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def measure_phase4_baseline():
    """Measure Phase 4 performance using existing schemas from previous runs"""
    
    test_interviews = [
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx"
    ]
    
    config = ExtractionConfig(
        analytic_question="How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?",
        interview_files=test_interviews,
        coding_approach=ExtractionApproach.OPEN,
        speaker_approach=ExtractionApproach.OPEN,
        entity_approach=ExtractionApproach.OPEN,
        output_dir="output_phase4_baseline",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash"
    )
    
    print("=== PHASE 4 BASELINE TEST ===")
    print(f"Testing Phase 4 SEQUENTIAL processing with {len(test_interviews)} interviews")
    print("Using schemas from: output_single_test/")
    
    extractor = CodeFirstExtractor(config)
    
    # Load existing schemas instead of regenerating
    baseline_dir = Path("output_single_test")
    if not baseline_dir.exists():
        print("ERROR: Need to run Phases 1-3 first - output_performance_baseline/ not found")
        return None
    
    # Load schemas from previous run
    try:
        with open(baseline_dir / "taxonomy.json") as f:
            taxonomy_data = json.load(f)
        with open(baseline_dir / "speaker_schema.json") as f:
            speaker_data = json.load(f)
        with open(baseline_dir / "entity_schema.json") as f:
            entity_data = json.load(f)
            
        # Import schemas
        from src.qc.extraction.code_first_schemas import CodeTaxonomy, SpeakerPropertySchema, EntityRelationshipSchema
        extractor.code_taxonomy = CodeTaxonomy(**taxonomy_data)
        extractor.speaker_schema = SpeakerPropertySchema(**speaker_data)
        extractor.entity_schema = EntityRelationshipSchema(**entity_data)
        
        print(f"[OK] Loaded schemas: {len(extractor.code_taxonomy.codes)} codes, {len(extractor.speaker_schema.properties)} speaker props, {len(extractor.entity_schema.entity_types)} entity types")
        
    except Exception as e:
        print(f"ERROR loading schemas: {e}")
        return None
    
    # Now measure Phase 4 performance
    print("\n[TIME] Starting Phase 4 sequential baseline measurement...")
    phase4_start = time.time()
    
    await extractor._run_phase_4()
    
    phase4_elapsed = time.time() - phase4_start
    
    # Results
    print("\n=== PHASE 4 BASELINE RESULTS ===")
    print(f"[TIME] Phase 4 time: {phase4_elapsed:.1f} seconds")
    print(f"[STAT] Per interview: {phase4_elapsed/len(test_interviews):.1f} seconds")
    print(f"[INFO] Interviews processed: {len(extractor.coded_interviews)}")
    
    # Extrapolation
    per_interview = phase4_elapsed / len(test_interviews)
    print(f"\n[SCALE] Scaling estimates:")
    print(f"   5 interviews: {per_interview * 5/60:.1f} minutes")
    print(f"  10 interviews: {per_interview * 10/60:.1f} minutes") 
    print(f"  50 interviews: {per_interview * 50/60:.1f} minutes")
    print(f" 100 interviews: {per_interview * 100/60:.1f} minutes")
    
    # Target for optimization
    target_time = phase4_elapsed / 3  # 3x speedup target
    print(f"\n[TARGET] Optimization target: <{target_time:.1f} seconds (3x speedup)")
    
    return {
        'phase4_time': phase4_elapsed,
        'per_interview': per_interview,
        'interviews_processed': len(extractor.coded_interviews),
        'target_time': target_time
    }

if __name__ == "__main__":
    import os
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] GEMINI_API_KEY not found")
        sys.exit(1)
        
    try:
        result = asyncio.run(measure_phase4_baseline())
        if result:
            print(f"\n[SUCCESS] BASELINE ESTABLISHED: {result['phase4_time']:.1f}s total, {result['per_interview']:.1f}s per interview")
        else:
            print("[ERROR] BASELINE FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)