#!/usr/bin/env python3
"""
Test what the LLM actually generates for hierarchical codes
"""
import asyncio
import json
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode
from typing import List

async def test_hierarchy_prompt():
    """Test LLM with explicit hierarchy instructions"""
    
    # Initialize LLM (no need for initialization)
    llm = LLMHandler(
        model_name="gemini/gemini-2.0-flash-exp",
        temperature=0.7,
        max_retries=3
    )
    
    # Create a prompt that explicitly asks for multi-level hierarchy
    prompt = '''
    You are analyzing interview data for qualitative research using Grounded Theory methodology.
    
    CRITICAL REQUIREMENT: Generate a MULTI-LEVEL hierarchical code structure with at least 3 levels:
    - Level 0: Top-level parent codes (3-5 codes)
    - Level 1: Child codes under each parent (2-4 per parent)
    - Level 2: Grandchild codes under some Level 1 codes (1-3 per child)
    
    For the field definitions:
    - parent_id: Use the parent's code_name with underscores (e.g., "Research_Methods")
    - level: 0 for top-level, 1 for children, 2 for grandchildren
    - child_codes: List of child code_names with underscores
    
    Example structure:
    - Research_Methods (level=0, parent_id=null, child_codes=["Qualitative", "Quantitative"])
      - Qualitative (level=1, parent_id="Research_Methods", child_codes=["Interviews", "Observations"])
        - Interviews (level=2, parent_id="Qualitative", child_codes=[])
        - Observations (level=2, parent_id="Qualitative", child_codes=[])
      - Quantitative (level=1, parent_id="Research_Methods", child_codes=["Statistics"])
        - Statistics (level=2, parent_id="Quantitative", child_codes=[])
    
    Interview excerpt to analyze:
    "We use many research methods at RAND. Qualitative methods include interviews, focus groups, and case studies. 
    For interviews, we do both structured and semi-structured formats. Quantitative methods include statistical 
    analysis, modeling, and simulations. Statistical analysis involves regression, time series, and causal inference."
    
    Generate the OpenCodesResponse with a multi-level hierarchy.
    '''
    
    # Get LLM response
    print("Sending prompt to LLM...")
    from pydantic import BaseModel, Field
    from typing import List
    
    class OpenCodesResponse(BaseModel):
        codes: List[OpenCode] = Field(description="List of open codes with hierarchy")
    
    response_obj = await llm.extract_structured(
        prompt=prompt,
        schema=OpenCodesResponse
    )
    response = response_obj.codes
    
    print(f"\nReceived {len(response)} codes from LLM")
    
    # Analyze the hierarchy
    levels = {}
    for code in response:
        level = code.level
        levels[level] = levels.get(level, 0) + 1
        
        if level == 0:
            print(f"\nLevel 0 (Parent): {code.code_name}")
            print(f"  Children: {code.child_codes}")
        elif level == 1:
            print(f"\nLevel 1 (Child): {code.code_name}")
            print(f"  Parent: {code.parent_id}")
            print(f"  Children: {code.child_codes}")
        elif level == 2:
            print(f"\nLevel 2 (Grandchild): {code.code_name}")
            print(f"  Parent: {code.parent_id}")
    
    print(f"\n=== HIERARCHY SUMMARY ===")
    print(f"Level distribution: {levels}")
    print(f"Maximum depth: {max(levels.keys()) if levels else 0}")
    
    # Save for inspection
    output = {
        'codes': [
            {
                'name': c.code_name,
                'level': c.level,
                'parent_id': c.parent_id,
                'child_codes': c.child_codes,
                'description': c.description
            }
            for c in response
        ],
        'level_distribution': levels
    }
    
    with open('test_hierarchy_output.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nOutput saved to test_hierarchy_output.json")
    
    return response

if __name__ == "__main__":
    asyncio.run(test_hierarchy_prompt())