"""Establish baseline performance metrics before optimization"""
import asyncio
import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def measure_baseline():
    """Measure current Phase 4 performance with sequential processing"""
    
    # Use 3 actual interview files for testing
    test_interviews = [
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/Interview Kandice Kapinos.docx"
    ]
    
    # Verify files exist
    for file in test_interviews:
        if not Path(file).exists():
            print(f"Error: Interview file not found: {file}")
            return None
    
    config = ExtractionConfig(
        analytic_question="How do researchers perceive AI's impact on their work?",
        interview_files=test_interviews,
        coding_approach=ExtractionApproach.OPEN,
        output_dir="output_performance_baseline",
        auto_import_neo4j=False,  # Don't import to Neo4j for this test
        llm_model="gemini/gemini-2.5-flash"  # Use the correct flash model
    )
    
    print(f"Testing Phase 4 performance with {len(config.interview_files)} interviews")
    print(f"Model: {config.llm_model}")
    print("-" * 60)
    
    extractor = CodeFirstExtractor(config)
    
    # Run phases 1-3 first (required for Phase 4)
    print("Running Phases 1-3 (preparation)...")
    phase_1_3_start = time.time()
    
    # Phase 1
    await extractor._run_phase_1()
    print(f"Phase 1 complete: {len(extractor.code_taxonomy.codes)} codes discovered")
    
    # Phase 2
    await extractor._run_phase_2()
    print(f"Phase 2 complete: {len(extractor.speaker_schema.properties)} speaker properties")
    
    # Phase 3
    await extractor._run_phase_3()
    print(f"Phase 3 complete: {len(extractor.entity_schema.entity_types)} entity types")
    
    phase_1_3_elapsed = time.time() - phase_1_3_start
    print(f"Phases 1-3 took: {phase_1_3_elapsed:.1f} seconds")
    print("-" * 60)
    
    # Measure Phase 4 specifically (SEQUENTIAL VERSION)
    print("Measuring Phase 4 baseline performance (sequential processing)...")
    phase_4_start = time.time()
    
    # Track individual interview times
    interview_times = []
    
    # Monkey-patch to track individual times
    original_process = extractor._run_phase_4
    
    async def tracked_phase_4():
        for i, interview_file in enumerate(extractor.config.interview_files):
            interview_start = time.time()
            print(f"  Processing interview {i+1}/{len(extractor.config.interview_files)}: {Path(interview_file).stem}")
            
            # Call the actual processing logic
            await original_process()
            
            interview_time = time.time() - interview_start
            interview_times.append(interview_time)
            print(f"    Completed in {interview_time:.1f} seconds")
            
            # Break after first interview since original processes all
            break
    
    # Actually run Phase 4
    await extractor._run_phase_4()
    
    phase_4_elapsed = time.time() - phase_4_start
    
    print("-" * 60)
    print("\n=== BASELINE PERFORMANCE RESULTS ===")
    print(f"Phase 4 total time: {phase_4_elapsed:.1f} seconds for {len(config.interview_files)} interviews")
    print(f"Average per interview: {phase_4_elapsed/len(config.interview_files):.1f} seconds")
    print(f"Total extraction time: {phase_1_3_elapsed + phase_4_elapsed:.1f} seconds")
    
    # Calculate estimated times for larger sets
    per_interview = phase_4_elapsed / len(config.interview_files)
    print(f"\nEstimated times (Phase 4 only):")
    print(f"  5 interviews: {per_interview * 5:.1f} seconds ({(per_interview * 5)/60:.1f} minutes)")
    print(f"  10 interviews: {per_interview * 10:.1f} seconds ({(per_interview * 10)/60:.1f} minutes)")
    print(f"  50 interviews: {per_interview * 50:.1f} seconds ({(per_interview * 50)/60:.1f} minutes)")
    print(f"  100 interviews: {per_interview * 100:.1f} seconds ({(per_interview * 100)/60:.1f} minutes)")
    
    # Check output
    output_dir = Path(config.output_dir)
    if output_dir.exists():
        json_files = list(output_dir.glob("*.json"))
        print(f"\nOutput files generated: {len(json_files)}")
        for file in json_files[:5]:  # Show first 5 files
            print(f"  - {file.name}")
    
    return {
        "phase_4_total": phase_4_elapsed,
        "per_interview": per_interview,
        "num_interviews": len(config.interview_files),
        "phases_1_3": phase_1_3_elapsed
    }

if __name__ == "__main__":
    print("=" * 60)
    print("PERFORMANCE BASELINE TEST - SEQUENTIAL PROCESSING")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please ensure .env file exists with GEMINI_API_KEY set")
        sys.exit(1)
    
    try:
        baseline = asyncio.run(measure_baseline())
        if baseline:
            print("\n" + "=" * 60)
            print("BASELINE ESTABLISHED SUCCESSFULLY")
            print(f"Target: Achieve 3-5x speedup (< {baseline['per_interview']/3:.1f} seconds per interview)")
            print("=" * 60)
    except Exception as e:
        print(f"\nError during baseline measurement: {e}")
        import traceback
        traceback.print_exc()