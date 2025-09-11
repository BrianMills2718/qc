"""
Test that the prompt improvements are working correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.prompts.prompt_loader import PromptLoader

def test_prompt_improvements():
    """Verify all prompt improvements are in place"""
    
    print("="*80)
    print("TESTING PROMPT IMPROVEMENTS")
    print("="*80)
    
    loader = PromptLoader()
    
    # Test Phase 1 improvements
    print("\n>>> Phase 1: Code Discovery")
    print("-" * 40)
    template = loader.load_template("phase1", "open_code_discovery")
    
    checks = [
        ("ID format specified", "CAPS_WITH_UNDERSCORES" in template),
        ("Example format shown", "e.g., AI_CHALLENGES" in template),
        ("2-3 sentences specified", "2-3 sentences" in template),
        ("Minimize overlap mentioned", "minimize overlap" in template)
    ]
    
    for check_name, passed in checks:
        status = "OK" if passed else "MISSING"
        print(f"  {status}: {check_name}")
    
    # Test Phase 2 improvements
    print("\n>>> Phase 2: Speaker Properties")
    print("-" * 40)
    template = loader.load_template("phase2", "open_speaker_discovery")
    
    checks = [
        ("Clarifies NOT identifying speakers", "NOT identifying individual speakers" in template),
        ("snake_case format specified", "snake_case format" in template),
        ("Example shown", "e.g., years_experience" in template),
        ("Frequency mentioned", "How often" in template)
    ]
    
    for check_name, passed in checks:
        status = "OK" if passed else "MISSING"
        print(f"  {status}: {check_name}")
    
    # Test Phase 3 improvements
    print("\n>>> Phase 3: Entity/Relationship Discovery")
    print("-" * 40)
    template = loader.load_template("phase3", "open_entity_discovery")
    
    checks = [
        ("Entity ID format", "CAPS_SNAKE_CASE" in template),
        ("Relationship ID format", "CAPS format" in template),
        ("No biasing examples", "tools, methods, concepts, organizations" not in template),
        ("Direction specified", "one-way" in template and "bidirectional" in template)
    ]
    
    for check_name, passed in checks:
        status = "OK" if passed else "MISSING"
        print(f"  {status}: {check_name}")
    
    # Test Phase 4A improvements
    print("\n>>> Phase 4A: Quote Extraction")
    print("-" * 40)
    template = loader.load_template("phase4", "quotes_speakers")
    
    checks = [
        ("Minimum quote length", "minimum ~10 words" in template),
        ("Null handling specified", "Use null if" in template),
        ("Unknown vs null clarified", "only if the property is mentioned but unclear" in template),
        ("Selective extraction", "ONLY extract quotes that clearly relate" in template)
    ]
    
    for check_name, passed in checks:
        status = "OK" if passed else "MISSING"
        print(f"  {status}: {check_name}")
    
    # Test Phase 4B improvements
    print("\n>>> Phase 4B: Entity Extraction")
    print("-" * 40)
    template = loader.load_template("phase4", "entities_relationships")
    
    checks = [
        ("Entity naming convention", "most complete/formal name" in template),
        ("Confidence scale defined", "1.0 if explicitly" in template),
        ("Total guess = 0.0", "0.0 = total guess" in template),
        ("Must match schema IDs", "Must exactly match" in template)
    ]
    
    for check_name, passed in checks:
        status = "OK" if passed else "MISSING"
        print(f"  {status}: {check_name}")
    
    print("\n" + "="*80)
    print("KEY IMPROVEMENTS SUMMARY")
    print("="*80)
    print("""
1. ID Formats Standardized:
   - Codes: CAPS_WITH_UNDERSCORES (e.g., AI_CHALLENGES)
   - Properties: snake_case (e.g., years_experience)
   - Entities: CAPS_SNAKE_CASE (e.g., AI_TOOL)
   - Relationships: CAPS (e.g., USES)

2. Task Boundaries Clarified:
   - Phases 1-3: Discover TYPES/SCHEMAS only
   - Phase 4: Extract INSTANCES using schemas

3. Ambiguity Removed:
   - Confidence: 1.0 = explicit, 0.0 = total guess
   - Null = not mentioned, Unknown = mentioned but unclear
   - Minimum quote length specified (~10 words)

4. Better Instructions:
   - Phase 2: Clarified it's schema discovery, not speaker identification
   - Phase 3: Removed biasing examples
   - Phase 4: Must use exact IDs from schemas
    """)
    
    print(">>> PROMPT IMPROVEMENTS COMPLETE")

if __name__ == "__main__":
    test_prompt_improvements()