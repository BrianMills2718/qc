#!/usr/bin/env python3
"""
ROOT CAUSE INVESTIGATION: Examine the actual prompts being sent to LLM
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig
import yaml

async def investigate_prompts():
    print("PROMPT INVESTIGATION - ROOT CAUSE ANALYSIS")
    print("=" * 60)
    
    # Setup
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    # Auto-load taxonomy
    await extractor._auto_load_existing_taxonomy()
    
    # Create test conversation with clear speaker identities
    test_text = '''
    Moderator: What are your thoughts on AI in research?
    
    Alice: I think AI has great potential for data analysis, but I'm concerned about accuracy.
    
    Bob: I agree with Alice about the accuracy concerns. I've seen AI make mistakes.
    
    Alice: Thanks Bob. But I wonder if proper validation could address those issues?
    
    Carol: Building on Alice's point about validation, I think human oversight is crucial.
    '''
    
    interview_id = "PROMPT_TEST"
    
    # Get dialogue structure
    dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(test_text, interview_id)
    
    print(f"Test conversation: {len(dialogue_turns)} dialogue turns")
    for i, turn in enumerate(dialogue_turns):
        print(f"  {i+1}. {turn.speaker_name}: {turn.text[:50]}...")
    print()
    
    # Generate the actual prompt that would be sent to LLM
    print("GENERATING ACTUAL PROMPT FOR DIALOGUE-AWARE TEMPLATE:")
    print("-" * 60)
    
    try:
        actual_prompt = extractor._build_quotes_speakers_prompt(
            interview_text=test_text,
            interview_id=interview_id,
            is_focus_group=True,  # Use dialogue-aware template
            dialogue_turns=dialogue_turns
        )
        
        print("FULL PROMPT BEING SENT TO LLM:")
        print("=" * 80)
        print(actual_prompt)
        print("=" * 80)
        print()
        
        # Analyze the prompt for potential issues
        print("PROMPT ANALYSIS:")
        print("-" * 30)
        
        # Check if prompt mentions avoiding self-connections
        if "same speaker" in actual_prompt.lower() or "self" in actual_prompt.lower():
            print("✓ Prompt mentions avoiding self-connections")
        else:
            print("✗ Prompt does NOT mention avoiding self-connections")
        
        # Check if prompt emphasizes using "none"
        none_mentions = actual_prompt.lower().count('"none"') + actual_prompt.lower().count("'none'")
        print(f"✓ Prompt mentions 'none' {none_mentions} times")
        
        # Check connection instructions
        if "only identify clear" in actual_prompt.lower() or "use none when" in actual_prompt.lower():
            print("✓ Prompt encourages conservative connection detection")
        else:
            print("✗ Prompt may be encouraging over-connection")
        
        return actual_prompt
        
    except Exception as e:
        print(f"ERROR generating prompt: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_llm_with_controlled_input():
    print("\nTESTING LLM WITH CONTROLLED INPUT:")
    print("-" * 50)
    
    # Setup
    with open('extraction_config.yaml') as f:
        config_data = yaml.safe_load(f)
    config = ExtractionConfig(**config_data)
    extractor = CodeFirstExtractor(config)
    
    await extractor._auto_load_existing_taxonomy()
    
    # Simple test case where self-connections should be impossible
    simple_test = '''
    Moderator: Alice, what do you think about AI?
    
    Alice: I think AI is useful for research.
    
    Moderator: Bob, what's your view?
    
    Bob: I disagree with Alice. I think AI has too many risks.
    '''
    
    try:
        dialogue_turns = extractor.dialogue_detector.extract_dialogue_turns(simple_test, "SIMPLE_TEST")
        
        prompt = extractor._build_quotes_speakers_prompt(
            interview_text=simple_test,
            interview_id="SIMPLE_TEST",
            is_focus_group=True,
            dialogue_turns=dialogue_turns
        )
        
        print("Testing with simple conversation...")
        print("Expected: Alice and Bob should NOT connect to themselves")
        print()
        
        # Call LLM
        from qc.extraction.code_first_schemas import QuotesAndSpeakers
        result = await asyncio.wait_for(
            extractor.llm.extract_structured(
                prompt=prompt,
                schema=QuotesAndSpeakers,
                max_tokens=None
            ),
            timeout=60
        )
        
        if result and result.quotes:
            print("LLM RESPONSE ANALYSIS:")
            print("-" * 30)
            
            for quote in result.quotes:
                speaker = quote.speaker.name if quote.speaker else "Unknown"
                target = quote.connection_target
                connection = quote.thematic_connection
                
                print(f"Quote: \"{quote.text[:50]}...\"")
                print(f"Speaker: {speaker}")
                print(f"Connection: {connection} -> {target}")
                
                if speaker == target and connection != "none":
                    print("🚨 PROBLEM: Self-connection detected!")
                elif connection == "none":
                    print("✓ Good: Connection properly marked as 'none'")
                else:
                    print("✓ Good: Different speaker connection")
                print()
        
        return result
        
    except Exception as e:
        print(f"ERROR in controlled test: {e}")
        return None

if __name__ == "__main__":
    async def run_investigation():
        prompt = await investigate_prompts()
        result = await test_llm_with_controlled_input()
        
        print("\nROOT CAUSE INVESTIGATION SUMMARY:")
        print("=" * 60)
        print("1. Examined actual prompts being sent to LLM")
        print("2. Tested LLM behavior with controlled input")
        print("3. Check results above for self-connection patterns")
        
    asyncio.run(run_investigation())