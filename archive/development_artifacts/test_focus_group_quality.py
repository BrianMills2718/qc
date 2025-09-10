#!/usr/bin/env python3
"""
Test script to verify conservative connection detection on focus group
"""
import asyncio
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_extractor import CodeFirstExtractor
from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach
from src.qc.analysis.quality_assessment import QualityAssessmentFramework

async def test_focus_group_quality():
    """Test focus group processing with improved prompts"""
    
    # Configuration for test
    config = ExtractionConfig(
        analytic_question="How are researchers experiencing and adapting to the integration of AI tools in qualitative research methods?",
        interview_files_dir=Path("data/interviews/ai_interviews_3_for_test"),
        coding_approach=ExtractionApproach.CLOSED,  # Use existing taxonomy
        speaker_approach=ExtractionApproach.CLOSED,
        entity_approach=ExtractionApproach.CLOSED,
        output_dir="test_quality_single",
        auto_import_neo4j=False,
        llm_model="gemini/gemini-2.5-flash",
        temperature=0.1,
        max_concurrent_interviews=1
    )
    
    # Load existing schemas
    config.predefined_codes_file = "output_production/taxonomy.json"
    config.predefined_speaker_schema_file = "output_production/speaker_schema.json"
    config.predefined_entity_schema_file = "output_production/entity_schema.json"
    
    extractor = CodeFirstExtractor(config)
    
    # Find just the focus group file
    focus_group_file = None
    for file_path in config.interview_files_dir.glob("*.docx"):
        if "Focus Group" in file_path.name:
            focus_group_file = file_path
            break
    
    if not focus_group_file:
        print("No focus group file found!")
        return
    
    print(f"Testing focus group: {focus_group_file.name}")
    
    # Process just this one file
    try:
        # We need to call the Phase 4 processing directly on the focus group
        from qc.extraction.dialogue_processor import DialogueProcessor
        from qc.prompts.prompt_loader import PromptLoader
        from qc.llm.llm_handler import LLMHandler
        
        # Initialize components
        llm_handler = LLMHandler(config.llm_model, config.temperature)
        prompt_loader = PromptLoader()
        dialogue_processor = DialogueProcessor()
        
        # Read the focus group file
        if focus_group_file.suffix.lower() == '.docx':
            import docx
            doc = docx.Document(focus_group_file)
            interview_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        else:
            with open(focus_group_file, 'r', encoding='utf-8') as f:
                interview_text = f.read()
        
        print(f"Interview text length: {len(interview_text)} characters")
        
        # Load existing schemas
        with open("output_production/taxonomy.json", 'r') as f:
            taxonomy = json.load(f)
        
        with open("output_production/speaker_schema.json", 'r') as f:
            speaker_schema = json.load(f)
        
        # Detect dialogue structure
        dialogue_result = dialogue_processor.analyze_dialogue_structure(
            interview_text, focus_group_file.stem
        )
        
        print(f"Dialogue analysis: {dialogue_result.interview_type} with {dialogue_result.dialogue_turn_count} turns")
        
        # Load and prepare prompt for focus group
        if dialogue_result.interview_type == 'focus_group':
            phase4_prompt = prompt_loader.load_prompt('phase4', 'dialogue_aware_quotes.txt')
            
            # Format prompt with schemas
            formatted_codes = ""
            for code in taxonomy.get('codes', []):
                formatted_codes += f"[{code['id']}] {code['name']}: {code.get('description', '')}\n"
            
            formatted_speaker_schema = ""
            for prop in speaker_schema.get('properties', []):
                required = "(required)" if prop.get('required', False) else "(optional)"
                formatted_speaker_schema += f"{prop['name']} {required}: {prop.get('description', '')}\n"
            
            # Prepare code examples
            code_examples = ""
            for i, code in enumerate(taxonomy.get('codes', [])[:3]):  # First 3 codes as examples
                code_examples += f"Example {i+1}: code_ids: [\"{code['id']}\"]\n"
            
            formatted_prompt = phase4_prompt.format(
                interview_id=focus_group_file.stem,
                analytic_question=config.analytic_question,
                speaker_count=len(dialogue_result.identified_speakers),
                formatted_codes=formatted_codes,
                formatted_speaker_schema=formatted_speaker_schema,
                code_examples=code_examples,
                interview_text=interview_text
            )
            
            print("Calling LLM with enhanced conservative prompts...")
            
            # Call LLM
            response = await llm_handler.complete_with_structured_output(
                messages=[{"role": "user", "content": formatted_prompt}],
                output_schema={
                    "type": "object",
                    "properties": {
                        "quotes": {"type": "array"},
                        "speakers": {"type": "array"},
                        "total_quotes": {"type": "integer"},
                        "total_codes_applied": {"type": "integer"},
                        "thematic_connections_detected": {"type": "integer"}
                    }
                }
            )
            
            print(f"Extraction completed:")
            print(f"  Total quotes: {response.get('total_quotes', 0)}")
            print(f"  Thematic connections: {response.get('thematic_connections_detected', 0)}")
            
            # Calculate connection rate
            connection_rate = response.get('thematic_connections_detected', 0) / response.get('total_quotes', 1)
            print(f"  Connection rate: {connection_rate:.1%}")
            
            # Save result
            output_file = Path("test_quality_single") / "focus_group_test.json"
            output_file.parent.mkdir(exist_ok=True)
            
            result_data = {
                'interview_id': focus_group_file.stem,
                'quotes': response.get('quotes', []),
                'speakers': response.get('speakers', []),
                'dialogue_analysis': dialogue_result.__dict__
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to: {output_file}")
            
            # Run quality assessment
            framework = QualityAssessmentFramework()
            assessment = framework.assess_processing_quality(result_data)
            
            print("\n=== QUALITY ASSESSMENT ===")
            print(f"Overall Quality Score: {assessment['overall_quality_score']:.2f}")
            print(f"Connection Rate: {assessment['connection_quality']['metrics']['connection_rate']:.1%}")
            
            print("\nQuality Alerts:")
            for alert in assessment['connection_quality']['alerts']:
                print(f"  {alert['severity'].upper()}: {alert['message']}")
            
            print("\nRecommendations:")
            for rec in assessment['recommendations']:
                print(f"  - {rec}")
            
            # Success criteria check
            target_range = (0.3, 0.6)  # 30-60% connection rate
            if target_range[0] <= connection_rate <= target_range[1]:
                print(f"\n✅ SUCCESS: Connection rate ({connection_rate:.1%}) is within target range ({target_range[0]:.0%}-{target_range[1]:.0%})")
                return True
            else:
                print(f"\n⚠️  IMPROVEMENT NEEDED: Connection rate ({connection_rate:.1%}) is outside target range ({target_range[0]:.0%}-{target_range[1]:.0%})")
                return False
        
    except Exception as e:
        print(f"Error processing focus group: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_focus_group_quality())
    sys.exit(0 if result else 1)