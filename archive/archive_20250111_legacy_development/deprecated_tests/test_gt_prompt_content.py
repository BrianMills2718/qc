#!/usr/bin/env python3
"""
GT Prompt Content Analysis
Test the exact GT workflow prompt content to isolate the failure cause
"""

import asyncio
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from pathlib import Path

async def test_exact_gt_prompt():
    """Test the exact prompt that's failing in the GT workflow"""
    
    print("=== Exact GT Prompt Content Testing ===")
    
    # Load realistic configuration
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_realistic.yaml"))
    
    # Initialize system like GT workflow does
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
    
    # Create workflow and get the exact same prompt
    workflow = GroundedTheoryWorkflow(operations, config=config)
    interview_text = workflow._prepare_interview_text(interviews)
    
    print(f"Prepared interview text length: {len(interview_text)} characters")
    print(f"First 200 chars: {interview_text[:200]}...")
    print(f"Last 200 chars: ...{interview_text[-200:]}")
    
    # Generate the exact prompt that's failing
    if workflow.prompt_generator:
        exact_prompt = workflow.prompt_generator.generate_open_coding_prompt(interview_text)
        print(f"\nUsing ConfigurablePromptGenerator")
    else:
        # Fallback - should not happen but let's be safe
        exact_prompt = "FALLBACK PROMPT"
        print(f"\nUsing fallback prompt")
    
    print(f"Generated prompt length: {len(exact_prompt)} characters")
    print(f"Prompt starts with: {exact_prompt[:300]}...")
    
    # Test this exact prompt step by step
    
    # Step 1: Raw completion test
    print(f"\n--- Step 1: Raw Completion Test ---")
    try:
        raw_response = await operations._llm_handler.complete_raw(
            prompt=exact_prompt,
            max_tokens=8000,  # Use the realistic config max_tokens
            temperature=0.1
        )
        
        if raw_response:
            print(f"SUCCESS: Raw response generated ({len(raw_response)} chars)")
            print(f"Raw response preview: {raw_response[:300]}...")
            print(f"Contains JSON brackets: {'{' in raw_response and '}' in raw_response}")
        else:
            print(f"FAILED: Raw response is None - this is the root problem!")
            return False
    except Exception as e:
        print(f"FAILED: Raw completion error: {e}")
        return False
    
    # Step 2: JSON extraction test (if raw worked)
    print(f"\n--- Step 2: JSON Extraction Test ---")
    try:
        import json
        import re
        
        # Try the same JSON extraction the LLM handler uses
        json_pattern = r'(\{.*\}|\[.*\])'
        matches = re.findall(json_pattern, raw_response, re.DOTALL)
        print(f"Found {len(matches)} potential JSON matches")
        
        for i, match in enumerate(matches[:3]):  # Test first 3 matches
            try:
                parsed = json.loads(match)
                print(f"  Match {i+1}: Successfully parsed JSON")
                if isinstance(parsed, dict) and 'open_codes' in parsed:
                    codes = parsed.get('open_codes', [])
                    print(f"    Found open_codes array with {len(codes)} items")
                    if codes and len(codes) > 0:
                        first_code = codes[0]
                        print(f"    First code keys: {list(first_code.keys()) if isinstance(first_code, dict) else 'Not a dict'}")
                        
            except json.JSONDecodeError as e:
                print(f"  Match {i+1}: JSON parsing failed: {e}")
    
    except Exception as e:
        print(f"JSON extraction test failed: {e}")
    
    # Step 3: Structured extraction test
    print(f"\n--- Step 3: Structured Extraction Test ---")
    try:
        schema = workflow._create_open_codes_schema()
        structured_result = await operations._llm_handler.extract_structured(
            prompt=exact_prompt,
            schema=schema,
            max_tokens=8000
        )
        
        print(f"SUCCESS: Structured extraction worked!")
        print(f"Generated {len(structured_result.open_codes)} codes")
        
        for i, code in enumerate(structured_result.open_codes[:3]):
            print(f"  Code {i+1}: {code.code_name} (freq={code.frequency}, conf={code.confidence:.2f})")
        
        return True
        
    except Exception as e:
        print(f"FAILED: Structured extraction failed: {e}")
        return False

async def test_prompt_variations():
    """Test variations of the GT prompt to isolate the issue"""
    
    print(f"\n=== GT Prompt Variations Testing ===")
    
    # Load configuration and data
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_realistic.yaml"))
    
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
    
    workflow = GroundedTheoryWorkflow(operations, config=config)
    interview_text = workflow._prepare_interview_text(interviews)
    
    # Test different variations of the prompt
    variations = [
        ("Short Sample Data", "Sample interview data: 'I think AI is helpful but concerning.'"),
        ("Medium Sample Data", "Interview 1: " + "AI technology is changing rapidly. " * 50),  # ~1500 chars
        ("Actual Data Truncated", interview_text[:5000]),  # First 5K chars
        ("Actual Data Full", interview_text)  # Full data
    ]
    
    for var_name, var_data in variations:
        print(f"\n--- Testing: {var_name} ({len(var_data)} chars) ---")
        
        try:
            # Generate prompt with this variation
            test_prompt = workflow.prompt_generator.generate_open_coding_prompt(var_data)
            
            # Test raw completion
            raw_response = await operations._llm_handler.complete_raw(
                test_prompt, 
                max_tokens=4000,
                temperature=0.1
            )
            
            if raw_response:
                print(f"  Raw response: OK ({len(raw_response)} chars)")
                
                # Test structured extraction  
                schema = workflow._create_open_codes_schema()
                try:
                    structured_result = await operations._llm_handler.extract_structured(
                        prompt=test_prompt,
                        schema=schema,
                        max_tokens=4000
                    )
                    
                    print(f"  Structured: SUCCESS ({len(structured_result.open_codes)} codes)")
                    
                except Exception as struct_e:
                    print(f"  Structured: FAILED ({struct_e})")
            else:
                print(f"  Raw response: FAILED (None response)")
                print(f"  --> BREAKING POINT IDENTIFIED: {var_name}")
                break
                
        except Exception as e:
            print(f"  Error: {e}")

async def run_tests():
    """Run all GT prompt content tests"""
    
    success = await test_exact_gt_prompt()
    await test_prompt_variations()
    
    return success

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    print(f"\nGT Prompt Content Test Result: {'SUCCESS' if success else 'FAILED'}")
    exit(0 if success else 1)