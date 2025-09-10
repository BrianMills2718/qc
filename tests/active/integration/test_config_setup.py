"""
Quick test to verify configuration and file access
"""

import sys
import yaml
from pathlib import Path
sys.path.insert(0, 'src')

from src.qc.extraction.code_first_schemas import ExtractionConfig, ExtractionApproach

def test_configuration():
    """Test that configuration is valid"""
    
    print("="*80)
    print("CONFIGURATION TEST")
    print("="*80)
    
    # Load configuration
    config_file = "extraction_config_test.yaml"
    
    if not Path(config_file).exists():
        print(f"ERROR: ERROR: {config_file} not found!")
        return False
    
    print(f"OK: Found configuration file: {config_file}")
    
    with open(config_file, 'r') as f:
        config_data = yaml.safe_load(f)
    
    print("\n[CONFIG] Configuration Contents:")
    print(f"  - Analytic Question: {config_data['analytic_question'][:50]}...")
    print(f"  - Number of Interview Files: {len(config_data['interview_files'])}")
    print(f"  - Approach: {config_data['coding_approach']}")
    print(f"  - Output Directory: {config_data['output_dir']}")
    print(f"  - LLM Model: {config_data['llm_model']}")
    
    # Check if all interview files exist
    print("\n[FILES] Checking Interview Files:")
    all_exist = True
    for i, file_path in enumerate(config_data['interview_files'], 1):
        path = Path(file_path)
        if path.exists():
            size_kb = path.stat().st_size / 1024
            print(f"  {i}. OK: {path.name} ({size_kb:.1f} KB)")
        else:
            print(f"  {i}. ERROR: {path.name} - FILE NOT FOUND!")
            all_exist = False
    
    if not all_exist:
        print("\nERROR: ERROR: Some interview files are missing!")
        return False
    
    # Try to create the configuration object
    print("\n[TEST] Testing Configuration Object Creation...")
    try:
        config = ExtractionConfig(
            analytic_question=config_data['analytic_question'],
            interview_files=config_data['interview_files'],
            coding_approach=ExtractionApproach[config_data['coding_approach'].upper()],
            speaker_approach=ExtractionApproach[config_data['speaker_approach'].upper()],
            entity_approach=ExtractionApproach[config_data['entity_approach'].upper()],
            output_dir=config_data['output_dir'],
            code_hierarchy_depth=config_data['code_hierarchy_depth'],
            llm_model=config_data['llm_model'],
            max_concurrent_interviews=config_data.get('max_concurrent_interviews', 3),
            auto_import_neo4j=config_data['auto_import_neo4j']
        )
        print("OK: Configuration object created successfully")
    except Exception as e:
        print(f"ERROR: ERROR creating configuration: {e}")
        return False
    
    # Check environment
    print("\n[ENV] Checking Environment:")
    import os
    if os.getenv('GEMINI_API_KEY'):
        key = os.getenv('GEMINI_API_KEY')
        print(f"OK: GEMINI_API_KEY found (length: {len(key)} chars)")
    else:
        print("WARNING: GEMINI_API_KEY not found in environment")
        print("   You'll need to set this before running the extraction")
    
    # Test reading a sample from first file
    print("\n[READ] Testing File Reading (first file sample):")
    try:
        from src.qc.extraction.code_first_extractor import CodeFirstExtractor
        extractor = CodeFirstExtractor(config)
        
        first_file = config.interview_files[0]
        content = extractor._read_interview_file(first_file)
        
        # Check for location markers
        if "[Paragraph" in content[:500]:
            print("OK: File reader is adding paragraph markers correctly")
        elif "[Line" in content[:500]:
            print("OK: File reader is adding line markers correctly")
        else:
            print("WARNING: No location markers found - check file reader")
        
        print(f"   First 200 chars: {content[:200]}...")
        
    except Exception as e:
        print(f"ERROR: ERROR reading file: {e}")
        return False
    
    print("\n" + "="*80)
    print("CONFIGURATION TEST COMPLETE")
    print("="*80)
    
    print("\nOK: All checks passed! Ready to run extraction.")
    print("\nTo run the full extraction, use:")
    print("  python run_test_extraction.py")
    
    return True

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1)