#!/usr/bin/env python3
"""
TRANSCRIPT ANALYSIS - Extract original transcript and compare to thematic connections
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig
import yaml

async def analyze_transcript_intelligence():
    print("TRANSCRIPT INTELLIGENCE ANALYSIS")
    print("=" * 60)
    
    # Load the JSON output to see what connections were made
    with open('output_production/interviews/Focus Group on AI and Methods 7_7.json') as f:
        output_data = json.load(f)
    
    quotes = output_data['quotes']
    print(f"Analyzing {len(quotes)} quotes with thematic connections...")
    print()
    
    # Setup extractor to read original transcript
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    # Read original transcript
    transcript_file = "tests/fixtures/Focus Group on AI and Methods 7_7.docx"
    try:
        original_text = extractor._read_interview_file(transcript_file)
        print("Original transcript extracted successfully")
        print(f"Transcript length: {len(original_text)} characters")
        print()
        
        # Get dialogue structure from original
        dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(original_text, "ANALYSIS")
        print(f"Dialogue structure: {len(dialogue_turns)} turns detected")
        print()
        
        # Show sample of original conversation flow
        print("ORIGINAL CONVERSATION FLOW (first 10 turns):")
        print("-" * 50)
        for i, turn in enumerate(dialogue_turns[:10]):
            speaker = turn.speaker_name[:15] if turn.speaker_name else "Unknown"
            text_preview = turn.text[:80].replace('\n', ' ') if turn.text else ""
            print(f"{i+1:2d}. {speaker:<15}: {text_preview}...")
        print()
        
        # Analyze thematic connections in context
        print("THEMATIC CONNECTION ANALYSIS:")
        print("-" * 50)
        
        # Group quotes by connection type for analysis
        connection_groups = {}
        for quote in quotes:
            conn_type = quote.get('thematic_connection', 'none')
            if conn_type not in connection_groups:
                connection_groups[conn_type] = []
            connection_groups[conn_type].append(quote)
        
        # Analyze each connection type
        for conn_type, conn_quotes in connection_groups.items():
            print(f"{conn_type.upper()} connections ({len(conn_quotes)} quotes):")
            
            for i, quote in enumerate(conn_quotes[:3]):  # Show first 3 of each type
                quote_text = quote['text'][:100].replace('\n', ' ')
                target = quote.get('connection_target', 'N/A')
                confidence = quote.get('connection_confidence', 'N/A')
                speaker = quote.get('speaker', {}).get('name', 'Unknown') if quote.get('speaker') else 'Unknown'
                
                print(f"  {i+1}. {speaker} -> {target} (conf: {confidence})")
                print(f"     Text: \"{quote_text}...\"")
                
                # Try to find context in original dialogue
                matching_turns = [t for t in dialogue_turns if quote_text[:50] in t.text]
                if matching_turns:
                    turn = matching_turns[0]
                    turn_index = dialogue_turns.index(turn)
                    print(f"     Context: Turn {turn_index + 1} of {len(dialogue_turns)}")
                    
                    # Show preceding context
                    if turn_index > 0:
                        prev_turn = dialogue_turns[turn_index - 1]
                        prev_text = prev_turn.text[:60].replace('\n', ' ') if prev_turn.text else ""
                        print(f"     Previous: {prev_turn.speaker_name}: \"{prev_text}...\"")
                else:
                    print(f"     Context: Could not locate in original transcript")
                print()
            
            if len(conn_quotes) > 3:
                print(f"  ... and {len(conn_quotes) - 3} more {conn_type} connections")
            print()
        
        # Intelligence assessment
        print("INTELLIGENCE ASSESSMENT:")
        print("-" * 50)
        
        # Check if connections make sense
        responds_to_quotes = connection_groups.get('responds_to', [])
        clarifies_quotes = connection_groups.get('clarifies', [])
        supports_quotes = connection_groups.get('supports', [])
        
        print(f"Assessment criteria:")
        print(f"1. Do 'responds_to' connections show actual responses? ({len(responds_to_quotes)} cases)")
        print(f"2. Do 'clarifies' connections show clarification attempts? ({len(clarifies_quotes)} cases)")
        print(f"3. Do 'supports' connections show agreement/support? ({len(supports_quotes)} cases)")
        print(f"4. Are connection targets appropriate speakers?")
        print(f"5. Do confidence scores reflect connection strength?")
        
        return True
        
    except Exception as e:
        print(f"Error reading transcript: {e}")
        return False

def run_sync_analysis():
    """Run the analysis synchronously since we don't need LLM calls"""
    import asyncio
    try:
        return asyncio.run(analyze_transcript_intelligence())
    except Exception as e:
        print(f"Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = run_sync_analysis()
    if success:
        print("Analysis complete - review the connections above for intelligence assessment")
    else:
        print("Analysis failed")