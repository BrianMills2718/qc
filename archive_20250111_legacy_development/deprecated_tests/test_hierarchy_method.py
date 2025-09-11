#!/usr/bin/env python3
"""
Test to understand how hierarchy is built - are codes reused or new ones created?
"""
import asyncio
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode
from pydantic import BaseModel, Field
from typing import List

async def test_hierarchy_method():
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    # Clear prompt about hierarchy building
    prompt = '''
    Analyze this interview excerpt and create hierarchical codes.
    
    Interview: "We use AI for qualitative analysis like coding interviews and identifying themes. 
    We also use AI for quantitative analysis like statistical modeling and data visualization.
    Within qualitative analysis, we specifically use AI for automated coding and for theme extraction."
    
    Create a 3-level hierarchy:
    - Level 0: High-level categories
    - Level 1: Sub-categories 
    - Level 2: Specific techniques
    
    IMPORTANT: Show me ALL codes you create, including the parent category codes.
    '''
    
    class OpenCodesResponse(BaseModel):
        open_codes: List[OpenCode] = Field(description="All codes including parents and children")
    
    response = await llm.extract_structured(prompt=prompt, schema=OpenCodesResponse)
    
    print("=== ALL CODES GENERATED ===\n")
    
    # Group by level
    codes_by_level = {}
    for code in response.open_codes:
        level = code.level
        if level not in codes_by_level:
            codes_by_level[level] = []
        codes_by_level[level].append(code)
    
    # Display hierarchy
    for level in sorted(codes_by_level.keys()):
        print(f"\nLEVEL {level} CODES ({len(codes_by_level[level])} codes):")
        print("-" * 40)
        for code in codes_by_level[level]:
            print(f"  {code.code_name}")
            if code.parent_id:
                print(f"    Parent: {code.parent_id}")
            if code.child_codes:
                print(f"    Children: {code.child_codes}")
    
    print("\n=== ANALYSIS ===")
    print(f"Total codes created: {len(response.open_codes)}")
    
    # Check if parent codes exist as separate entities
    all_code_names = {code.code_name for code in response.open_codes}
    
    for code in response.open_codes:
        if code.parent_id:
            if code.parent_id in all_code_names:
                print(f"✓ Parent '{code.parent_id}' exists as a separate code")
            else:
                print(f"✗ Parent '{code.parent_id}' referenced but not created")
    
    return response.open_codes

if __name__ == "__main__":
    asyncio.run(test_hierarchy_method())