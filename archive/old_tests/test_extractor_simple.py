#!/usr/bin/env python3
"""
Simple Extractor Plugin Test

Basic test for extractor plugin functionality.
"""

import sys
import os
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_basic_import():
    """Test basic import of extractor plugins"""
    try:
        # Import extractor base
        from plugins.extractors.base_extractor import ExtractorPlugin
        print("Base extractor imported successfully")
        
        # Import specific extractors
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        from plugins.extractors.relationship_extractor import RelationshipExtractor 
        from plugins.extractors.semantic_extractor import SemanticExtractor
        from plugins.extractors.validated_extractor import ValidatedExtractor
        
        print("All extractor classes imported successfully")
        
        # Test instantiation
        extractors = [
            HierarchicalExtractor(),
            RelationshipExtractor(),
            SemanticExtractor(),
            ValidatedExtractor()
        ]
        
        for extractor in extractors:
            print(f"- {extractor.get_name()}: {extractor.get_description()}")
        
        return True
        
    except Exception as e:
        print(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_extraction():
    """Test basic extraction functionality"""
    try:
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        
        # Create test data
        interview_data = {
            'id': 'test_001',
            'content': 'AI is transforming research methods. Traditional approaches remain important.'
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open'
        }
        
        # Test extraction
        extractor = HierarchicalExtractor()
        codes = extractor.extract_codes(interview_data, config)
        
        print(f"Extraction successful: Generated {len(codes)} codes")
        if codes:
            print(f"First code: {codes[0].get('code_name', 'unknown')}")
            
        return len(codes) > 0
        
    except Exception as e:
        print(f"Extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple Extractor Plugin Test")
    print("=" * 30)
    
    tests = [
        ("Basic Import", test_basic_import),
        ("Basic Extraction", test_basic_extraction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 15)
        result = test_func()
        results.append(result)
        status = "PASS" if result else "FAIL"
        print(f"Result: {status}")
    
    print(f"\nOverall: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("All tests passed!")
    else:
        print("Some tests failed")