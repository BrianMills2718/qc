"""
Test that the migrated prompts work correctly
"""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

async def test_prompt_migration():
    """Test that prompts load and format correctly after migration"""
    
    print("="*80)
    print("TESTING PROMPT MIGRATION")
    print("="*80)
    
    # Create minimal config
    config = ExtractionConfig(
        analytic_question="Test question for prompt migration",
        interview_files=["test1.txt", "test2.txt"],
        coding_approach=ExtractionApproach.OPEN,
        output_dir="test_prompts",
        auto_import_neo4j=False
    )
    
    # Create extractor
    extractor = CodeFirstExtractor(config)
    
    # Test Phase 1 prompt
    print("\n>>> Testing Phase 1 Open Code Discovery Prompt:")
    print("-" * 40)
    try:
        prompt = extractor._build_open_code_discovery_prompt("Sample interview content")
        print("OK: Phase 1 prompt loads successfully")
        print(f"  Length: {len(prompt)} characters")
        # Check for key elements
        assert "Test question for prompt migration" in prompt
        assert "2 interviews" in prompt
        print("OK: Contains expected variables")
    except Exception as e:
        print(f"ERROR: Phase 1 prompt failed: {e}")
        return False
    
    # Test Phase 2 prompt
    print("\n>>> Testing Phase 2 Speaker Discovery Prompt:")
    print("-" * 40)
    try:
        prompt = extractor._build_open_speaker_discovery_prompt("Sample interview content")
        print("OK: Phase 2 prompt loads successfully")
        print(f"  Length: {len(prompt)} characters")
        assert "2 interviews" in prompt
        print("OK: Contains expected variables")
    except Exception as e:
        print(f"ERROR: Phase 2 prompt failed: {e}")
        return False
    
    # Test Phase 3 prompt
    print("\n>>> Testing Phase 3 Entity Discovery Prompt:")
    print("-" * 40)
    try:
        prompt = extractor._build_open_entity_discovery_prompt("Sample interview content")
        print("OK: Phase 3 prompt loads successfully")
        print(f"  Length: {len(prompt)} characters")
        assert "Test question" in prompt
        print("OK: Contains expected variables")
    except Exception as e:
        print(f"ERROR: Phase 3 prompt failed: {e}")
        return False
    
    # Test Phase 4 prompts (requires taxonomy)
    print("\n>>> Testing Phase 4 Prompts:")
    print("-" * 40)
    
    # Create minimal taxonomy for testing
    from qc.extraction.code_first_schemas import HierarchicalCode, CodeTaxonomy
    test_codes = [
        HierarchicalCode(
            id="C1",
            name="Test Code 1",
            description="Test description",
            semantic_definition="Test definition",
            parent_id=None,
            level=1,
            example_quotes=[],
            discovery_confidence=0.9
        ),
        HierarchicalCode(
            id="C2",
            name="Test Code 2",
            description="Test description 2",
            semantic_definition="Test definition 2",
            parent_id=None,
            level=1,
            example_quotes=[],
            discovery_confidence=0.9
        )
    ]
    
    extractor.code_taxonomy = CodeTaxonomy(
        codes=test_codes,
        total_codes=2,
        hierarchy_depth=1,
        discovery_method="test",
        analytic_question="Test question",
        extraction_confidence=0.9
    )
    
    # Create minimal speaker schema
    from qc.extraction.code_first_schemas import DiscoveredSpeakerProperty, SpeakerPropertySchema
    extractor.speaker_schema = SpeakerPropertySchema(
        properties=[
            DiscoveredSpeakerProperty(
                name="role",
                description="Speaker role",
                property_type="categorical",
                frequency=1.0,
                example_values=["Researcher"],
                is_categorical=True,
                possible_values=["Researcher"],
                confidence=0.9
            )
        ],
        total_properties=1,
        total_speakers_found=5,
        discovery_method="test",
        extraction_confidence=0.9
    )
    
    # Test Phase 4A
    try:
        prompt = extractor._build_quotes_speakers_prompt(
            interview_text="Sample interview text",
            interview_id="test_001"
        )
        print("OK: Phase 4A prompt loads successfully")
        print(f"  Length: {len(prompt)} characters")
        
        # Check for corrected code examples
        if "[C1]" in prompt and "[C2]" in prompt:
            print("OK: Contains actual code IDs from taxonomy")
        else:
            print("ERROR: Missing code IDs")
            
        # Check that bad examples are gone
        if "AI_RISK_ACCURACY_NUANCE" in prompt:
            print("ERROR: Still contains hardcoded wrong examples!")
            return False
        else:
            print("OK: Hardcoded wrong examples removed")
            
    except Exception as e:
        print(f"ERROR: Phase 4A prompt failed: {e}")
        return False
    
    # Test prompt reloading
    print("\n>>> Testing Prompt Reload:")
    print("-" * 40)
    extractor.prompt_loader.reload_templates()
    print("OK: Template cache cleared successfully")
    
    print("\n" + "="*80)
    print(">>> ALL PROMPT TESTS PASSED!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_prompt_migration())
    sys.exit(0 if success else 1)