"""
Show the actual prompts being sent to the LLM
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

def show_prompts():
    """Display the actual prompts sent to the LLM"""
    
    # Load a real taxonomy from test output
    taxonomy_file = Path("test_output_full/taxonomy.json")
    if not taxonomy_file.exists():
        print(f"ERROR: {taxonomy_file} not found")
        return
    
    with open(taxonomy_file, 'r', encoding='utf-8') as f:
        taxonomy_data = json.load(f)
    
    # Create minimal config
    config = ExtractionConfig(
        analytic_question="What are the key themes regarding AI and qualitative research methods?",
        interview_files=["dummy.txt"],
        coding_approach=ExtractionApproach.OPEN,
        output_dir="test_prompts",
        auto_import_neo4j=False
    )
    
    # Create extractor
    extractor = CodeFirstExtractor(config)
    
    # Manually set the taxonomy from saved file
    from qc.extraction.code_first_schemas import HierarchicalCode, CodeTaxonomy
    codes = []
    for code_data in taxonomy_data['codes']:
        code = HierarchicalCode(
            id=code_data['id'],
            name=code_data['name'],
            description=code_data['description'],
            semantic_definition=code_data['semantic_definition'],
            parent_id=code_data.get('parent_id'),
            level=code_data['level'],
            example_quotes=code_data.get('example_quotes', []),
            discovery_confidence=code_data.get('discovery_confidence', 0.9)
        )
        codes.append(code)
    
    extractor.code_taxonomy = CodeTaxonomy(
        codes=codes,
        total_codes=len(codes),
        hierarchy_depth=3,
        discovery_method="test",
        analytic_question=config.analytic_question,
        extraction_confidence=0.9
    )
    
    # Also set minimal speaker schema
    from qc.extraction.code_first_schemas import DiscoveredSpeakerProperty, SpeakerPropertySchema
    extractor.speaker_schema = SpeakerPropertySchema(
        properties=[
            DiscoveredSpeakerProperty(
                name="Role",
                description="The role or position of the speaker",
                property_type="categorical",
                frequency=1.0,
                example_values=["Researcher", "Manager", "Analyst"],
                is_categorical=True,
                possible_values=["Researcher", "Manager", "Analyst"],
                confidence=0.9
            )
        ],
        total_properties=1,
        total_speakers_found=10,  # Add required field
        discovery_method="test",
        extraction_confidence=0.9
    )
    
    print("="*80)
    print("ACTUAL PROMPTS SENT TO LLM")
    print("="*80)
    
    # Show how codes are formatted
    print("\n>>> 1. HOW CODES ARE FORMATTED IN PROMPTS:")
    print("-" * 40)
    formatted_codes = extractor._format_codes_for_prompt()
    # Show first few lines
    lines = formatted_codes.split('\n')[:10]
    for line in lines:
        print(line)
    print(f"... and {len(formatted_codes.split(chr(10))) - 10} more lines")
    
    # Show Phase 4A prompt structure
    print("\n>>> 2. PHASE 4A PROMPT (Extract Quotes/Speakers):")
    print("-" * 40)
    
    sample_interview = """Speaker 1: We've been using AI for transcription and it's really helpful.
Speaker 2: Yes, but I worry about the accuracy with technical terms.
Speaker 1: That's true. We also use it for coding qualitative data.
Speaker 2: The time savings are significant but we need human validation."""
    
    phase4a_prompt = extractor._build_quotes_speakers_prompt(
        interview_text=sample_interview,
        interview_id="sample_interview_001"
    )
    
    # Show key sections
    sections = phase4a_prompt.split('\n\n')
    for i, section in enumerate(sections[:5]):  # First 5 sections
        if section.strip():
            print(f"\n[Section {i+1}]")
            # Truncate long sections
            if len(section) > 500:
                print(section[:500] + "...")
            else:
                print(section)
    
    print("\n>>> 3. CRITICAL INSTRUCTIONS FOR CODE IDS:")
    print("-" * 40)
    
    # Extract the critical instructions section
    if "CRITICAL INSTRUCTIONS" in phase4a_prompt:
        start = phase4a_prompt.find("CRITICAL INSTRUCTIONS")
        end = phase4a_prompt.find("\n\n", start + 500)
        if end == -1:
            end = start + 1000
        critical_section = phase4a_prompt[start:end]
        print(critical_section)
    
    print("\n>>> 4. EXAMPLE OF EXPECTED LLM RESPONSE:")
    print("-" * 40)
    print("""
Expected JSON structure from LLM:
{
  "quotes": [
    {
      "text": "We've been using AI for transcription and it's really helpful.",
      "speaker_name": "Speaker 1",
      "code_ids": ["C1.1.1"],  // <-- Should use EXACT IDs from taxonomy
      "line_start": 1,
      "line_end": 1
    },
    {
      "text": "Yes, but I worry about the accuracy with technical terms.",
      "speaker_name": "Speaker 2", 
      "code_ids": ["C2.1"],  // <-- Should match taxonomy IDs exactly
      "line_start": 2,
      "line_end": 2
    }
  ],
  "speakers": [...],
  "total_quotes": 4,
  ...
}
    """)
    
    print("\n>>> 5. WHAT THE LLM OFTEN RETURNS INSTEAD:")
    print("-" * 40)
    print("""
Common problematic responses:
{
  "quotes": [
    {
      "text": "We've been using AI for transcription...",
      "speaker_name": "Speaker 1",
      "code_ids": [],  // <-- Empty array (very common)
      "line_start": 1,
      "line_end": 1
    },
    {
      "text": "Yes, but I worry about the accuracy...",
      "speaker_name": "Speaker 2",
      "code_ids": ["accuracy_concerns", "technical_challenges"],  // <-- Made-up IDs!
      "line_start": 2,
      "line_end": 2
    }
  ],
  ...
}
    """)

if __name__ == "__main__":
    show_prompts()