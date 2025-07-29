#!/usr/bin/env python3
"""
Token Counter for Qualitative Coding System

Provides accurate token counting for Gemini API using tiktoken.
Handles batch processing with 1M tokens/minute API limit management.
"""

import tiktoken
import os
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenUsageStats:
    """Statistics for token usage across operations"""
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_api_calls: int
    estimated_cost_usd: float
    estimated_processing_minutes: float
    interviews_processed: int
    average_tokens_per_interview: float


@dataclass
class BatchTokenBudget:
    """Token budget for batch processing within API limits"""
    max_tokens_per_minute: int
    target_batch_size: int
    interviews_in_batch: List[str]
    total_input_tokens: int
    estimated_output_tokens: int
    estimated_processing_time_minutes: float
    api_calls_required: int


class TokenCounter:
    """Accurate token counting for Gemini API operations"""
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize token counter.
        
        Args:
            model_name: Model name for tiktoken (Gemini uses similar tokenization to GPT-4)
        """
        try:
            # Gemini tokenization is similar to GPT-4
            self.encoding = tiktoken.encoding_for_model(model_name)
            self.model_name = model_name
            logger.info(f"Initialized TokenCounter with {model_name} encoding")
        except Exception as e:
            logger.warning(f"Failed to load {model_name} encoding, falling back to cl100k_base: {e}")
            self.encoding = tiktoken.get_encoding("cl100k_base")
            self.model_name = "cl100k_base"
    
    def count_tokens(self, text: str) -> int:
        """
        Get accurate token count for text.
        
        Args:
            text: Input text to count tokens
            
        Returns:
            Exact number of tokens
        """
        if not text or not text.strip():
            return 0
        
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback to rough estimation
            return len(text.split()) * 1.3
    
    def count_tokens_batch(self, texts: List[str]) -> List[int]:
        """
        Count tokens for multiple texts efficiently.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of token counts corresponding to input texts
        """
        return [self.count_tokens(text) for text in texts]
    
    def fits_in_context(self, text: str, max_tokens: int = 1_000_000) -> bool:
        """
        Check if text fits within context window.
        
        Args:
            text: Text to check
            max_tokens: Maximum token limit (default: 1M for Gemini)
            
        Returns:
            True if text fits within limit
        """
        return self.count_tokens(text) <= max_tokens
    
    def estimate_three_phase_tokens(self, interview_text: str) -> Dict[str, int]:
        """
        Estimate token usage for three-phase qualitative coding.
        
        Args:
            interview_text: Raw interview text
            
        Returns:
            Dictionary with token estimates for each phase
        """
        input_tokens = self.count_tokens(interview_text)
        
        # Estimate prompt overhead for each phase
        phase_1_prompt_overhead = 500  # Open coding prompt
        phase_2_prompt_overhead = 800  # Axial coding prompt + Phase 1 results
        phase_3_prompt_overhead = 1200  # Selective coding prompt + Phase 1 & 2 results
        
        # Estimate output tokens per phase (conservative estimates)
        phase_1_output = min(20000, input_tokens * 0.3)  # Open codes
        phase_2_output = min(25000, input_tokens * 0.2)  # Categories
        phase_3_output = min(15000, input_tokens * 0.1)  # Themes
        
        return {
            'input_tokens_per_phase': input_tokens,
            'phase_1_prompt_tokens': phase_1_prompt_overhead,
            'phase_1_output_tokens': int(phase_1_output),
            'phase_1_total': input_tokens + phase_1_prompt_overhead + int(phase_1_output),
            
            'phase_2_prompt_tokens': phase_2_prompt_overhead,
            'phase_2_output_tokens': int(phase_2_output),
            'phase_2_total': input_tokens + phase_2_prompt_overhead + int(phase_2_output),
            
            'phase_3_prompt_tokens': phase_3_prompt_overhead,
            'phase_3_output_tokens': int(phase_3_output),
            'phase_3_total': input_tokens + phase_3_prompt_overhead + int(phase_3_output),
            
            'total_input_tokens': input_tokens * 3,  # Same interview text used 3 times
            'total_output_tokens': int(phase_1_output + phase_2_output + phase_3_output),
            'total_prompt_overhead': phase_1_prompt_overhead + phase_2_prompt_overhead + phase_3_prompt_overhead,
            'grand_total': (input_tokens * 3) + (phase_1_prompt_overhead + phase_2_prompt_overhead + phase_3_prompt_overhead) + int(phase_1_output + phase_2_output + phase_3_output)
        }
    
    def calculate_batch_budget(self, 
                              interview_texts: List[str],
                              max_tokens_per_minute: int = 1_000_000,
                              target_processing_minutes: float = 5.0) -> BatchTokenBudget:
        """
        Calculate optimal batch size within API token limits.
        
        Args:
            interview_texts: List of interview texts to process
            max_tokens_per_minute: API rate limit (default: 1M/min for Gemini)
            target_processing_minutes: Target time for batch completion
            
        Returns:
            BatchTokenBudget with optimal batching strategy
        """
        # Calculate token requirements for all interviews
        token_estimates = []
        for text in interview_texts:
            estimates = self.estimate_three_phase_tokens(text)
            token_estimates.append(estimates)
        
        # Calculate total token budget available
        total_budget = int(max_tokens_per_minute * target_processing_minutes)
        
        # Find optimal batch size
        current_batch = []
        current_tokens = 0
        
        for i, estimates in enumerate(token_estimates):
            interview_total = estimates['grand_total']
            
            if current_tokens + interview_total <= total_budget:
                current_batch.append(interview_texts[i])
                current_tokens += interview_total
            else:
                break
        
        # If no interviews fit, take just one (largest possible)
        if not current_batch and interview_texts:
            current_batch = [interview_texts[0]]
            current_tokens = token_estimates[0]['grand_total']
        
        # Calculate estimates
        batch_estimates = token_estimates[:len(current_batch)]
        total_input = sum(est['total_input_tokens'] for est in batch_estimates)
        total_output = sum(est['total_output_tokens'] for est in batch_estimates)
        total_api_calls = len(current_batch) * 3  # Three phases per interview
        estimated_time = (total_input + total_output) / max_tokens_per_minute
        
        return BatchTokenBudget(
            max_tokens_per_minute=max_tokens_per_minute,
            target_batch_size=len(current_batch),
            interviews_in_batch=current_batch,
            total_input_tokens=total_input,
            estimated_output_tokens=total_output,
            estimated_processing_time_minutes=estimated_time,
            api_calls_required=total_api_calls
        )
    
    def estimate_full_study(self, 
                           interview_texts: List[str],
                           cost_per_million_tokens: float = 0.50) -> TokenUsageStats:
        """
        Estimate total token usage and cost for complete study.
        
        Args:
            interview_texts: All interview texts to process
            cost_per_million_tokens: Cost per 1M tokens (approximate Gemini pricing)
            
        Returns:
            Complete usage statistics
        """
        total_input = 0
        total_output = 0
        
        for text in interview_texts:
            estimates = self.estimate_three_phase_tokens(text)
            total_input += estimates['total_input_tokens']
            total_output += estimates['total_output_tokens']
        
        total_tokens = total_input + total_output
        total_api_calls = len(interview_texts) * 3  # Three phases per interview
        estimated_cost = (total_tokens / 1_000_000) * cost_per_million_tokens
        estimated_minutes = total_tokens / 1_000_000  # 1M tokens/minute limit
        avg_tokens = total_tokens / len(interview_texts) if interview_texts else 0
        
        return TokenUsageStats(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            estimated_api_calls=total_api_calls,
            estimated_cost_usd=estimated_cost,
            estimated_processing_minutes=estimated_minutes,
            interviews_processed=len(interview_texts),
            average_tokens_per_interview=avg_tokens
        )
    
    def check_interview_feasibility(self, interview_text: str) -> Dict[str, Any]:
        """
        Check if single interview is feasible within token limits.
        
        Args:
            interview_text: Interview text to check
            
        Returns:
            Feasibility assessment
        """
        estimates = self.estimate_three_phase_tokens(interview_text)
        input_tokens = self.count_tokens(interview_text)
        
        # Check various limits
        fits_in_context = input_tokens < 900_000  # Leave room for prompts
        reasonable_cost = estimates['grand_total'] < 100_000  # Reasonable per-interview cost
        
        return {
            'feasible': fits_in_context and reasonable_cost,
            'input_tokens': input_tokens,
            'estimated_total_tokens': estimates['grand_total'],
            'fits_in_context': fits_in_context,
            'reasonable_cost': reasonable_cost,
            'warnings': self._generate_warnings(estimates, input_tokens),
            'token_breakdown': estimates
        }
    
    def _generate_warnings(self, estimates: Dict[str, int], input_tokens: int) -> List[str]:
        """Generate warnings about token usage"""
        warnings = []
        
        if input_tokens > 900_000:
            warnings.append(f"Interview very large ({input_tokens:,} tokens) - may not fit with prompts")
        
        if estimates['grand_total'] > 200_000:
            warnings.append(f"High token usage ({estimates['grand_total']:,} tokens) - expensive processing")
        
        if input_tokens > 500_000:
            warnings.append("Large interview may cause slower processing")
        
        return warnings


# Test/demo function
def test_token_counter():
    """Test token counter with real interview data"""
    import sys
    sys.path.append('.')
    from qc.parsing.docx_parser import DOCXParser
    
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
    test_token_counter()