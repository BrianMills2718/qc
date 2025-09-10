#!/usr/bin/env python3
"""
Test if removing the escape clauses forces deeper hierarchy
"""
import asyncio
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode
from pydantic import BaseModel, Field
from typing import List

async def test_forced_hierarchy():
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    # More forceful prompt without escape clauses
    prompt = '''
    You are conducting open coding analysis. 
    
    MANDATORY REQUIREMENT: You MUST create a hierarchy that is EXACTLY 3 levels deep.
    - Level 0: Exactly 3 top-level parent codes
    - Level 1: Exactly 3 child codes under EACH parent (9 total)
    - Level 2: Exactly 2 grandchild codes under EACH Level 1 code (18 total)
    
    DO NOT create fewer levels. This is required for the system to work properly.
    Every Level 0 code MUST have Level 1 children.
    Every Level 1 code MUST have Level 2 children.
    
    Interview Data:
    "We use AI for research in various ways. For qualitative analysis, we use it for coding and theme identification. 
    For quantitative work, we use it for data analysis and modeling. We also face challenges with AI adoption 
    including training needs, quality concerns, and ethical issues."
    
    Generate EXACTLY 30 codes (3 + 9 + 18) in a 3-level hierarchy.
    '''
    
    class OpenCodesResponse(BaseModel):
        codes: List[OpenCode] = Field(description="Exactly 30 codes in 3-level hierarchy")
    
    response = await llm.extract_structured(prompt=prompt, schema=OpenCodesResponse)
    
    # Check hierarchy
    levels = {}
    for code in response.codes:
        level = code.level
        levels[level] = levels.get(level, 0) + 1
    
    print(f"Level distribution: {levels}")
    print(f"Total codes: {len(response.codes)}")
    
    if levels.get(0, 0) == 3 and levels.get(1, 0) == 9 and levels.get(2, 0) == 18:
        print("\nSUCCESS: Forced hierarchy worked!")
    else:
        print("\nFAILED: LLM didn't follow strict requirements")
    
    return levels

if __name__ == "__main__":
    asyncio.run(test_forced_hierarchy())