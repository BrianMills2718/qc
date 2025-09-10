"""
Parallel version of Phase 4 for Code-First Extractor
"""
import asyncio
from typing import List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

async def process_interview_parallel(self, interview_file: str) -> 'CodedInterview':
    """Process a single interview (for parallel execution)"""
    try:
        logger.info(f"Processing interview: {interview_file}")
        
        # Read interview content
        interview_text = self._read_interview_file(interview_file)
        interview_id = Path(interview_file).stem
        
        # Phase 4A: Extract quotes and speakers
        logger.info(f"Phase 4A for {interview_id}: Extracting quotes and speakers...")
        quotes_prompt = self._build_quotes_speakers_prompt(
            interview_text=interview_text,
            interview_id=interview_id
        )
        
        quotes_and_speakers = await self.llm.extract_structured(
            prompt=quotes_prompt,
            schema=QuotesAndSpeakers,
            max_tokens=None
        )
        
        logger.info(f"{interview_id}: Extracted {quotes_and_speakers.total_quotes} quotes")
        
        # Phase 4B: Extract entities and relationships
        logger.info(f"Phase 4B for {interview_id}: Extracting entities and relationships...")
        entities_prompt = self._build_entities_relationships_prompt(
            interview_text=interview_text,
            interview_id=interview_id,
            quotes=quotes_and_speakers.quotes
        )
        
        entities_and_relationships = await self.llm.extract_structured(
            prompt=entities_prompt,
            schema=EntitiesAndRelationships,
            max_tokens=None
        )
        
        logger.info(f"{interview_id}: Extracted {entities_and_relationships.total_entities} entities")
        
        # Combine results
        coded_interview = self._combine_extraction_results(
            interview_id=interview_id,
            interview_file=interview_file,
            quotes_and_speakers=quotes_and_speakers,
            entities_and_relationships=entities_and_relationships
        )
        
        # Save individual interview result
        await self._save_coded_interview(coded_interview)
        
        logger.info(f"Completed interview: {interview_id}")
        return coded_interview
        
    except Exception as e:
        logger.error(f"Error processing {interview_file}: {e}")
        raise

async def _run_phase_4_parallel(self, max_concurrent: int = 3):
    """Phase 4 with parallel processing"""
    logger.info(f"Phase 4: Applying schemas to {len(self.config.interview_files)} interviews in parallel")
    
    # Process all interviews in parallel with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(interview_file):
        async with semaphore:
            return await process_interview_parallel(self, interview_file)
    
    # Create tasks for all interviews
    tasks = [
        process_with_semaphore(interview_file) 
        for interview_file in self.config.interview_files
    ]
    
    # Wait for all to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Interview processing failed: {result}")
        else:
            self.coded_interviews.append(result)
            self.total_tokens_used += 5000  # Rough estimate
    
    logger.info(f"Phase 4 complete: {len(self.coded_interviews)} interviews processed")