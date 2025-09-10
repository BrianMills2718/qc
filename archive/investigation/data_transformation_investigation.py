#!/usr/bin/env python3
"""
DATA TRANSFORMATION INVESTIGATION: How do self-connections occur?
"""

import sys
import asyncio
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, QuotesAndSpeakers
import yaml

async def investigate_data_transformation():
    print("DATA TRANSFORMATION INVESTIGATION")
    print("=" * 60)
    
    # Setup
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    await extractor._auto_load_existing_taxonomy()
    
    # Create test with PROPER timestamp format to trigger focus group detection
    timestamp_focus_group = '''
Alice   01:00
I think AI has great potential for data analysis, but I'm concerned about accuracy.

Bob   01:30  
I agree with Alice about the accuracy concerns. I've seen AI make mistakes in my field.

Carol   02:00
Building on Alice's point about validation, I think human oversight is crucial.

Alice   02:30
Thanks Bob and Carol. But I wonder if proper validation could address those accuracy issues?
    '''
    
    print("STEP 1: Test focus group detection with timestamp format")
    print("-" * 50)
    
    # Test detection
    dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(timestamp_focus_group, "TIMESTAMP_TEST")
    interview_type = extractor.dialogue_detector.detect_interview_type(timestamp_focus_group)
    
    print(f"Detected type: {interview_type}")
    print(f"Dialogue turns: {len(dialogue_turns)}")
    
    speakers = set(turn.speaker_name for turn in dialogue_turns if turn.speaker_name)
    print(f"Unique speakers: {speakers}")
    
    if interview_type != "focus_group":
        print("WARNING: Still not detected as focus group!")
        return
    
    print("SUCCESS: Detected as focus group!")
    print()
    
    print("STEP 2: Generate LLM prompt and test extraction")
    print("-" * 50)
    
    try:
        # Generate prompt  
        prompt = extractor._build_quotes_speakers_prompt(
            interview_text=timestamp_focus_group,
            interview_id="TIMESTAMP_TEST",
            is_focus_group=True,
            dialogue_turns=dialogue_turns
        )
        
        # Save prompt to file to avoid encoding issues
        with open("debug_prompt.txt", "w", encoding="utf-8") as f:
            f.write(prompt)
        print("Saved actual prompt to debug_prompt.txt")
        
        # Check critical parts of prompt
        prompt_lower = prompt.lower()
        print("\nPROMPT ANALYSIS:")
        print(f"  Mentions 'none': {prompt_lower.count('none')} times")
        print(f"  Mentions self-connection warnings: {'self' in prompt_lower or 'same speaker' in prompt_lower}")
        print(f"  Encourages conservative detection: {'only identify clear' in prompt_lower}")
        
        print("\nSTEP 3: Call LLM and analyze raw response")
        print("-" * 50)
        
        # Call LLM
        raw_result = await extractor.llm.extract_structured(
            prompt=prompt,
            schema=QuotesAndSpeakers,
            max_tokens=None
        )
        
        if raw_result and raw_result.quotes:
            print(f"LLM returned {len(raw_result.quotes)} quotes")
            
            # Save raw LLM response to file
            raw_data = {
                "quotes": [],
                "speakers": []
            }
            
            for quote in raw_result.quotes:
                quote_dict = {
                    "text": quote.text,
                    "speaker_name": getattr(quote, 'speaker_name', 'NO_SPEAKER_NAME'),
                    "thematic_connection": getattr(quote, 'thematic_connection', 'NO_CONNECTION'),
                    "connection_target": getattr(quote, 'connection_target', 'NO_TARGET'),
                    "connection_confidence": getattr(quote, 'connection_confidence', 'NO_CONFIDENCE'),
                }
                raw_data["quotes"].append(quote_dict)
            
            with open("debug_raw_llm_response.json", "w") as f:
                json.dump(raw_data, f, indent=2)
            print("Saved raw LLM response to debug_raw_llm_response.json")
            
            # Analyze for self-connections in raw response
            print("\nRAW LLM RESPONSE ANALYSIS:")
            self_connections_in_raw = 0
            
            for quote in raw_result.quotes:
                speaker = getattr(quote, 'speaker_name', None)
                target = getattr(quote, 'connection_target', None)
                connection = getattr(quote, 'thematic_connection', None)
                
                print(f"Quote: \"{quote.text[:50]}...\"")
                print(f"  Speaker: {speaker}")
                print(f"  Connection: {connection} -> {target}")
                
                if speaker == target and connection and connection != "none":
                    print("  🚨 SELF-CONNECTION IN RAW LLM RESPONSE!")
                    self_connections_in_raw += 1
                elif connection == "none":
                    print("  ✓ Properly marked as 'none'")
                else:
                    print("  ✓ Valid connection to different speaker")
                print()
            
            print(f"SELF-CONNECTIONS IN RAW LLM RESPONSE: {self_connections_in_raw}")
            
            if self_connections_in_raw > 0:
                print("CONCLUSION: Self-connections originate from LLM, not data transformation")
            else:
                print("CONCLUSION: Self-connections occur during data transformation")
            
        else:
            print("ERROR: LLM returned no quotes")
            
    except Exception as e:
        print(f"ERROR in investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(investigate_data_transformation())