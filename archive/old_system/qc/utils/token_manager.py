"""
Token Management for LLM API Calls

Handles token counting, chunking, and optimization for Gemini's 1M token context window.
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
import tiktoken
from .error_handler import TokenizationError

logger = logging.getLogger(__name__)


class TokenLimitError(Exception):
    """Raised when token limit would be exceeded"""
    pass


class TokenManager:
    """
    Manages token counting and chunking for LLM calls.
    
    Uses cl100k_base encoding as approximation for Gemini token counting.
    """
    
    def __init__(self, max_tokens: int = 900000, chunk_size: int = 500000):
        """
        Initialize token manager.
        
        Args:
            max_tokens: Maximum tokens for a single call (default 900K, leaving 100K buffer)
            chunk_size: Size of chunks when splitting large texts
        """
        self.max_tokens = max_tokens
        self.chunk_size = chunk_size
        
        # Initialize tiktoken encoder (cl100k_base is a good approximation)
        try:
            self.encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Failed to load tiktoken encoder: {e}")
            raise TokenizationError(f"Token encoder initialization failed: {e}") from e
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        if self.encoder:
            try:
                return len(self.encoder.encode(text))
            except Exception as e:
                logger.error(f"Token encoding failed: {e}")
                raise TokenizationError(f"Token encoding failed: {e}") from e
        else:
            raise TokenizationError("Token encoder not initialized - cannot count tokens")
    
    def validate_prompt_size(self, prompt: str, max_response_tokens: int = 4096) -> bool:
        """
        Check if prompt size is within limits.
        
        Args:
            prompt: The prompt to validate
            max_response_tokens: Expected max tokens in response
            
        Returns:
            True if within limits
            
        Raises:
            TokenLimitError: If prompt is too large
        """
        prompt_tokens = self.count_tokens(prompt)
        total_tokens = prompt_tokens + max_response_tokens
        
        if total_tokens > self.max_tokens:
            raise TokenLimitError(
                f"Prompt too large: {prompt_tokens} tokens + {max_response_tokens} response tokens = "
                f"{total_tokens} total (max: {self.max_tokens})"
            )
        
        logger.debug(f"Token count: {prompt_tokens} prompt + {max_response_tokens} response = {total_tokens} total")
        return True
    
    def chunk_text(self, text: str, overlap: int = 1000) -> List[str]:
        """
        Split large text into chunks that fit within token limits.
        
        Args:
            text: Text to chunk
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if self.encoder:
            tokens = self.encoder.encode(text)
        else:
            # Fallback: split by characters
            chars_per_chunk = self.chunk_size * 4  # Approximate 4 chars per token
            chunks = []
            for i in range(0, len(text), chars_per_chunk - overlap * 4):
                chunks.append(text[i:i + chars_per_chunk])
            return chunks
        
        chunks = []
        total_tokens = len(tokens)
        
        if total_tokens <= self.chunk_size:
            return [text]
        
        # Create overlapping chunks
        for i in range(0, total_tokens, self.chunk_size - overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # If we've processed all tokens, break
            if i + self.chunk_size >= total_tokens:
                break
        
        logger.info(f"Split {total_tokens} tokens into {len(chunks)} chunks")
        return chunks
    
    def optimize_prompt(self, prompt: str, max_size: Optional[int] = None) -> str:
        """
        Optimize prompt to fit within token limits.
        
        Args:
            prompt: Original prompt
            max_size: Maximum allowed tokens (uses self.max_tokens if not specified)
            
        Returns:
            Optimized prompt
        """
        max_size = max_size or self.max_tokens
        current_tokens = self.count_tokens(prompt)
        
        if current_tokens <= max_size:
            return prompt
        
        # Strategy: Remove examples and redundant instructions
        lines = prompt.split('\n')
        
        # First pass: Remove example sections
        filtered_lines = []
        skip_examples = False
        for line in lines:
            if 'example' in line.lower() or 'e.g.' in line.lower():
                skip_examples = True
            elif skip_examples and line.strip() == '':
                skip_examples = False
            elif not skip_examples:
                filtered_lines.append(line)
        
        optimized = '\n'.join(filtered_lines)
        new_tokens = self.count_tokens(optimized)
        
        if new_tokens <= max_size:
            logger.info(f"Optimized prompt from {current_tokens} to {new_tokens} tokens")
            return optimized
        
        # Second pass: Truncate if still too large
        if self.encoder:
            tokens = self.encoder.encode(optimized)
            truncated_tokens = tokens[:max_size - 100]  # Leave some buffer
            optimized = self.encoder.decode(truncated_tokens)
        else:
            # Character-based truncation
            max_chars = (max_size - 100) * 4
            optimized = optimized[:max_chars]
        
        logger.warning(f"Had to truncate prompt from {current_tokens} to {self.count_tokens(optimized)} tokens")
        return optimized
    
    def estimate_interview_chunks(self, interview_text: str) -> int:
        """
        Estimate how many chunks an interview will need.
        
        Args:
            interview_text: The interview text
            
        Returns:
            Number of chunks needed
        """
        tokens = self.count_tokens(interview_text)
        chunks_needed = (tokens + self.chunk_size - 1) // self.chunk_size
        return max(1, chunks_needed)
    
    def get_token_usage_stats(self, prompts: List[str], responses: List[str]) -> Dict[str, Any]:
        """
        Calculate token usage statistics.
        
        Args:
            prompts: List of prompts sent
            responses: List of responses received
            
        Returns:
            Dictionary with usage statistics
        """
        prompt_tokens = sum(self.count_tokens(p) for p in prompts)
        response_tokens = sum(self.count_tokens(r) for r in responses)
        total_tokens = prompt_tokens + response_tokens
        
        return {
            "prompt_tokens": prompt_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "prompts_count": len(prompts),
            "responses_count": len(responses),
            "avg_prompt_tokens": prompt_tokens // len(prompts) if prompts else 0,
            "avg_response_tokens": response_tokens // len(responses) if responses else 0,
            "utilization_percent": (total_tokens / self.max_tokens) * 100
        }