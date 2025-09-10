#!/usr/bin/env python3
"""
Quick test to verify hierarchy generation with the improved prompt
"""
import asyncio
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode
from pydantic import BaseModel, Field
from typing import List

async def test_improved_prompt():
    llm = LLMHandler(model_name="gemini/gemini-2.5-flash")
    
    # Use the EXACT prompt from the workflow
    prompt = '''
    For each concept you identify:
    1. Name the concept clearly and concisely
    2. Describe what this concept represents in the data
    3. Identify properties (characteristics) of this concept
    4. Note dimensional variations (different ways this concept appears)
    5. Provide supporting quotes that demonstrate this concept
    6. Assess frequency and confidence
    7. ORGANIZE HIERARCHICALLY with MULTIPLE LEVELS:
       - Create a MULTI-LEVEL hierarchy (at least 3 levels deep where appropriate)
       - Level 0: Top-level parent codes (3-5 major themes)
       - Level 1: Child codes under each parent (2-4 per parent)
       - Level 2: Grandchild codes under Level 1 codes (1-3 per child where relevant)
       - Level 3+: Further sub-codes if the data supports it
       - Use parent_id to link each code to its parent (use parent's code_name with underscores)
       - List child_codes for any code that has children
    
    Follow open coding principles:
    - Stay close to the data
    - Use participants' language when possible
    - Look for actions, interactions, and meanings
    - Ask: What is happening here? What are people doing?
    - Organize related concepts into MULTI-LEVEL hierarchical groups
    - Build deep hierarchies: parent → child → grandchild → great-grandchild where the data supports it
    
    Interview Data:
    "We use various research methods at RAND. For qualitative research, we do interviews which can be structured or semi-structured. We also do focus groups and case studies. For quantitative work, we use statistical analysis including regression, time series, and causal inference methods. We also do modeling and simulations."
    
    Generate comprehensive open codes that capture the key concepts in this data, organizing them into a MULTI-LEVEL hierarchical structure (at least 3 levels deep) where natural groupings emerge.
    '''
    
    class OpenCodesResponse(BaseModel):
        codes: List[OpenCode] = Field(description="List of open codes")
    
    response = await llm.extract_structured(prompt=prompt, schema=OpenCodesResponse)
    
    # Check hierarchy
    levels = {}
    for code in response.codes:
        level = code.level
        levels[level] = levels.get(level, 0) + 1
        if level <= 1:
            print(f"L{level}: {code.code_name} (children: {len(code.child_codes)})")
    
    print(f"\nLevel distribution: {levels}")
    print(f"Max depth: {max(levels.keys()) if levels else 0}")
    
    return levels

if __name__ == "__main__":
    levels = asyncio.run(test_improved_prompt())
    if max(levels.keys()) >= 2:
        print("\n✓ SUCCESS: Multi-level hierarchy generated!")
    else:
        print("\n✗ FAILED: Only single-level hierarchy")