"""
Test that the prompt format includes code IDs
"""

import sys
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import (
    ExtractionConfig, ExtractionApproach, HierarchicalCode, CodeTaxonomy
)

def test_prompt_format():
    """Test that prompts include code IDs"""
    print("\n" + "="*60)
    print("Testing Prompt Format with Code IDs")
    print("="*60)
    
    # Create a mock config
    config = ExtractionConfig(
        analytic_question="Test question",
        interview_files=["test.docx"],
        coding_approach=ExtractionApproach.OPEN,
        output_dir="test_output",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash"
    )
    
    # Create extractor
    extractor = CodeFirstExtractor(config)
    
    # Create a mock taxonomy
    extractor.code_taxonomy = CodeTaxonomy(
        codes=[
            HierarchicalCode(
                id="AI_IMPACT_RESEARCH_TASKS",
                name="AI's Impact on Research Tasks",
                description="How AI affects research",
                semantic_definition="Test definition",
                parent_id=None,
                level=1,
                example_quotes=["Example quote"],
                discovery_confidence=0.9
            ),
            HierarchicalCode(
                id="AI_IMPACT_TRANSCRIPTION",
                name="AI for Transcription",
                description="Using AI for transcription",
                semantic_definition="Test definition",
                parent_id="AI_IMPACT_RESEARCH_TASKS",
                level=2,
                example_quotes=["Example quote"],
                discovery_confidence=0.9
            )
        ],
        total_codes=2,
        hierarchy_depth=2,
        discovery_method="open",
        analytic_question="Test question",
        extraction_confidence=0.9
    )
    
    # Test the format method
    formatted_codes = extractor._format_codes_for_prompt()
    
    print("\nFormatted codes for prompt:")
    print("-" * 40)
    print(formatted_codes)
    print("-" * 40)
    
    # Check if IDs are included
    if "[AI_IMPACT_RESEARCH_TASKS]" in formatted_codes:
        print("\n>>> SUCCESS: Code IDs are included in brackets!")
        print("  - Found [AI_IMPACT_RESEARCH_TASKS]")
    else:
        print("\n>>> ERROR: Code IDs are not included!")
        return False
    
    if "[AI_IMPACT_TRANSCRIPTION]" in formatted_codes:
        print("  - Found [AI_IMPACT_TRANSCRIPTION]")
    else:
        print("\n>>> ERROR: Child code ID not found!")
        return False
    
    # Test that it maintains hierarchy
    lines = formatted_codes.split('\n')
    # Level 1 has 2 spaces (1 * "  "), level 2 has 4 spaces (2 * "  ")
    if lines[0].startswith('  - [') and lines[1].startswith('    - ['):
        print("\n>>> SUCCESS: Hierarchy is preserved with indentation!")
        print(f"  Level 1: '{lines[0][:40]}'")
        print(f"  Level 2: '{lines[1][:40]}'")
    else:
        print("\n>>> ERROR: Hierarchy not preserved!")
        print(f"  Line 0: '{lines[0][:40]}'")
        print(f"  Line 1: '{lines[1][:40]}'")
        return False
    
    return True

if __name__ == "__main__":
    success = test_prompt_format()
    
    print("\n" + "="*60)
    if success:
        print(">>> TEST PASSED: Prompt format is correct!")
    else:
        print(">>> TEST FAILED: Prompt format issue detected")
    print("="*60)
    
    sys.exit(0 if success else 1)