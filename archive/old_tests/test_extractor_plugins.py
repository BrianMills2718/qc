#!/usr/bin/env python3
"""
Test Extractor Plugin System

Verify that extractor plugins are working correctly and producing different results.
"""

import sys
from pathlib import Path

# Add qc_clean to path
sys.path.insert(0, str(Path(__file__).parent / 'qc_clean'))

def test_extractor_plugin_loading():
    """Test that extractor plugins can be loaded"""
    try:
        from plugins.extractors import get_available_extractors, get_extractor_plugin
        
        extractors = get_available_extractors()
        print(f"Available extractors: {extractors}")
        
        # Test loading each extractor
        for extractor_name in extractors:
            extractor = get_extractor_plugin(extractor_name)
            if extractor:
                print(f"✅ {extractor_name}: {extractor.get_description()}")
                print(f"   Capabilities: {extractor.get_capabilities()}")
            else:
                print(f"❌ {extractor_name}: Failed to load")
        
        return len(extractors) >= 3
        
    except Exception as e:
        print(f"❌ Plugin loading failed: {e}")
        return False

def test_extractor_differences():
    """Test that different extractors produce different results"""
    try:
        from plugins.extractors import get_extractor_plugin
        
        # Test interview data
        interview_data = {
            'id': 'test_interview',
            'content': '''
            I think AI is really changing how we do qualitative research. 
            The traditional methods are still important, but technology offers new possibilities.
            However, there are challenges with reliability and validation.
            The benefits include speed and the ability to process large amounts of data.
            '''
        }
        
        # Test configuration
        config = {
            'llm_handler': None,  # Mock for testing
            'coding_approach': 'open',
            'relationship_threshold': 0.7,
            'semantic_units': ['sentence', 'paragraph'],
            'validation_level': 'standard',
            'consolidation_enabled': True
        }
        
        # Test each extractor
        extractors_to_test = ['hierarchical', 'relationship', 'semantic']
        results = {}
        
        for extractor_name in extractors_to_test:
            extractor = get_extractor_plugin(extractor_name)
            if extractor:
                codes = extractor.extract_codes(interview_data, config)
                results[extractor_name] = codes
                print(f"✅ {extractor_name}: Generated {len(codes)} codes")
                
                # Show first code as example
                if codes:
                    first_code = codes[0]
                    print(f"   Example code: {first_code.get('code_name', 'unknown')}")
                    print(f"   Description: {first_code.get('description', 'No description')[:50]}...")
        
        # Check that results are different
        if len(results) >= 2:
            extractor_names = list(results.keys())
            codes_1 = set(code.get('code_name', '') for code in results[extractor_names[0]])
            codes_2 = set(code.get('code_name', '') for code in results[extractor_names[1]])
            
            # Calculate difference
            intersection = codes_1.intersection(codes_2)
            union = codes_1.union(codes_2)
            difference = 1.0 - (len(intersection) / len(union)) if union else 0.0
            
            print(f"Code difference between {extractor_names[0]} and {extractor_names[1]}: {difference:.2f}")
            return difference > 0.3  # Should be >30% different
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Extractor difference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_integration():
    """Test that GT workflow can use extractor plugins"""
    try:
        # This test would require full system setup, so just check imports work
        from core.workflow.grounded_theory import GroundedTheoryWorkflow
        print("✅ GT workflow can import extractor integration")
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Extractor Plugin System")
    print("=" * 40)
    
    tests = [
        ("Plugin Loading", test_extractor_plugin_loading),
        ("Extractor Differences", test_extractor_differences), 
        ("Workflow Integration", test_workflow_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        result = test_func()
        results.append(result)
        status = "PASS" if result else "FAIL"
        print(f"Result: {status}")
    
    print(f"\n{'='*40}")
    print(f"Overall: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✅ All tests passed - Extractor plugin system is working!")
    else:
        print("❌ Some tests failed - Need to investigate")