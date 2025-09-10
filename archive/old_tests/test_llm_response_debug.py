#!/usr/bin/env python3
"""
Debug what LLM is actually returning for open codes
"""
import asyncio
import json
from pathlib import Path
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.prompt_templates import GroundedTheoryPromptGenerator

async def debug_llm_response():
    """See what LLM actually returns"""
    print("=" * 60)
    print("DEBUGGING LLM OPEN CODING RESPONSE")
    print("=" * 60)
    
    # Initialize
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(
        Path('config/methodology_configs/grounded_theory_reliable.yaml')
    )
    
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    
    # Load interviews
    interviews = operations.robust_load_interviews(
        Path('data/interviews/ai_interviews_3_for_test')
    )
    
    # Create prompt
    prompt_gen = GroundedTheoryPromptGenerator(
        theoretical_sensitivity=config.theoretical_sensitivity,
        coding_depth=config.coding_depth
    )
    
    prompt = prompt_gen.generate_open_coding_prompt(interviews)
    print("\n[PROMPT LENGTH]:", len(prompt))
    
    # Call LLM directly for raw response
    from src.qc.llm.llm_handler import LLMHandler
    llm = LLMHandler(
        model_name="gemini/gemini-2.5-flash",
        temperature=0.1,
        max_retries=1
    )
    
    print("\n[CALLING LLM]...")
    raw_response = await llm.complete_raw(prompt)
    
    print("\n[RAW RESPONSE]:")
    print(raw_response[:2000])  # First 2000 chars
    
    # Try to parse as JSON
    try:
        # Clean JSON
        if "```json" in raw_response:
            json_str = raw_response.split("```json")[1].split("```")[0]
        else:
            json_str = raw_response
            
        data = json.loads(json_str.strip())
        
        print("\n[PARSED JSON STRUCTURE]:")
        if 'open_codes' in data:
            print(f"Number of codes: {len(data['open_codes'])}")
            
            # Check first code
            if data['open_codes']:
                first_code = data['open_codes'][0]
                print("\n[FIRST CODE]:")
                print(json.dumps(first_code, indent=2))
                
                # Check child_codes type
                if 'child_codes' in first_code:
                    print(f"\nchild_codes type: {type(first_code['child_codes'])}")
                    print(f"child_codes value: {first_code['child_codes']}")
                    if first_code['child_codes']:
                        print(f"First child type: {type(first_code['child_codes'][0])}")
                        
    except Exception as e:
        print(f"\n[PARSE ERROR]: {e}")
    
    await operations.cleanup()

if __name__ == "__main__":
    asyncio.run(debug_llm_response())