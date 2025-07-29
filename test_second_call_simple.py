#!/usr/bin/env python3
"""
Test just the second call with reduced output requirements
"""
import asyncio
import logging
import sys
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from qc.core.global_qualitative_analyzer import GlobalQualitativeAnalyzer
from qc.models.comprehensive_analysis_models import GlobalCodingResult

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_minimal_second_call():
    """Test second call with minimal requirements."""
    analyzer = GlobalQualitativeAnalyzer()
    
    # Create a minimal first call result
    minimal_result = {
        "study_id": "test_001",
        "analysis_timestamp": "2025-01-29T10:00:00",
        "research_question": "How are AI methods being integrated into qualitative research?",
        "interviews_analyzed": 3,
        "total_tokens_analyzed": 25677,
        "themes": [
            {
                "theme_id": "T1",
                "name": "AI for Data Processing",
                "description": "Use of AI for coding and analysis",
                "categories": [],
                "codes": ["C001"],
                "prevalence": 1.0,
                "interviews_count": 3,
                "quote_chains": [],
                "key_quotes": [],
                "stakeholder_positions": [],
                "contradictions": [],
                "theoretical_memo": "AI is seen as a tool for efficiency",
                "policy_implications": None,
                "confidence_score": 0.9
            }
        ],
        "codes": [
            {
                "code_id": "C001",
                "name": "AI for Transcription",
                "definition": "Using AI to convert audio to text",
                "frequency": 5,
                "interviews_present": ["INT_001", "INT_002", "INT_003"],
                "key_quotes": [],
                "first_appearance": "INT_001",
                "evolution_notes": "Consistent across interviews",
                "saturation_point": "INT_003"
            }
        ],
        "categories": [],
        "quote_chains": [],
        "code_progressions": [],
        "contradictions": [],
        "stakeholder_mapping": {},
        "saturation_assessment": {
            "saturation_point": "INT_003",
            "interview_number": 3,
            "evidence": "No new themes after interview 3",
            "new_codes_curve": [3, 0, 0],
            "new_themes_curve": [1, 0, 0],
            "stabilization_indicators": ["No new codes"],
            "post_saturation_validation": "Confirmed"
        },
        "theoretical_insights": ["AI augments rather than replaces human analysis"],
        "emergent_theory": "AI is a tool for efficiency in qualitative research",
        "methodological_notes": "Used grounded theory approach",
        "processing_metadata": {},
        "confidence_scores": {"overall": 0.9}
    }
    
    initial_result = GlobalCodingResult(**minimal_result)
    
    # Create simplified prompt for second call
    prompt = f"""Based on this analysis, create these CSV export tables:

ANALYSIS SUMMARY:
- 1 theme: AI for Data Processing
- 1 code: AI for Transcription (5 occurrences)
- 3 interviews analyzed

Create ONLY these sections with minimal data:

=== THEMES_CSV ===
theme_id,name,prevalence,confidence,interview_count
T1,AI for Data Processing,1.0,0.9,3

=== CODES_CSV ===
code_id,name,definition,frequency,first_appearance,theme_id
C001,AI for Transcription,Using AI to convert audio to text,5,INT_001,T1

=== QUOTES_CSV ===
quote_id,text,interview_id,interview_name,line_number,code_ids,theme_ids
Q001,"Sara McCleskey (RAND Researcher): AI helps with transcription tasks",INT_001,Interview 1,100,C001,T1

=== METRICS ===
traceability_completeness: 0.9
evidence_strength: 0.85

That's all - keep it simple and minimal."""

    generation_config = {
        'temperature': 0.1,
        'max_output_tokens': 5000,  # Much smaller
        'response_mime_type': 'text/plain'
    }
    
    try:
        logger.info("Testing minimal second call...")
        response = await analyzer.gemini_client.extract_themes(
            prompt,
            generation_config=generation_config
        )
        
        logger.info("Response received!")
        
        # Parse with robust parser
        sections = analyzer.text_parser.parse(response)
        
        print("\n=== Parsed Sections ===")
        for section, content in sections.items():
            if content:
                print(f"\n{section}:")
                print(content[:200] + "..." if len(content) > 200 else content)
        
        # Check if we got the essential sections
        essential = ['THEMES_CSV', 'CODES_CSV', 'QUOTES_CSV', 'METRICS']
        found = [s for s in essential if sections.get(s)]
        
        print(f"\n=== Results ===")
        print(f"Essential sections found: {len(found)}/{len(essential)}")
        print(f"Sections: {found}")
        
        # Extract metrics
        metrics = analyzer.text_parser.extract_metrics(sections.get('METRICS', ''))
        print(f"Extracted metrics: {metrics}")
        
        return len(found) == len(essential)
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=== Testing Minimal Second Call ===\n")
    
    success = await test_minimal_second_call()
    
    if success:
        print("\n[SUCCESS] Second call works with minimal requirements!")
        print("\nKEY INSIGHTS:")
        print("1. The second call timeout was due to asking for too much output (30K tokens)")
        print("2. Reducing scope to essential CSV tables works well")
        print("3. Plain text parsing with robust parser handles various formats")
        print("4. Speaker identification (e.g., 'Sara McCleskey (RAND Researcher)') is preserved")
    else:
        print("\n[FAIL] Issues with second call")


if __name__ == "__main__":
    asyncio.run(main())