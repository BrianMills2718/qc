#!/usr/bin/env python3
"""
Progressive Schema Complexity Testing for LiteLLM
Tests LLM with schemas of increasing complexity to isolate parsing issues
"""

import asyncio
from pydantic import BaseModel, Field
from typing import List
from src.qc.llm.llm_handler import LLMHandler

# Test schemas of increasing complexity
class SimpleSchema(BaseModel):
    name: str
    value: int

class MediumSchema(BaseModel):
    name: str
    description: str
    properties: List[str]
    confidence: float

class ComplexSchema(BaseModel):
    name: str
    description: str
    properties: List[str]
    dimensions: List[str]
    supporting_quotes: List[str]
    frequency: int
    confidence: float

# Current problematic schema from GT workflow
class OpenCodeSchema(BaseModel):
    code_name: str = Field(description="Name of the open code")
    description: str = Field(description="Description of what this code represents")
    properties: List[str] = Field(description="Properties of this concept")
    dimensions: List[str] = Field(description="Dimensional variations")
    supporting_quotes: List[str] = Field(description="Quotes that support this code")
    frequency: int = Field(description="Number of occurrences")
    confidence: float = Field(description="Confidence in this code 0-1")

class OpenCodesResponse(BaseModel):
    open_codes: List[OpenCodeSchema] = Field(description="List of open codes identified")

async def test_schema_complexity():
    """Test LLM with schemas of increasing complexity"""
    
    # Test with realistic configuration
    from src.qc.config.methodology_config import MethodologyConfigManager
    from pathlib import Path
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_realistic.yaml"))
    
    llm = LLMHandler(config=config)
    
    schemas = [
        ("Simple", SimpleSchema, "Generate a simple name-value pair. Name should be 'test_item', value should be 42."),
        ("Medium", MediumSchema, "Generate information about a research concept with name 'Communication', description 'Team communication patterns', properties ['frequency', 'clarity'], and confidence 0.8."), 
        ("Complex", ComplexSchema, "Generate a research code with name 'Adaptation', description 'Organizational adaptation strategies', properties ['flexibility'], dimensions ['proactive-reactive'], quotes ['Sample quote'], frequency 3, confidence 0.9."),
        ("OpenCode", OpenCodeSchema, "Generate one open code with name 'Technology_Use', description 'How participants use technology', properties ['ease', 'frequency'], dimensions ['expert-novice'], quotes ['I use it daily'], frequency 2, confidence 0.8."),
        ("OpenCodesArray", OpenCodesResponse, "Generate 2 open codes: first about 'Communication' with frequency 3, second about 'Technology' with frequency 2.")
    ]
    
    for name, schema, prompt in schemas:
        print(f"\n=== Testing {name} Schema ===")
        print(f"Prompt: {prompt[:100]}...")
        
        try:
            result = await llm.extract_structured(
                prompt=prompt,
                schema=schema,
                max_tokens=2000  # Start with lower limit
            )
            print(f"SUCCESS: {name} schema extraction worked")
            print(f"  Result type: {type(result)}")
            
            # Show specific results
            if name == "OpenCodesArray" and hasattr(result, 'open_codes'):
                print(f"  Generated {len(result.open_codes)} codes")
                for i, code in enumerate(result.open_codes):
                    print(f"    Code {i+1}: {code.code_name} (freq={code.frequency})")
            elif hasattr(result, 'name'):
                print(f"  Generated: {result.name}")
            elif hasattr(result, 'code_name'):
                print(f"  Generated code: {result.code_name} (freq={getattr(result, 'frequency', 'N/A')})")
            
        except Exception as e:
            print(f"FAILED: {name} schema extraction failed")
            print(f"  Error: {e}")
            print(f"  Error type: {type(e).__name__}")
            
            # For failures, try to get raw response to debug
            try:
                raw = await llm.complete_raw(prompt, max_tokens=2000)
                print(f"  Raw response available: {bool(raw)}")
                if raw:
                    print(f"  Raw response length: {len(raw)}")
                    print(f"  Raw response preview: {raw[:200]}...")
                else:
                    print("  Raw response is None/empty - this is the core issue")
            except Exception as raw_error:
                print(f"  Could not get raw response: {raw_error}")

async def test_prompt_length_limits():
    """Test different prompt lengths to find the breaking point"""
    
    print("\n=== Prompt Length Limit Testing ===")
    
    from src.qc.config.methodology_config import MethodologyConfigManager
    from pathlib import Path
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_realistic.yaml"))
    
    llm = LLMHandler(config=config)
    
    # Generate prompts of different lengths
    base_prompt = "Analyze this text and generate a simple response: "
    test_texts = [
        "Short text." * 10,         # ~100 chars
        "Medium text. " * 100,      # ~1,300 chars  
        "Longer text. " * 1000,     # ~13,000 chars
        "Very long text. " * 5000,  # ~70,000 chars (similar to our failing case)
    ]
    
    for i, test_text in enumerate(test_texts):
        prompt = base_prompt + test_text
        print(f"\nTest {i+1}: Prompt length {len(prompt)} characters")
        
        try:
            # Test raw completion first
            raw_response = await llm.complete_raw(prompt, max_tokens=1000)
            
            if raw_response:
                print(f"  OK Raw response: {len(raw_response)} chars")
            else:
                print(f"  FAIL Raw response: None (FAILURE POINT IDENTIFIED)")
                break
                
        except Exception as e:
            print(f"  FAIL Raw completion failed: {e}")
            break

async def run_tests():
    """Run all tests"""
    print("Schema Complexity Testing")
    print("=" * 50)
    
    await test_schema_complexity()
    await test_prompt_length_limits()
    
    print("\n" + "=" * 50)
    print("Testing Complete")

if __name__ == "__main__":
    asyncio.run(run_tests())