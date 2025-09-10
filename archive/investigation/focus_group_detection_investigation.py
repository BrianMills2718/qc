#!/usr/bin/env python3
"""
CRITICAL INVESTIGATION: Why aren't focus groups being detected properly?
This could be the root cause of self-connections
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig
import yaml

async def investigate_focus_group_detection():
    print("FOCUS GROUP DETECTION INVESTIGATION")
    print("=" * 60)
    
    # Setup
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    await extractor._auto_load_existing_taxonomy()
    
    # Test cases
    test_cases = [
        {
            'name': 'Obvious Focus Group',
            'text': '''
            Moderator: Welcome everyone to our focus group on AI research.
            
            Alice: I think AI has great potential.
            
            Bob: I agree with Alice, but I have some concerns.
            
            Carol: Building on what Bob said, I think validation is key.
            
            David: I disagree with Carol's approach.
            '''
        },
        {
            'name': 'Individual Interview',
            'text': '''
            Interviewer: Thank you for joining me today.
            
            Participant: Happy to be here.
            
            Interviewer: Tell me about your experience with AI.
            
            Participant: Well, I've been using it for research...
            '''
        },
        {
            'name': 'Real Focus Group File',
            'file': 'tests/fixtures/Focus Group on AI and Methods 7_7.docx'
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTEST CASE: {test_case['name']}")
        print("-" * 40)
        
        try:
            if 'file' in test_case:
                # Test with real file
                interview_text = extractor._read_interview_file(test_case['file'])
                print(f"File content length: {len(interview_text)} characters")
            else:
                interview_text = test_case['text']
                print(f"Test text length: {len(interview_text)} characters")
            
            # Test detection
            dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(interview_text, test_case['name'])
            interview_type = extractor.dialogue_detector.detect_interview_type(interview_text)
            
            print(f"Detected type: {interview_type}")
            print(f"Dialogue turns: {len(dialogue_turns)}")
            
            # Show speakers detected
            speakers = set(turn.speaker_name for turn in dialogue_turns if turn.speaker_name)
            print(f"Unique speakers: {len(speakers)}")
            print(f"Speaker list: {list(speakers)}")
            
            # Check focus group criteria
            print(f"\nFOCUS GROUP CRITERIA CHECK:")
            print(f"  Multiple speakers (>2): {'✓' if len(speakers) > 2 else '✗'} ({len(speakers)} speakers)")
            print(f"  Sufficient dialogue turns (>3): {'✓' if len(dialogue_turns) > 3 else '✗'} ({len(dialogue_turns)} turns)")
            print(f"  Contains 'focus group' in text: {'✓' if 'focus group' in interview_text.lower() else '✗'}")
            print(f"  Contains 'moderator': {'✓' if 'moderator' in interview_text.lower() else '✗'}")
            
            # What template would be used?
            if interview_type == "focus_group" and len(dialogue_turns) > 3:
                template_used = "dialogue_aware_quotes"
            else:
                template_used = "quotes_speakers"
            
            print(f"  Template that would be used: {template_used}")
            
            # Show sample dialogue turns
            print(f"\nSAMPLE DIALOGUE TURNS (first 5):")
            for i, turn in enumerate(dialogue_turns[:5]):
                speaker = turn.speaker_name[:15] if turn.speaker_name else "Unknown"
                text_preview = turn.text[:60].replace('\n', ' ') if turn.text else ""
                print(f"  {i+1}. {speaker:<15}: {text_preview}...")
        
        except Exception as e:
            print(f"ERROR processing {test_case['name']}: {e}")
    
    print(f"\n" + "=" * 60)
    print("FOCUS GROUP DETECTION ANALYSIS COMPLETE")

async def investigate_detection_logic():
    print(f"\nINVESTIGATING DETECTION LOGIC SOURCE CODE:")
    print("-" * 50)
    
    # Let's look at the actual detection method
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    # Create a simple test
    test_text = '''
    Moderator: Welcome to our focus group.
    Alice: Thank you.
    Bob: Happy to be here.
    Carol: Looking forward to the discussion.
    '''
    
    # Test the detection step by step
    dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(test_text, "DEBUG_TEST")
    
    print(f"Dialogue turns extracted: {len(dialogue_turns)}")
    for turn in dialogue_turns:
        print(f"  Speaker: '{turn.speaker_name}' | Text: '{turn.text[:30]}...'")
    
    # Now test the type detection
    detected_type = extractor.dialogue_detector.detect_interview_type(test_text)
    print(f"\nDetected interview type: {detected_type}")
    
    # Let's see what the detection logic actually checks
    print(f"\nDETECTION CRITERIA ANALYSIS:")
    print(f"Text contains 'focus group': {'focus group' in test_text.lower()}")
    print(f"Text contains 'moderator': {'moderator' in test_text.lower()}")
    print(f"Number of speakers: {len(set(turn.speaker_name for turn in dialogue_turns))}")

if __name__ == "__main__":
    async def run_investigation():
        await investigate_focus_group_detection()
        await investigate_detection_logic()
    
    asyncio.run(run_investigation())