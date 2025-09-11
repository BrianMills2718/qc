#!/usr/bin/env python3
"""
Test end-to-end functionality of Phase 2.2 system
"""

import asyncio
import logging
from pathlib import Path

# Import required modules
from src.qc.extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext
from src.qc.core.schema_config import create_research_schema
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_end_to_end():
    """Test the complete Phase 2.2 system end-to-end"""
    print("Testing Phase 2.2 End-to-End System")
    print("=" * 50)
    
    try:
        # Initialize components with no authentication
        neo4j_manager = EnhancedNeo4jManager(username=None, password=None)
        await neo4j_manager.connect()
        print("Neo4j connected")
        
        schema = create_research_schema()
        print("Schema loaded")
        
        extractor = MultiPassExtractor(
            neo4j_manager=neo4j_manager,
            schema=schema
        )
        print("Extractor initialized")
        
        # Test with sample interview text
        sample_interview = """
        Interviewer: Can you tell me about your role at the organization?
        
        Dr. Sarah Johnson: I'm a Senior Research Director at TechCorp, which is a large technology 
        company focused on AI innovation. I've been here for 8 years and lead a team of 12 researchers. 
        We collaborate closely with Stanford University on machine learning projects, and I also serve 
        on the board of the AI Ethics Institute.
        
        One of the biggest challenges we face is the time investment required for data collection. 
        When we need new primary data, it can take months to design studies, get approvals, and 
        collect meaningful samples. This creates significant delays in our research timelines.
        
        I'm very interested in how AI could help streamline our qualitative data analysis. Right now, 
        we spend weeks manually coding interview transcripts and identifying themes. If AI could help 
        automate some of this pattern recognition, it would free up our researchers to focus on 
        interpretation and strategic insights.
        
        However, there are trust issues we need to address. Some of our senior researchers are 
        skeptical about AI reliability, especially for nuanced qualitative work. They worry about 
        losing the human insight that comes from deep engagement with the data.
        """
        
        # Create context
        context = InterviewContext(
            interview_id="test_001",
            interview_text=sample_interview,
            session_id="test_session",
            filename="test_interview.txt"
        )
        
        print("\nStarting extraction...")
        
        # Run extraction
        results = await extractor.extract_from_interview(context)
        
        print(f"\nExtraction Results:")
        print(f"   Passes completed: {len(results)}")
        
        total_entities = 0
        total_relationships = 0  
        total_codes = 0
        
        for i, result in enumerate(results, 1):
            entities_count = len(result.entities_found) if isinstance(result.entities_found, dict) else len(result.entities_found) if isinstance(result.entities_found, list) else 0
            relationships_count = len(result.relationships_found)
            codes_count = len(result.codes_found) if isinstance(result.codes_found, dict) else len(result.codes_found) if isinstance(result.codes_found, list) else 0
            
            print(f"   Pass {i}: {entities_count} entities, {relationships_count} relationships, {codes_count} codes")
            
            total_entities += entities_count
            total_relationships += relationships_count
            total_codes += codes_count
        
        print(f"\nTotal extracted: {total_entities} entities, {total_relationships} relationships, {total_codes} codes")
        
        # Test database query
        print("\nTesting database query...")
        query_result = await neo4j_manager.find_entities_by_type("Person")
        print(f"   Found {len(query_result)} Person entities in database")
        
        # Clean up
        await neo4j_manager.close()
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        logger.exception("End-to-end test failed")
        raise

if __name__ == "__main__":
    asyncio.run(test_end_to_end())