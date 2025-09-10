#!/usr/bin/env python3
"""
Direct test to see if LLM generates hierarchical codes with updated prompts
"""
import asyncio
import json
from src.qc.llm.llm_handler import LLMHandler
from src.qc.workflows.grounded_theory import OpenCode

async def test_direct_llm_hierarchy():
    """Test LLM directly with hierarchy-aware prompt"""
    print("=" * 60)
    print("DIRECT LLM HIERARCHY TEST")
    print("=" * 60)
    
    # 1. Initialize LLM
    print("\n1. INITIALIZING LLM...")
    llm = LLMHandler(
        model_name="gemini/gemini-2.5-flash",
        temperature=0.1,
        max_retries=3
    )
    print("   [OK] LLM initialized")
    
    # 2. Create test prompt with hierarchy instructions
    print("\n2. CREATING HIERARCHY-AWARE PROMPT...")
    prompt = """
    Analyze this interview data and generate open codes using Grounded Theory methodology.
    
    IMPORTANT: Organize codes hierarchically when appropriate:
    - Create parent codes for broad themes
    - Create child codes for specific instances
    - Use parent_id to link child codes to parents
    - Set level=0 for top-level codes, level=1 for children
    
    Interview Data:
    "I use ChatGPT for summarizing research papers. It saves me hours. But I worry about accuracy sometimes."
    "We're exploring Claude for coding assistance. The team finds it helpful for debugging."
    "AI tools are changing how we work, but there are concerns about data privacy."
    
    Return a JSON with this structure:
    {
        "codes": [
            {
                "code_name": "string",
                "description": "string",
                "properties": ["string"],
                "dimensions": ["string"],
                "supporting_quotes": ["string"],
                "frequency": integer,
                "confidence": float,
                "parent_id": "string or null",
                "level": integer,
                "child_codes": ["string"]
            }
        ]
    }
    
    Create at least one parent-child hierarchy in your response.
    """
    
    # 3. Call LLM
    print("\n3. CALLING LLM...")
    try:
        response = await llm.complete_raw(prompt)
        print("   [OK] LLM responded")
        
        # 4. Parse response
        print("\n4. PARSING RESPONSE...")
        response_text = response
        
        # Clean JSON if needed
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        
        data = json.loads(response_text.strip())
        print(f"   [OK] Parsed {len(data['codes'])} codes")
        
        # 5. Check for hierarchy
        print("\n5. CHECKING FOR HIERARCHY...")
        hierarchical_codes = []
        flat_codes = []
        
        for code_data in data['codes']:
            has_hierarchy = (
                code_data.get('parent_id') is not None or 
                len(code_data.get('child_codes', [])) > 0 or 
                code_data.get('level', 0) > 0
            )
            
            if has_hierarchy:
                hierarchical_codes.append(code_data)
            else:
                flat_codes.append(code_data)
        
        print(f"   Hierarchical codes: {len(hierarchical_codes)}")
        print(f"   Flat codes: {len(flat_codes)}")
        
        # 6. Display hierarchy
        if hierarchical_codes:
            print("\n6. HIERARCHICAL STRUCTURE FOUND:")
            for code in data['codes']:
                if code.get('level', 0) == 0 and code.get('child_codes'):
                    print(f"\n   PARENT: {code['code_name']}")
                    print(f"   - Level: {code.get('level', 0)}")
                    print(f"   - Children: {code.get('child_codes', [])}")
                    
                    # Find children
                    for child in data['codes']:
                        if child.get('parent_id') == code['code_name']:
                            print(f"     CHILD: {child['code_name']}")
                            print(f"     - Parent: {child.get('parent_id')}")
                            print(f"     - Level: {child.get('level', 1)}")
        
        # 7. Save evidence
        print("\n7. SAVING EVIDENCE...")
        with open('evidence/current/direct_llm_hierarchy_test.json', 'w') as f:
            json.dump({
                'prompt': prompt,
                'response': data,
                'hierarchical_count': len(hierarchical_codes),
                'flat_count': len(flat_codes),
                'success': len(hierarchical_codes) > 0
            }, f, indent=2)
        print("   [OK] Evidence saved")
        
        # Result
        print("\n" + "=" * 60)
        if hierarchical_codes:
            print("SUCCESS: LLM generated hierarchical codes!")
            return True
        else:
            print("FAILURE: LLM did not generate hierarchical codes")
            return False
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_direct_llm_hierarchy())
    exit(0 if success else 1)