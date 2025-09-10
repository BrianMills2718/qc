#!/usr/bin/env python3
"""
Test the ACTUAL full 4-phase grounded theory system using qc_clean/ structure

This tests the complete system described in README.md:
Phase 1: Theme Discovery → Phase 2: Speaker Intelligence → 
Phase 3: Entity Network Discovery → Phase 4: Application

NOT the hierarchical extractor plugin we tested before.
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))

from qc_clean.config.unified_config import UnifiedConfig
from qc_clean.core.cli.robust_cli_operations import RobustCLIOperations
from qc_clean.core.workflow.grounded_theory import GroundedTheoryWorkflow
from config.methodology_config import GroundedTheoryConfig

def read_docx_content(file_path):
    """Read content from DOCX files"""
    try:
        import docx
        doc = docx.Document(file_path)
        content = ""
        for paragraph in doc.paragraphs:
            content += paragraph.text + "\n"
        return content.strip()
    except ImportError:
        print("Warning: python-docx not installed. Cannot read DOCX files.")
        return None
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {e}")
        return None

def load_interview_data(directory):
    """Load interview data from the specified directory"""
    interview_dir = Path(directory)
    
    if not interview_dir.exists():
        print(f"Directory not found: {interview_dir}")
        return []
    
    interviews = []
    for file_path in interview_dir.glob("*.docx"):
        print(f"Loading: {file_path.name}")
        
        content = read_docx_content(file_path)
        if content:
            interview = {
                'id': file_path.stem,
                'interview_id': file_path.stem,
                'text': content,  # Use 'text' field as expected by workflow
                'filename': file_path.name,
                'file_path': str(file_path),
                'word_count': len(content.split()) if content else 0
            }
            interviews.append(interview)
            print(f"  Loaded: {interview['word_count']} words")
        else:
            print(f"  Skipped: Could not read content")
    
    return interviews

async def test_full_grounded_theory_workflow():
    """Test the complete 4-phase grounded theory workflow"""
    
    print("TESTING FULL GROUNDED THEORY WORKFLOW")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Load Configuration
    print("STEP 1: Loading Configuration...")
    try:
        config = UnifiedConfig()
        print(f"  Provider: {config.api_provider}")
        print(f"  Model: {config.model_preference}")
        print(f"  Temperature: {config.temperature}")
        print(f"  API Key: {config.api_key[:20]}... [OK]")
    except Exception as e:
        print(f"  ERROR loading configuration: {e}")
        return False
    
    print()
    
    # 2. Load Interview Data
    print("STEP 2: Loading Interview Data...")
    interview_dir = "C:\\Users\\Brian\\projects\\qualitative_coding\\data\\interviews\\ai_interviews_3_for_test"
    
    try:
        interviews = load_interview_data(interview_dir)
        if not interviews:
            print("  ERROR: No interviews loaded!")
            return False
        
        print(f"  Loaded: {len(interviews)} interviews")
        total_words = sum(i['word_count'] for i in interviews)
        print(f"  Total words: {total_words:,}")
        
        for interview in interviews:
            print(f"    - {interview['filename']}: {interview['word_count']} words")
        
    except Exception as e:
        print(f"  ERROR loading interviews: {e}")
        return False
    
    print()
    
    # 3. Initialize Full Grounded Theory System
    print("STEP 3: Initializing Full Grounded Theory System...")
    try:
        # Create robust CLI operations (needed by workflow)
        cli_ops = RobustCLIOperations(config=config)
        
        # Initialize the systems
        await cli_ops.initialize_systems()
        
        # Create methodology config for grounded theory
        gt_config = GroundedTheoryConfig(
            methodology="grounded_theory",
            theoretical_sensitivity="medium",
            coding_depth="focused",
            memo_generation_frequency="each_phase",
            report_formats=["academic_report"],
            include_audit_trail=True,
            include_supporting_quotes=True,
            minimum_code_frequency=1,
            relationship_confidence_threshold=0.7,
            validation_level="standard",
            temperature=0.1,
            max_tokens=4000,
            model_preference="gpt-4o-mini"
        )
        
        # Create the complete workflow
        gt_workflow = GroundedTheoryWorkflow(
            robust_operations=cli_ops,
            config=gt_config
        )
        
        print(f"  Workflow initialized: Grounded Theory")
        print(f"  Configuration: {gt_config.methodology}")
        print(f"  Extractor: {gt_workflow.extractor_plugin.get_name() if gt_workflow.extractor_plugin else 'none'}")
        
    except Exception as e:
        print(f"  ERROR initializing workflow: {e}")
        return False
    
    print()
    
    # 4. Run Complete 4-Phase Workflow
    print("STEP 4: Running Complete 4-Phase Grounded Theory Analysis...")
    print("  Expected phases:")
    print("    Phase 1: Open Coding - Identify concepts and categories")
    print("    Phase 2: Axial Coding - Identify relationships between categories")  
    print("    Phase 3: Selective Coding - Develop core categories")
    print("    Phase 4: Theoretical Integration - Generate theoretical model")
    print()
    
    try:
        start_time = datetime.now()
        
        # Run the COMPLETE workflow (not just single extractor)
        print("  Starting complete grounded theory analysis...")
        results = await gt_workflow.execute_complete_workflow(interviews)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"  COMPLETED in {duration:.1f} seconds")
        
    except Exception as e:
        print(f"  ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # 5. Analyze Results
    print("STEP 5: Analyzing Complete Results...")
    print("-" * 60)
    
    try:
        # Extract results
        open_codes = results.open_codes
        axial_relationships = results.axial_relationships
        core_categories = results.core_categories
        theoretical_model = results.theoretical_model
        memos = results.supporting_memos
        metadata = results.analysis_metadata
        
        print(f"PHASE RESULTS:")
        print(f"  Phase 1 - Open Codes: {len(open_codes)} codes identified")
        print(f"  Phase 2 - Axial Relationships: {len(axial_relationships)} relationships")
        print(f"  Phase 3 - Core Categories: {len(core_categories)} core categories")
        print(f"  Phase 4 - Theoretical Model: '{theoretical_model.model_name}'")
        print(f"  Supporting Memos: {len(memos)} memos generated")
        print()
        
        print(f"PROCESSING METRICS:")
        print(f"  Total Duration: {duration:.1f} seconds")
        print(f"  Interviews Processed: {metadata.get('interview_count', 'unknown')}")
        print(f"  Analysis Steps: {len(metadata.get('analysis_steps', []))}")
        print()
        
        # Show sample open codes
        print(f"SAMPLE OPEN CODES (top 5):")
        for i, code in enumerate(open_codes[:5], 1):
            indent = "  " * code.level if hasattr(code, 'level') else ""
            print(f"  {i}. {indent}{code.code_name} (conf: {code.confidence:.2f})")
            print(f"      {code.description}")
        
        if len(open_codes) > 5:
            print(f"  ... and {len(open_codes) - 5} more codes")
        print()
        
        # Show core categories
        print(f"CORE CATEGORIES:")
        for i, category in enumerate(core_categories, 1):
            print(f"  {i}. {category.category_name}")
            print(f"     Definition: {category.definition}")
            print(f"     Explains: {category.central_phenomenon}")
        print()
        
        # Show theoretical model
        print(f"THEORETICAL MODEL:")
        print(f"  Model: {theoretical_model.model_name}")
        print(f"  Framework: {theoretical_model.theoretical_framework}")
        print(f"  Propositions: {len(theoretical_model.propositions)}")
        for prop in theoretical_model.propositions[:3]:
            print(f"    - {prop}")
        print()
        
        # Save results
        output_file = f"full_grounded_theory_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to serializable format
        results_dict = {
            "analysis_metadata": metadata,
            "open_codes": [code.dict() for code in open_codes],
            "axial_relationships": [rel.dict() for rel in axial_relationships],
            "core_categories": [cat.dict() for cat in core_categories],
            "theoretical_model": theoretical_model.dict(),
            "supporting_memos": memos,
            "processing_time_seconds": duration
        }
        
        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"Complete results saved to: {output_file}")
        
    except Exception as e:
        print(f"  ERROR analyzing results: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("FULL GROUNDED THEORY ANALYSIS COMPLETE")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("Starting Full Grounded Theory System Test...")
    
    try:
        success = asyncio.run(test_full_grounded_theory_workflow())
        if success:
            print("[SUCCESS] Full grounded theory analysis completed!")
            print("This is the ACTUAL 4-phase system described in README.md")
        else:
            print("[FAILED] Full analysis failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)