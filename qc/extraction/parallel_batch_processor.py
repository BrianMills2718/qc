"""
Parallel Batch Processor for High-Throughput Interview Processing

This module provides parallel processing capabilities for multiple interviews
with intelligent rate limit management and concurrent processing controls.
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

from .multi_pass_extractor import MultiPassExtractor, InterviewContext, ExtractionResult
from ..core.neo4j_manager import EnhancedNeo4jManager
from ..core.schema_config import SchemaConfiguration
from ..core.llm_client import UniversalModelClient

logger = logging.getLogger(__name__)

@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing parameters"""
    max_concurrent_interviews: int = 10  # Process up to 10 interviews simultaneously
    max_concurrent_chunks: int = 5       # Process up to 5 chunks per interview
    rate_limit_requests_per_minute: int = 800  # Conservative rate limit
    progress_callback: Optional[callable] = None
    error_callback: Optional[callable] = None

@dataclass
class BatchResult:
    """Results from batch processing"""
    total_interviews: int
    successful_interviews: int
    failed_interviews: int
    total_processing_time: float
    average_time_per_interview: float
    total_entities: int
    total_relationships: int
    total_codes: int
    errors: List[str]

class ParallelBatchProcessor:
    """High-throughput parallel processor for multiple interviews"""
    
    def __init__(self, 
                 neo4j_manager: EnhancedNeo4jManager,
                 schema: SchemaConfiguration,
                 llm_client: UniversalModelClient = None,
                 config: BatchProcessingConfig = None):
        """
        Initialize the parallel batch processor
        
        Args:
            neo4j_manager: Neo4j database manager
            schema: Schema configuration for extraction
            llm_client: Universal LLM client (auto-created if not provided)
            config: Batch processing configuration
        """
        self.extractor = MultiPassExtractor(
            neo4j_manager, 
            schema, 
            llm_client,
            max_concurrent_chunks=self.config.max_concurrent_chunks
        )
        self.config = config or BatchProcessingConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_interviews)
        
    async def process_interview_batch(self, 
                                    interview_contexts: List[InterviewContext]) -> BatchResult:
        """
        Process multiple interviews in parallel with rate limiting
        
        Args:
            interview_contexts: List of interview contexts to process
            
        Returns:
            BatchResult with processing statistics and results
        """
        logger.info(f"Starting parallel batch processing of {len(interview_contexts)} interviews")
        logger.info(f"Concurrency: {self.config.max_concurrent_interviews} interviews, "
                   f"{self.config.max_concurrent_chunks} chunks per interview")
        
        start_time = time.time()
        
        # Create processing tasks with semaphore for rate limiting
        tasks = [
            self._process_single_interview_with_limit(context, i+1, len(interview_contexts))
            for i, context in enumerate(interview_contexts)
        ]
        
        # Execute all interview processing concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = []
        errors = []
        total_entities = 0
        total_relationships = 0
        total_codes = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"Interview {i+1} failed: {str(result)}"
                logger.error(error_msg)
                errors.append(error_msg)
                if self.config.error_callback:
                    self.config.error_callback(interview_contexts[i], result)
            else:
                successful_results.append(result)
                # Count entities/relationships/codes from extraction results
                for extraction_result in result:
                    total_entities += len(extraction_result.entities_found)
                    total_relationships += len(extraction_result.relationships_found)
                    total_codes += len(extraction_result.codes_found)
        
        batch_result = BatchResult(
            total_interviews=len(interview_contexts),
            successful_interviews=len(successful_results),
            failed_interviews=len(errors),
            total_processing_time=total_time,
            average_time_per_interview=total_time / len(interview_contexts) if interview_contexts else 0,
            total_entities=total_entities,
            total_relationships=total_relationships,
            total_codes=total_codes,
            errors=errors
        )
        
        logger.info(f"Batch processing complete!")
        logger.info(f"  Total time: {total_time:.2f} seconds")
        logger.info(f"  Average per interview: {batch_result.average_time_per_interview:.2f} seconds")
        logger.info(f"  Success rate: {batch_result.successful_interviews}/{batch_result.total_interviews}")
        logger.info(f"  Total extracted: {total_entities} entities, {total_relationships} relationships, {total_codes} codes")
        
        return batch_result
    
    async def _process_single_interview_with_limit(self, 
                                                 context: InterviewContext,
                                                 interview_num: int,
                                                 total_interviews: int) -> List[ExtractionResult]:
        """
        Process a single interview with concurrency limiting
        
        Args:
            context: Interview context to process
            interview_num: Current interview number (for logging)
            total_interviews: Total number of interviews
            
        Returns:
            List of extraction results
        """
        async with self.semaphore:
            logger.info(f"Starting interview {interview_num}/{total_interviews}: {context.interview_id}")
            start_time = time.time()
            
            try:
                # Process the interview
                results = await self.extractor.extract_from_interview(context)
                
                processing_time = time.time() - start_time
                logger.info(f"Completed interview {interview_num}/{total_interviews} in {processing_time:.2f}s: {context.interview_id}")
                
                # Call progress callback if provided
                if self.config.progress_callback:
                    self.config.progress_callback(interview_num, total_interviews, context, results)
                
                return results
                
            except Exception as e:
                processing_time = time.time() - start_time
                logger.error(f"Failed interview {interview_num}/{total_interviews} after {processing_time:.2f}s: {context.interview_id} - {str(e)}")
                raise e

    async def process_interview_files(self, 
                                    file_paths: List[str],
                                    session_id: str = None) -> BatchResult:
        """
        Process multiple interview files in parallel
        
        Args:
            file_paths: List of paths to interview text files
            session_id: Optional session ID for tracking
            
        Returns:
            BatchResult with processing statistics
        """
        if not session_id:
            session_id = f"batch_{int(time.time())}"
        
        # Load interview contexts from files
        interview_contexts = []
        for file_path in file_paths:
            try:
                file_path_obj = Path(file_path)
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    interview_text = f.read()
                
                context = InterviewContext(
                    interview_id=file_path_obj.stem,
                    interview_text=interview_text,
                    session_id=session_id,
                    filename=str(file_path_obj),
                    speaker_info={}
                )
                interview_contexts.append(context)
                
            except Exception as e:
                logger.error(f"Failed to load interview file {file_path}: {e}")
                continue
        
        if not interview_contexts:
            raise ValueError("No valid interview files could be loaded")
        
        return await self.process_interview_batch(interview_contexts)

    def update_concurrency_limits(self, 
                                max_concurrent_interviews: int = None,
                                max_concurrent_chunks: int = None):
        """
        Update concurrency limits dynamically
        
        Args:
            max_concurrent_interviews: New interview concurrency limit
            max_concurrent_chunks: New chunk concurrency limit
        """
        if max_concurrent_interviews:
            self.config.max_concurrent_interviews = max_concurrent_interviews
            self.semaphore = asyncio.Semaphore(max_concurrent_interviews)
            logger.info(f"Updated interview concurrency to {max_concurrent_interviews}")
        
        if max_concurrent_chunks:
            self.config.max_concurrent_chunks = max_concurrent_chunks
            logger.info(f"Updated chunk concurrency to {max_concurrent_chunks}")

