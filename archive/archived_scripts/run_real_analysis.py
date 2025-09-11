#!/usr/bin/env python3
"""
Run Real Qualitative Coding Analysis
Uses the new UnifiedConfig system with OpenAI to analyze actual interview data
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Add the qc_clean path to sys.path
sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))

from qc_clean.config.unified_config import UnifiedConfig
from qc_clean.plugins.extractors.hierarchical_extractor import HierarchicalExtractor
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
                'content': content,
                'filename': file_path.name,
                'file_path': str(file_path),
                'word_count': len(content.split()) if content else 0
            }
            interviews.append(interview)
            print(f"  Loaded: {interview['word_count']} words")
        else:
            print(f"  Skipped: Could not read content")
    
    return interviews

async def run_qualitative_analysis():
    """Run the complete qualitative analysis workflow"""
    
    print("REAL QUALITATIVE CODING ANALYSIS")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Load Configuration
    print("STEP 1: Loading Configuration...")
    try:
        config = UnifiedConfig()
        print(f"  Provider: {config.api_provider}")
        print(f"  Model: {config.model_preference}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Methodology: {config.methodology.value}")
        print(f"  Extractor: {config.extractor_type.value}")
        
        # Verify API key is available
        if not config.api_key:
            print("  ERROR: No API key found!")
            return False
        
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
    
    # 3. Initialize Analysis System
    print("STEP 3: Initializing Analysis System...")
    try:
        # Create LLM handler with unified config
        llm_handler = LLMHandler(config=config)
        
        # Create hierarchical extractor
        extractor = HierarchicalExtractor(llm_handler=llm_handler)
        
        print(f"  Extractor: {extractor.get_name()} v{extractor.get_version()}")
        print(f"  Description: {extractor.get_description()}")
        print(f"  LLM Handler: Ready [OK]")
        
    except Exception as e:
        print(f"  ERROR initializing analysis system: {e}")
        return False
    
    print()
    
    # 4. Run Analysis on Each Interview
    print("STEP 4: Running Qualitative Analysis...")
    all_results = []
    
    for i, interview in enumerate(interviews, 1):
        print(f"  Analyzing {i}/{len(interviews)}: {interview['filename']}")
        print(f"    Words: {interview['word_count']:,}")
        
        try:
            # Prepare extraction config
            extraction_config = config.get_extractor_config()
            
            # Run the extraction
            print("    Running hierarchical extraction...")
            start_time = datetime.now()
            
            # Run the actual qualitative coding
            try:
                # The extractor uses asyncio internally, so we need to handle this properly
                codes = extractor.extract_codes(interview, extraction_config)
            except RuntimeError as e:
                if "asyncio.run() cannot be called from a running event loop" in str(e):
                    # Try calling the async method directly
                    extraction_state = {
                        'original_text': interview['content'],
                        'interview_id': interview['id'],
                        'config': extraction_config,
                        'codes': [],
                        'relationships': [],
                        'hierarchy': {},
                        'metadata': {
                            'extractor': 'hierarchical',
                            'phases_completed': [],
                            'llm_calls_made': 0,
                            'text_length': len(interview['content'])
                        }
                    }
                    
                    # Call the async extraction method directly
                    extraction_state = await extractor._run_async_extraction(extraction_state)
                    codes = extractor._format_results(extraction_state)
                else:
                    raise e
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"    Completed in {duration:.1f} seconds")
            print(f"    Generated: {len(codes) if codes else 0} codes")
            
            # Store results
            result = {
                'interview_id': interview['id'],
                'filename': interview['filename'],
                'word_count': interview['word_count'],
                'codes_generated': len(codes) if codes else 0,
                'processing_time': duration,
                'codes': codes[:5] if codes else [],  # Store first 5 codes as sample
                'timestamp': end_time.isoformat()
            }
            
            all_results.append(result)
            
            # Show sample codes
            if codes:
                print(f"    Sample codes:")
                for j, code in enumerate(codes[:3], 1):
                    if isinstance(code, dict):
                        code_text = code.get('code', str(code))
                    else:
                        code_text = str(code)
                    print(f"      {j}. {code_text}")
            else:
                print(f"    WARNING: No codes generated")
            
        except Exception as e:
            print(f"    ERROR: {e}")
            result = {
                'interview_id': interview['id'],
                'filename': interview['filename'],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            all_results.append(result)
        
        print()
    
    # 5. Generate Summary
    print("STEP 5: Analysis Summary")
    print("-" * 40)
    
    successful_analyses = [r for r in all_results if 'error' not in r]
    failed_analyses = [r for r in all_results if 'error' in r]
    
    print(f"Total Interviews: {len(interviews)}")
    print(f"Successful Analyses: {len(successful_analyses)}")
    print(f"Failed Analyses: {len(failed_analyses)}")
    
    if successful_analyses:
        total_codes = sum(r['codes_generated'] for r in successful_analyses)
        avg_codes = total_codes / len(successful_analyses)
        total_time = sum(r['processing_time'] for r in successful_analyses)
        
        print(f"Total Codes Generated: {total_codes}")
        print(f"Average Codes per Interview: {avg_codes:.1f}")
        print(f"Total Processing Time: {total_time:.1f} seconds")
        print(f"Average Time per Interview: {total_time/len(successful_analyses):.1f} seconds")
        
        print()
        print("Results by Interview:")
        for result in successful_analyses:
            print(f"  - {result['filename']}: {result['codes_generated']} codes ({result['processing_time']:.1f}s)")
    
    if failed_analyses:
        print()
        print("Failed Analyses:")
        for result in failed_analyses:
            print(f"  - {result['filename']}: {result['error']}")
    
    # Save results to file
    output_file = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print()
    print(f"Results saved to: {output_file}")
    
    print()
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    
    return len(successful_analyses) > 0

if __name__ == "__main__":
    print("Starting Real Qualitative Coding Analysis...")
    
    try:
        success = asyncio.run(run_qualitative_analysis())
        if success:
            print("[SUCCESS] Analysis completed successfully!")
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