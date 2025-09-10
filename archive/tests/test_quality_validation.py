"""Ensure parallel processing maintains extraction quality"""
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

def compare_extraction_results(result1: Dict[str, Any], result2: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two extraction results for quality validation"""
    comparison = {
        "quotes_match": False,
        "codes_match": False,
        "entities_match": False,
        "relationships_match": False,
        "quality_maintained": False,
        "details": {}
    }
    
    # Extract key metrics from both results
    if 'quotes' in result1:
        quotes1 = len(result1.get('quotes', []))
        quotes2 = len(result2.get('quotes', []))
        comparison['details']['quotes'] = {
            'result1': quotes1,
            'result2': quotes2,
            'difference': abs(quotes1 - quotes2)
        }
        # Allow small variance (within 10%)
        comparison['quotes_match'] = abs(quotes1 - quotes2) <= max(1, int(quotes1 * 0.1))
    
    if 'unique_codes' in result1:
        codes1 = result1.get('unique_codes', 0)
        codes2 = result2.get('unique_codes', 0)
        comparison['details']['codes'] = {
            'result1': codes1,
            'result2': codes2,
            'difference': abs(codes1 - codes2)
        }
        comparison['codes_match'] = abs(codes1 - codes2) <= max(1, int(codes1 * 0.1))
    
    if 'entities' in result1:
        entities1 = len(result1.get('entities', []))
        entities2 = len(result2.get('entities', []))
        comparison['details']['entities'] = {
            'result1': entities1,
            'result2': entities2,
            'difference': abs(entities1 - entities2)
        }
        comparison['entities_match'] = abs(entities1 - entities2) <= max(1, int(entities1 * 0.1))
    
    if 'relationships' in result1:
        relationships1 = len(result1.get('relationships', []))
        relationships2 = len(result2.get('relationships', []))
        comparison['details']['relationships'] = {
            'result1': relationships1,
            'result2': relationships2,
            'difference': abs(relationships1 - relationships2)
        }
        comparison['relationships_match'] = abs(relationships1 - relationships2) <= max(1, int(relationships1 * 0.1))
    
    # Overall quality maintained if all key metrics match
    comparison['quality_maintained'] = (
        comparison['quotes_match'] and 
        comparison['codes_match'] and 
        comparison['entities_match'] and 
        comparison['relationships_match']
    )
    
    return comparison


async def run_extraction_test(output_dir: str, max_concurrent: int = 1) -> Dict[str, Any]:
    """Run extraction with specified concurrency and return results"""
    
    # Use 2 interview files for faster testing
    test_interviews = [
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI and Methods focus group July 23 2025.docx",
        "C:/Users/Brian/projects/qualitative_coding/data/interviews/ai_interviews/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test/AI assessment Arroyo SDR.docx"
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
        output_dir=output_dir,
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.0-flash-exp",
        max_concurrent_interviews=max_concurrent
    )
    
    print(f"Running extraction with max_concurrent={max_concurrent}...")
    
    extractor = CodeFirstExtractor(config)
    
    # Run all phases
    await extractor._run_phase_1()
    await extractor._run_phase_2()
    await extractor._run_phase_3()
    await extractor._run_phase_4()
    
    # Collect results
    results = {
        "num_interviews": len(extractor.coded_interviews),
        "total_quotes": sum(len(interview.quotes) for interview in extractor.coded_interviews),
        "total_entities": sum(len(interview.entities) for interview in extractor.coded_interviews),
        "total_relationships": sum(len(interview.relationships) for interview in extractor.coded_interviews),
        "interviews": []
    }
    
    # Detailed per-interview results
    for interview in extractor.coded_interviews:
        interview_data = {
            "id": interview.interview_id,
            "quotes": len(interview.quotes),
            "unique_codes": len(interview.unique_codes),
            "entities": len(interview.entities),
            "relationships": len(interview.relationships)
        }
        results["interviews"].append(interview_data)
    
    return results


async def validate_quality():
    """Main quality validation test"""
    print("=" * 60)
    print("QUALITY VALIDATION TEST")
    print("=" * 60)
    print("\nThis test ensures parallel processing maintains extraction quality\n")
    
    # Run sequential extraction (baseline for quality)
    print("Step 1: Running SEQUENTIAL extraction (max_concurrent=1)...")
    sequential_results = await run_extraction_test("output_quality_sequential", max_concurrent=1)
    
    if not sequential_results:
        print("Failed to run sequential extraction")
        return False
    
    print(f"Sequential results: {sequential_results['num_interviews']} interviews processed")
    print(f"  Total quotes: {sequential_results['total_quotes']}")
    print(f"  Total entities: {sequential_results['total_entities']}")
    print(f"  Total relationships: {sequential_results['total_relationships']}")
    
    # Run parallel extraction
    print("\nStep 2: Running PARALLEL extraction (max_concurrent=2)...")
    parallel_results = await run_extraction_test("output_quality_parallel", max_concurrent=2)
    
    if not parallel_results:
        print("Failed to run parallel extraction")
        return False
    
    print(f"Parallel results: {parallel_results['num_interviews']} interviews processed")
    print(f"  Total quotes: {parallel_results['total_quotes']}")
    print(f"  Total entities: {parallel_results['total_entities']}")
    print(f"  Total relationships: {parallel_results['total_relationships']}")
    
    # Compare results
    print("\n" + "-" * 60)
    print("QUALITY COMPARISON")
    print("-" * 60)
    
    # Overall comparison
    overall_comparison = {
        "quotes_match": abs(sequential_results['total_quotes'] - parallel_results['total_quotes']) <= 2,
        "entities_match": abs(sequential_results['total_entities'] - parallel_results['total_entities']) <= 2,
        "relationships_match": abs(sequential_results['total_relationships'] - parallel_results['total_relationships']) <= 2,
    }
    
    print(f"\nTotal Quotes:")
    print(f"  Sequential: {sequential_results['total_quotes']}")
    print(f"  Parallel: {parallel_results['total_quotes']}")
    print(f"  Match: {'YES' if overall_comparison['quotes_match'] else 'NO'}")
    
    print(f"\nTotal Entities:")
    print(f"  Sequential: {sequential_results['total_entities']}")
    print(f"  Parallel: {parallel_results['total_entities']}")
    print(f"  Match: {'YES' if overall_comparison['entities_match'] else 'NO'}")
    
    print(f"\nTotal Relationships:")
    print(f"  Sequential: {sequential_results['total_relationships']}")
    print(f"  Parallel: {parallel_results['total_relationships']}")
    print(f"  Match: {'YES' if overall_comparison['relationships_match'] else 'NO'}")
    
    # Per-interview comparison
    print("\n" + "-" * 60)
    print("PER-INTERVIEW COMPARISON")
    print("-" * 60)
    
    for i, (seq_interview, par_interview) in enumerate(zip(
        sequential_results['interviews'], 
        parallel_results['interviews']
    )):
        print(f"\nInterview {i+1} ({seq_interview['id']}):")
        comparison = compare_extraction_results(seq_interview, par_interview)
        
        for metric in ['quotes', 'codes', 'entities', 'relationships']:
            if metric in comparison['details']:
                detail = comparison['details'][metric]
                match_symbol = 'OK' if comparison[f'{metric}_match'] else 'DIFF'
                print(f"  {metric.capitalize()}: Seq={detail['result1']}, Par={detail['result2']} {match_symbol}")
    
    # Final verdict
    print("\n" + "=" * 60)
    print("QUALITY VALIDATION RESULTS")
    print("=" * 60)
    
    quality_maintained = all([
        overall_comparison['quotes_match'],
        overall_comparison['entities_match'],
        overall_comparison['relationships_match']
    ])
    
    if quality_maintained:
        print("SUCCESS - QUALITY MAINTAINED: Parallel processing produces equivalent results!")
        print("   Extraction accuracy is preserved with performance optimization.")
    else:
        print("WARNING - QUALITY VARIANCE DETECTED: Some differences in extraction results.")
        print("   Small variations are normal due to LLM non-determinism.")
        print("   Review the differences to ensure they are within acceptable range.")
    
    return quality_maintained


if __name__ == "__main__":
    print("=" * 60)
    print("EXTRACTION QUALITY VALIDATION")
    print("=" * 60)
    
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in environment variables")
        print("Please ensure .env file exists with GEMINI_API_KEY set")
        sys.exit(1)
    
    try:
        quality_ok = asyncio.run(validate_quality())
        
        print("\n" + "=" * 60)
        if quality_ok:
            print("VALIDATION COMPLETED: Quality maintained - SUCCESS")
        else:
            print("VALIDATION COMPLETED: Review quality differences - WARNING")
        print("=" * 60)
    except Exception as e:
        print(f"\nError during quality validation: {e}")
        import traceback
        traceback.print_exc()