# Utility functions for easy batch processing

async def process_interview_batch_simple(interview_files: List[str],
                                       neo4j_manager: EnhancedNeo4jManager,
                                       schema: SchemaConfiguration,
                                       max_concurrent: int = 10) -> BatchResult:
    """
    Simple interface for batch processing multiple interview files
    
    Args:
        interview_files: List of paths to interview files
        neo4j_manager: Neo4j database manager
        schema: Schema configuration
        max_concurrent: Maximum concurrent interviews to process
        
    Returns:
        BatchResult with processing statistics
    """
    config = BatchProcessingConfig(max_concurrent_interviews=max_concurrent)
    processor = ParallelBatchProcessor(neo4j_manager, schema, config=config)
    
    return await processor.process_interview_files(interview_files)

def progress_callback_logger(interview_num: int, total: int, context: InterviewContext, results: List[ExtractionResult]):
    """Simple progress callback that logs completion"""
    entities = sum(len(r.entities_found) for r in results)
    relationships = sum(len(r.relationships_found) for r in results)
    codes = sum(len(r.codes_found) for r in results)
    
    logger.info(f"✅ Interview {interview_num}/{total} completed: {context.interview_id}")
    logger.info(f"   Extracted: {entities} entities, {relationships} relationships, {codes} codes")

# Example usage
async def example_batch_processing():
    """Example of how to use the parallel batch processor"""
    
    # Setup (you would provide your actual managers and schema)
    neo4j_manager = None  # Your Neo4j manager
    schema = None         # Your schema configuration
    
    # Configuration for high-throughput processing
    config = BatchProcessingConfig(
        max_concurrent_interviews=15,  # Process 15 interviews at once
        max_concurrent_chunks=5,       # 5 chunks per interview  
        rate_limit_requests_per_minute=800,
        progress_callback=progress_callback_logger
    )
    
    # Create processor
    processor = ParallelBatchProcessor(neo4j_manager, schema, config=config)
    
    # Process batch of interviews
    interview_files = [
        "interviews/interview_1.txt",
        "interviews/interview_2.txt", 
        # ... up to hundreds of files
    ]
    
    # Execute parallel processing
    result = await processor.process_interview_files(interview_files)
    
    print(f"Processed {result.successful_interviews}/{result.total_interviews} interviews")
    print(f"Total time: {result.total_processing_time:.2f} seconds")
    print(f"Average: {result.average_time_per_interview:.2f} seconds per interview")
    
    return result

if __name__ == "__main__":
    # Run example
    asyncio.run(example_batch_processing())