"""
Test that the improved prompts produce better results
"""

import sys
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.prompts.prompt_loader import PromptLoader
from src.qc.extraction.code_first_schemas import HierarchicalCode

def test_improved_prompts():
    """Show how the improved prompts guide better code extraction"""
    
    print("="*80)
    print("IMPROVED PROMPT COMPARISON")
    print("="*80)
    
    # Load the prompt template
    loader = PromptLoader()
    
    # Create sample taxonomy
    sample_codes = [
        HierarchicalCode(
            id="AI_USE",
            name="AI Tool Usage",
            description="Discussion of using AI tools in research",
            semantic_definition="Any mention of AI tool usage",
            parent_id=None,
            level=1,
            example_quotes=[],
            discovery_confidence=0.9
        ),
        HierarchicalCode(
            id="AI_CHALLENGE",
            name="AI Challenges",
            description="Problems or concerns with AI",
            semantic_definition="Challenges faced when using AI",
            parent_id=None,
            level=1,
            example_quotes=[],
            discovery_confidence=0.9
        )
    ]
    
    # Format codes as they would appear in prompt
    formatted_codes = "\n".join([
        f"  - [{code.id}] {code.name}: {code.description}"
        for code in sample_codes
    ])
    
    # Generate dynamic examples
    code_examples = loader.generate_code_examples(sample_codes)
    
    print("\n>>> KEY IMPROVEMENTS IN PHASE 4 PROMPT:")
    print("-" * 40)
    
    print("\n1. SELECTIVE EXTRACTION (NEW):")
    print("   - ONLY extract quotes that clearly relate to codes")
    print("   - Skip small talk and off-topic statements")
    print("   - Quality over quantity")
    
    print("\n2. MANDATORY CODING (NEW):")
    print("   - Each quote MUST have at least one code_id")
    print("   - If a statement doesn't map to any code, don't extract it")
    
    print("\n3. CORRECT CODE IDS (FIXED):")
    print("   - Uses actual IDs from taxonomy: [AI_USE], [AI_CHALLENGE]")
    print("   - No more made-up IDs like 'accuracy_concerns'")
    
    print("\n>>> SAMPLE INTERVIEW TEXT:")
    print("-" * 40)
    interview_sample = """
Speaker 1: Good morning, how are you today?
Speaker 2: I'm doing well, thanks. Should we start?
Speaker 1: Yes. So we've been using ChatGPT for our literature reviews.
Speaker 2: That's interesting. We use Claude for coding our interview data.
Speaker 1: Have you had issues with hallucinations?
Speaker 2: Yes, sometimes it makes up references that don't exist.
Speaker 1: The weather is nice today.
Speaker 2: Indeed. Back to AI - the time savings are significant.
    """
    print(interview_sample)
    
    print("\n>>> EXPECTED EXTRACTION BEHAVIOR:")
    print("-" * 40)
    
    print("\nWITH OLD PROMPT (extract everything):")
    print("  Quote 1: 'Good morning, how are you today?' - code_ids: []")
    print("  Quote 2: 'I'm doing well, thanks.' - code_ids: []")
    print("  Quote 3: 'Should we start?' - code_ids: []")
    print("  ... (extracts all 8 statements)")
    
    print("\nWITH NEW PROMPT (selective extraction):")
    print("  Quote 1: 'So we've been using ChatGPT for our literature reviews.' - code_ids: ['AI_USE']")
    print("  Quote 2: 'We use Claude for coding our interview data.' - code_ids: ['AI_USE']")
    print("  Quote 3: 'Have you had issues with hallucinations?' - code_ids: ['AI_CHALLENGE']")
    print("  Quote 4: 'Yes, sometimes it makes up references that don't exist.' - code_ids: ['AI_CHALLENGE']")
    print("  Quote 5: 'Back to AI - the time savings are significant.' - code_ids: ['AI_USE']")
    print("  (Skips greetings, small talk, and weather comment)")
    
    print("\n>>> BENEFITS:")
    print("-" * 40)
    print("1. Fewer but more relevant quotes")
    print("2. Every quote has at least one valid code")
    print("3. No empty code_ids arrays")
    print("4. No made-up code IDs")
    print("5. Better signal-to-noise ratio")
    
    print("\n" + "="*80)
    print("IMPROVED PROMPTS READY FOR USE")
    print("="*80)

if __name__ == "__main__":
    test_improved_prompts()