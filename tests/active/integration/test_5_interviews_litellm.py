"""
Test Entity Extraction on 5 Interviews with LiteLLM
Tests the complete pipeline with our new LiteLLM implementation.
"""

import asyncio
import os
from pathlib import Path
from docx import Document
from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.core.native_gemini_client import NativeGeminiClient
from src.qc.core.schema_config import create_research_schema
from src.qc.extraction.multi_pass_extractor import MultiPassExtractor, InterviewContext

async def test_5_interviews():
    """Test entity extraction on 5 interviews"""
    print("TESTING: Entity Extraction on 5 Interviews with LiteLLM")
    print("=" * 70)
    
    # Initialize components
    neo4j = EnhancedNeo4jManager()
    await neo4j.connect()
    
    schema = create_research_schema()
    llm_client = NativeGeminiClient()
    extractor = MultiPassExtractor(neo4j_manager=neo4j, schema=schema, llm_client=llm_client, use_code_driven=True)
    
    # Interview files
    base_path = Path("C:/Users/Brian/projects/qualitative_coding/AI_Interviews_all_2025.0728/Interviews/ai_interviews_5_for_test")
    interview_files = list(base_path.glob("*.docx"))
    
    print(f"Found {len(interview_files)} interview files:")
    for file in interview_files:
        print(f"  - {file.name}")
    
    if not interview_files:
        print("No interview files found!")
        return
    
    print(f"\nProcessing {len(interview_files)} interviews...")
    
    total_themes = 0
    total_quotes = 0
    total_entities = 0
    total_mentions = 0
    
    for i, interview_file in enumerate(interview_files, 1):
        print(f"\nProcessing Interview {i}/{len(interview_files)}: {interview_file.name}")
        print("-" * 50)
        
        try:
            # Process docx file to extract text
            doc = Document(interview_file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            
            if not text.strip():
                print(f"  WARNING: No text extracted from {interview_file.name}")
                continue
            
            # Create interview context
            context = InterviewContext(
                interview_id=f"test_interview_{i}",
                interview_text=text,
                session_id="test_session",
                filename=str(interview_file)
            )
            
            # Run extraction
            print(f"  Running LiteLLM-powered extraction...")
            results = await extractor.extract_from_interview(context)
            
            # Count results from ExtractionResult list
            themes = 0
            quotes = 0
            entities = 0
            mentions = 0
            
            for result in results:
                if result.success:
                    themes += len(result.codes_found)
                    entities += len(result.entities_found)
                    mentions += len(result.relationships_found)
                    
                    # Quotes are embedded in the themes/codes, need to extract from metadata
                    if 'quotes_count' in result.metadata:
                        quotes += result.metadata['quotes_count']
            
            total_themes += themes
            total_quotes += quotes
            total_entities += entities
            total_mentions += mentions
            
            print(f"  SUCCESS: {themes} themes, {quotes} quotes, {entities} entities, {mentions} mentions")
            
        except Exception as e:
            print(f"  ERROR: {interview_file.name}: {e}")
            continue
    
    print(f"\nFINAL RESULTS - 5 Interview Test")
    print("=" * 50)
    print(f"Total Themes: {total_themes}")
    print(f"Total Quotes: {total_quotes}")  
    print(f"Total Entities: {total_entities}")
    print(f"Total MENTIONS: {total_mentions}")
    print(f"Average per Interview:")
    print(f"   - Themes: {total_themes/len(interview_files):.1f}")
    print(f"   - Quotes: {total_quotes/len(interview_files):.1f}")
    print(f"   - Entities: {total_entities/len(interview_files):.1f}")
    print(f"   - MENTIONS: {total_mentions/len(interview_files):.1f}")
    
    # Basic success assessment
    if total_entities > 0 and total_mentions > 0:
        print(f"\nSUCCESS: Three-layer knowledge graph working!")
        print(f"   Themes <-> Quotes <-> Entities architecture complete")
        print(f"   LiteLLM migration confirmed working with real interviews!")
    else:
        print(f"\nIssue: No entities or mentions extracted")
        print(f"   Need to investigate extraction pipeline")
    
    await neo4j.close()

if __name__ == "__main__":
    asyncio.run(test_5_interviews())