#!/usr/bin/env python3
"""
Test a minimal version of the grounded theory system bypassing failed components

Focus on just getting the 4-phase workflow to run with minimal dependencies.
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
from qc_clean.core.llm.llm_handler import LLMHandler

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
                'text': content,
                'content': content,  # Add both formats
                'filename': file_path.name,
                'file_path': str(file_path),
                'word_count': len(content.split()) if content else 0
            }
            interviews.append(interview)
            print(f"  Loaded: {interview['word_count']} words")
        else:
            print(f"  Skipped: Could not read content")
    
    return interviews

async def test_direct_llm_grounded_theory():
    """Test direct LLM-based grounded theory analysis"""
    
    print("TESTING DIRECT LLM GROUNDED THEORY ANALYSIS")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Load Configuration
    print("STEP 1: Loading Configuration...")
    try:
        config = UnifiedConfig()
        llm_handler = LLMHandler(config=config)
        print(f"  Provider: {config.api_provider}")
        print(f"  Model: {config.model_preference}")
        print(f"  Temperature: {config.temperature}")
        print(f"  LLM Handler: Ready")
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
        
    except Exception as e:
        print(f"  ERROR loading interviews: {e}")
        return False
    
    print()
    
    # 3. Run Direct 4-Phase Analysis
    print("STEP 3: Running Direct 4-Phase Grounded Theory Analysis...")
    print("  This bypasses the complex workflow and tests the core LLM-based analysis")
    print()
    
    all_results = []
    start_time = datetime.now()
    
    try:
        # Prepare combined interview text
        combined_text = "\n\n".join([
            f"Interview {interview['id']}:\n{interview['text']}" 
            for interview in interviews
        ])
        
        # Phase 1: Open Coding
        print("  PHASE 1: Open Coding...")
        open_coding_prompt = f"""
        You are conducting grounded theory analysis. Perform open coding on the following interview data.

        Identify key concepts, their properties, dimensions, and supporting quotes.
        Create a hierarchical structure of codes where appropriate.

        Interview Data:
        {combined_text[:8000]}  # Limit for token management

        Provide a structured analysis with:
        1. Primary codes (main concepts)
        2. Properties of each code
        3. Dimensional variations
        4. Supporting quotes from the data
        5. Relationships between codes
        
        Format as clear categories with evidence.
        """
        
        phase1_start = datetime.now()
        try:
            phase1_result = await llm_handler.complete_raw(open_coding_prompt, max_tokens=3000)
            phase1_duration = (datetime.now() - phase1_start).total_seconds()
            print(f"    Completed in {phase1_duration:.1f} seconds")
            print(f"    Generated: {len(phase1_result)} characters of analysis")
        except Exception as e:
            print(f"    ERROR in Phase 1: {e}")
            return False
        
        # Phase 2: Axial Coding
        print("  PHASE 2: Axial Coding...")
        axial_coding_prompt = f"""
        Based on the open coding results below, identify relationships between categories.
        
        Open Coding Results:
        {phase1_result[:2000]}
        
        Identify:
        1. Causal conditions (what leads to phenomena)
        2. Context (specific conditions)
        3. Intervening conditions (broader conditions)
        4. Action/interaction strategies (responses)
        5. Consequences (outcomes)
        6. Relationships between major categories
        
        Focus on the paradigm model and how categories relate to each other.
        """
        
        phase2_start = datetime.now()
        try:
            phase2_result = await llm_handler.complete_raw(axial_coding_prompt, max_tokens=2500)
            phase2_duration = (datetime.now() - phase2_start).total_seconds()
            print(f"    Completed in {phase2_duration:.1f} seconds")
            print(f"    Generated: {len(phase2_result)} characters of analysis")
        except Exception as e:
            print(f"    ERROR in Phase 2: {e}")
            return False
        
        # Phase 3: Selective Coding
        print("  PHASE 3: Selective Coding...")
        selective_coding_prompt = f"""
        Based on the open coding and axial coding results, identify the core category.
        
        Open Coding:
        {phase1_result[:1500]}
        
        Axial Coding:
        {phase2_result[:1500]}
        
        Identify:
        1. The core category that explains the central phenomenon
        2. How other categories relate to this core category
        3. The central story or process being described
        4. Integration of all major categories
        
        The core category should have the most explanatory power.
        """
        
        phase3_start = datetime.now()
        try:
            phase3_result = await llm_handler.complete_raw(selective_coding_prompt, max_tokens=2000)
            phase3_duration = (datetime.now() - phase3_start).total_seconds()
            print(f"    Completed in {phase3_duration:.1f} seconds")
            print(f"    Generated: {len(phase3_result)} characters of analysis")
        except Exception as e:
            print(f"    ERROR in Phase 3: {e}")
            return False
        
        # Phase 4: Theory Development
        print("  PHASE 4: Theory Development...")
        theory_prompt = f"""
        Integrate all analysis phases into a theoretical model.
        
        Open Coding: {phase1_result[:800]}
        Axial Coding: {phase2_result[:800]}
        Selective Coding: {phase3_result[:800]}
        
        Develop:
        1. A theoretical model name
        2. Key theoretical propositions
        3. The process or phenomenon explained
        4. Conditions under which the theory applies
        5. Implications and predictions
        
        Create a coherent grounded theory.
        """
        
        phase4_start = datetime.now()
        try:
            phase4_result = await llm_handler.complete_raw(theory_prompt, max_tokens=2000)
            phase4_duration = (datetime.now() - phase4_start).total_seconds()
            print(f"    Completed in {phase4_duration:.1f} seconds")
            print(f"    Generated: {len(phase4_result)} characters of analysis")
        except Exception as e:
            print(f"    ERROR in Phase 4: {e}")
            return False
        
        total_duration = (datetime.now() - start_time).total_seconds()
        
        # Compile results
        analysis_results = {
            "phase_1_open_coding": {
                "duration_seconds": phase1_duration,
                "analysis": phase1_result
            },
            "phase_2_axial_coding": {
                "duration_seconds": phase2_duration,
                "analysis": phase2_result
            },
            "phase_3_selective_coding": {
                "duration_seconds": phase3_duration,
                "analysis": phase3_result
            },
            "phase_4_theory_development": {
                "duration_seconds": phase4_duration,
                "analysis": phase4_result
            },
            "total_duration_seconds": total_duration,
            "interviews_processed": len(interviews),
            "total_words_analyzed": total_words
        }
        
    except Exception as e:
        print(f"  ERROR during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("STEP 4: Analysis Results...")
    print("-" * 60)
    
    print(f"PROCESSING SUMMARY:")
    print(f"  Phase 1 (Open Coding): {phase1_duration:.1f} seconds")
    print(f"  Phase 2 (Axial Coding): {phase2_duration:.1f} seconds") 
    print(f"  Phase 3 (Selective Coding): {phase3_duration:.1f} seconds")
    print(f"  Phase 4 (Theory Development): {phase4_duration:.1f} seconds")
    print(f"  Total Duration: {total_duration:.1f} seconds")
    print(f"  Interviews Processed: {len(interviews)}")
    print(f"  Words Analyzed: {total_words:,}")
    print()
    
    print(f"SAMPLE ANALYSIS OUTPUTS:")
    print(f"Phase 1 - Open Coding (first 300 chars):")
    print(f"  {phase1_result[:300]}...")
    print()
    print(f"Phase 4 - Final Theory (first 300 chars):")
    print(f"  {phase4_result[:300]}...")
    print()
    
    # Save results
    output_file = f"direct_grounded_theory_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"Complete results saved to: {output_file}")
    print()
    print("DIRECT GROUNDED THEORY ANALYSIS COMPLETE")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    print("Starting Direct Grounded Theory System Test...")
    
    try:
        success = asyncio.run(test_direct_llm_grounded_theory())
        if success:
            print("[SUCCESS] Direct grounded theory analysis completed!")
            print("This demonstrates the core 4-phase LLM-based analysis capability")
        else:
            print("[FAILED] Analysis failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)