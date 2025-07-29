#!/usr/bin/env python3
"""Standalone test for token counter"""

from qc.utils.token_counter import TokenCounter
from qc.parsing.docx_parser import DOCXParser
from pathlib import Path

def main():
    print("Testing Token Counter with Real Interview Data\n")
    
    # Initialize components
    parser = DOCXParser()
    counter = TokenCounter()
    
    # Test with actual interview files
    ai_interviews_path = Path("data/interviews/AI_Interviews_all_2025.0728/Interviews")
    
    if ai_interviews_path.exists():
        print(f"Loading interviews from: {ai_interviews_path}")
        
        # Parse all interviews
        results = parser.parse_directory(ai_interviews_path)
        successful_results = [r for r in results if r['parsing_info']['success']]
        
        if successful_results:
            # Get interview texts
            interview_texts = [r['content'] for r in successful_results]
            
            print(f"Loaded {len(interview_texts)} interviews")
            
            # Test individual interview feasibility
            print("\n=== Individual Interview Analysis ===")
            largest_interview = max(successful_results, key=lambda r: r['estimated_tokens'])
            feasibility = counter.check_interview_feasibility(largest_interview['content'])
            
            print(f"Largest interview: {largest_interview['metadata']['file_name']}")
            print(f"  Input tokens (accurate): {feasibility['input_tokens']:,}")
            print(f"  Estimated total (3-phase): {feasibility['estimated_total_tokens']:,}")
            print(f"  Feasible: {feasibility['feasible']}")
            if feasibility['warnings']:
                for warning in feasibility['warnings']:
                    print(f"  WARNING: {warning}")
            
            # Test batch optimization
            print("\n=== Batch Processing Analysis ===")
            batch_budget = counter.calculate_batch_budget(interview_texts, target_processing_minutes=10.0)
            
            print(f"Optimal batch size: {batch_budget.target_batch_size} interviews")
            print(f"Total input tokens: {batch_budget.total_input_tokens:,}")
            print(f"Estimated output tokens: {batch_budget.estimated_output_tokens:,}")
            print(f"API calls required: {batch_budget.api_calls_required}")
            print(f"Estimated processing time: {batch_budget.estimated_processing_time_minutes:.1f} minutes")
            
            # Test full study estimation
            print("\n=== Complete Study Estimation ===")
            study_stats = counter.estimate_full_study(interview_texts)
            
            print(f"Total interviews: {study_stats.interviews_processed}")
            print(f"Total tokens: {study_stats.total_tokens:,}")
            print(f"Total API calls: {study_stats.estimated_api_calls}")
            print(f"Estimated cost: ${study_stats.estimated_cost_usd:.2f}")
            print(f"Estimated processing time: {study_stats.estimated_processing_minutes:.1f} minutes")
            print(f"Average tokens per interview: {study_stats.average_tokens_per_interview:.0f}")
            
        else:
            print("No interviews successfully parsed")
    else:
        print(f"Interview directory not found: {ai_interviews_path}")

if __name__ == "__main__":
    main()