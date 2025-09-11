"""Test Phase 4 split approach with a small interview chunk"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.llm.llm_handler import LLMHandler
from src.qc.extraction.code_first_schemas import (
    SimpleQuote, QuotesAndSpeakers, SpeakerInfo,
    ExtractedEntity, ExtractedRelationship, EntitiesAndRelationships
)

async def test_small_split():
    """Test split extraction on small interview chunk"""
    
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    # Small interview chunk
    interview_text = """
    1: Todd Helmus: Welcome everyone. Today we're discussing AI in qualitative research. 
    2: Can you share your experiences using AI tools for research?
    
    3: Joie Acosta: I've been using ChatGPT for transcription and initial coding. 
    4: It saves tremendous time, but I worry about accuracy with technical terms. 
    5: The AI doesn't always understand context the way a human researcher does.
    
    6: Laura Elan: I agree about the context issue. I use Claude for literature reviews.
    7: It's excellent at finding connections between papers I might have missed.
    8: But you definitely need human oversight - it can hallucinate citations.
    
    9: Todd Helmus: What about ethical concerns with using AI?
    
    10: Joie Acosta: That's a big issue. Data privacy is my main concern.
    11: We can't just upload interview transcripts to ChatGPT without considering participant privacy.
    12: I think we need clear guidelines from IRBs about AI use.
    
    13: Laura Elan: Absolutely. And there's the question of attribution.
    14: If AI helps with analysis, how do we acknowledge that contribution?
    15: It's changing the nature of qualitative research itself.
    """
    
    codes = ["AI Benefits", "AI Challenges", "Ethical Concerns", "Human Oversight", "Research Methods"]
    
    # Phase 4A: Quotes and Speakers
    quotes_prompt = f"""
    Extract quotes and speakers from this interview about AI in research.
    
    Available codes: {', '.join(codes)}
    
    CRITICAL: 
    - Extract EVERY substantive statement as a quote
    - Apply MULTIPLE codes to each quote when relevant
    - Identify speakers from the text
    
    Interview:
    {interview_text}
    """
    
    print("Phase 4A: Extracting quotes and speakers...")
    quotes_result = await llm.extract_structured(
        prompt=quotes_prompt,
        schema=QuotesAndSpeakers,
        max_tokens=None
    )
    
    print(f"  Extracted {quotes_result.total_quotes} quotes")
    print(f"  Found {len(quotes_result.speakers)} speakers")
    print(f"  Total code applications: {quotes_result.total_codes_applied}")
    
    # Check many-to-many
    multi_coded = sum(1 for q in quotes_result.quotes if len(q.code_names) > 1)
    print(f"  Quotes with multiple codes: {multi_coded}/{len(quotes_result.quotes)}")
    
    # Show first few quotes
    print("\n  Sample quotes:")
    for i, quote in enumerate(quotes_result.quotes[:3], 1):
        print(f"    {i}. '{quote.text[:60]}...'")
        print(f"       Speaker: {quote.speaker_name}")
        print(f"       Codes: {', '.join(quote.code_names)}")
    
    # Phase 4B: Entities and Relationships
    entities_prompt = f"""
    Extract entities and relationships from this interview.
    
    Entity types to look for:
    - AI_Tool (ChatGPT, Claude, etc.)
    - Research_Method (transcription, coding, literature review)
    - Person (researchers mentioned)
    - Concept (privacy, ethics, attribution)
    - Organization (IRB)
    
    Relationship types:
    - USES (person uses tool/method)
    - CONCERNS (person has concern about something)
    - REQUIRES (something requires something else)
    
    Interview:
    {interview_text}
    """
    
    print("\n\nPhase 4B: Extracting entities and relationships...")
    entities_result = await llm.extract_structured(
        prompt=entities_prompt,
        schema=EntitiesAndRelationships,
        max_tokens=None
    )
    
    print(f"  Extracted {entities_result.total_entities} entities")
    print(f"  Extracted {entities_result.total_relationships} relationships")
    
    # Show some entities
    if entities_result.entities:
        print("\n  Sample entities:")
        for entity in entities_result.entities[:5]:
            print(f"    - {entity.name} (type: {entity.type})")
    
    # Show some relationships
    if entities_result.relationships:
        print("\n  Sample relationships:")
        for rel in entities_result.relationships[:3]:
            print(f"    - {rel.source_entity} --[{rel.relationship_type}]--> {rel.target_entity}")
    
    return quotes_result, entities_result

if __name__ == "__main__":
    quotes, entities = asyncio.run(test_small_split())
    
    if quotes.total_quotes >= 5:
        print(f"\n[SUCCESS] Split extraction working! Got {quotes.total_quotes} quotes")
    else:
        print(f"\n[WARNING] Only got {quotes.total_quotes} quotes")