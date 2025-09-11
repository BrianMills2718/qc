"""Test optimized parallel performance of Phase 4"""
import asyncio
import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def measure_optimized():
    """Measure optimized Phase 4 performance with parallel processing"""
    
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
        output_dir="output_performance_optimized",
        auto_import_neo4j=False,  # Don't import to Neo4j for this test
        llm_model="gemini/gemini-2.5-flash",  # Use the correct flash model
        max_concurrent_interviews=3  # Test with all 3 concurrent since we have high rate limits
    )
    
    print(f"Testing OPTIMIZED Phase 4 performance with {len(config.interview_files)} interviews")
    print(f"Model: {config.llm_model}")
    print(f"Max concurrent: {config.max_concurrent_interviews}")
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
    
    # Measure Phase 4 specifically (PARALLEL VERSION)
    print("Measuring Phase 4 OPTIMIZED performance (parallel processing)...")
    print(f"Processing {len(config.interview_files)} interviews simultaneously...")
    phase_4_start = time.time()
    
    # Run optimized Phase 4
    await extractor._run_phase_4()
    
    phase_4_elapsed = time.time() - phase_4_start
    
    print("-" * 60)
    print("\n=== OPTIMIZED PERFORMANCE RESULTS ===")
    print(f"Phase 4 total time: {phase_4_elapsed:.1f} seconds for {len(config.interview_files)} interviews")
    print(f"Average per interview: {phase_4_elapsed/len(config.interview_files):.1f} seconds")
    print(f"Total extraction time: {phase_1_3_elapsed + phase_4_elapsed:.1f} seconds")
    
    # Calculate estimated times for larger sets
    # With parallel processing, time should be roughly constant up to max_concurrent
    effective_time_per_batch = phase_4_elapsed  # Time for one batch of max_concurrent
    batch_size = config.max_concurrent_interviews
    
    print(f"\nEstimated times with parallel processing (Phase 4 only):")
    print(f"Batch size: {batch_size} interviews")
    
    for num in [5, 10, 50, 100]:
        num_batches = (num + batch_size - 1) // batch_size  # Ceiling division
        estimated_time = effective_time_per_batch * num_batches
        print(f"  {num} interviews: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
    
    # Check output quality
    output_dir = Path(config.output_dir)
    if output_dir.exists():
        json_files = list(output_dir.glob("**/*.json"))
        print(f"\nOutput files generated: {len(json_files)}")
        
        # Count interviews processed
        interview_dir = output_dir / "interviews"
        if interview_dir.exists():
            interview_files = list(interview_dir.glob("*.json"))
            print(f"Interview files: {len(interview_files)}")
            
            # Check that all interviews were processed
            if len(interview_files) == len(config.interview_files):
                print("SUCCESS: All interviews successfully processed")
            else:
                print(f"WARNING: Only {len(interview_files)}/{len(config.interview_files)} interviews processed")
    
    return {
        "phase_4_total": phase_4_elapsed,
        "per_interview": phase_4_elapsed / len(config.interview_files),
        "num_interviews": len(config.interview_files),
        "phases_1_3": phase_1_3_elapsed,
        "max_concurrent": config.max_concurrent_interviews
    }


async def compare_with_baseline():
    """Compare optimized performance with baseline"""
    print("\n" + "=" * 60)
    print("PERFORMANCE COMPARISON")
    print("=" * 60)
    
    # Baseline numbers (from sequential processing)
    # These would be from running test_performance_baseline.py
    baseline_per_interview = 60.0  # Estimated 60 seconds per interview sequentially
    
    # Run optimized test
    optimized = await measure_optimized()
    
    if optimized:
        speedup = baseline_per_interview / (optimized['per_interview'])
        
        print(f"\nSPEEDUP ANALYSIS:")
        print(f"Baseline (sequential): ~{baseline_per_interview:.1f} seconds per interview")
        print(f"Optimized (parallel): {optimized['per_interview']:.1f} seconds per interview")
        print(f"SPEEDUP FACTOR: {speedup:.1f}x")
        
        if speedup >= 3.0:
            print("SUCCESS: TARGET MET - Achieved 3x+ speedup!")
        elif speedup >= 2.0:
            print("PARTIAL SUCCESS: Achieved 2x+ speedup")
        else:
            print("NEEDS IMPROVEMENT: Speedup less than 2x")
        
        # Time savings calculation
        time_saved_50 = (baseline_per_interview * 50 - optimized['phase_4_total'] * (50 // optimized['max_concurrent'] + 1)) / 60
        print(f"\nTime saved for 50 interviews: {time_saved_50:.1f} minutes")
        
        return optimized


if __name__ == "__main__":
    print("=" * 60)
    print("PERFORMANCE OPTIMIZATION TEST - PARALLEL PROCESSING")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please ensure .env file exists with GEMINI_API_KEY set")
        sys.exit(1)
    
    try:
        result = asyncio.run(compare_with_baseline())
        if result:
            print("\n" + "=" * 60)
            print("OPTIMIZATION TEST COMPLETED SUCCESSFULLY")
            print("=" * 60)
    except Exception as e:
        print(f"\nError during optimization test: {e}")
        import traceback
        traceback.print_exc()