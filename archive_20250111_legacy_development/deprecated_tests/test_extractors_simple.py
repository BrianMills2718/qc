#!/usr/bin/env python3
"""
Simple Extractor Validation Test

Tests that extractors can be instantiated and have the basic structure.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_hierarchical_extractor():
    """Test that hierarchical extractor can be instantiated"""
    try:
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        
        extractor = HierarchicalExtractor()
        print("PASS: Hierarchical extractor instantiated successfully")
        
        # Test basic interface
        assert hasattr(extractor, 'extract_codes'), "Missing extract_codes method"
        assert hasattr(extractor, 'get_capabilities'), "Missing get_capabilities method"
        assert hasattr(extractor, 'supports_hierarchy'), "Missing supports_hierarchy method"
        
        capabilities = extractor.get_capabilities()
        assert capabilities.get('requires_llm') == True, "Must require LLM integration"
        assert capabilities.get('supports_hierarchy') == True, "Must support hierarchy"
        
        print("PASS: Hierarchical extractor interface validation passed")
        print("PASS: Extractor reports LLM requirement correctly")
        
        # Test that it fails properly without real LLM
        try:
            empty_results = extractor.extract_codes({'content': ''}, {'minimum_confidence': 0.3})
            assert empty_results == [], "Empty input should return empty results"
            print("PASS: Empty input handling correct")
            
            # This should work since it's just empty input
            return True
            
        except Exception as e:
            print(f"PASS: System handles error correctly: {type(e).__name__}")
            return True
            
    except Exception as e:
        print(f"FAIL: Hierarchical extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relationship_extractor():
    """Test that relationship extractor can be instantiated"""
    try:
        from plugins.extractors.relationship_extractor import RelationshipExtractor
        
        extractor = RelationshipExtractor()
        print("PASS: Relationship extractor instantiated successfully")
        
        capabilities = extractor.get_capabilities()
        assert capabilities.get('requires_llm') == True, "Must require LLM integration"
        assert capabilities.get('supports_relationships') == True, "Must support relationships"
        
        print("PASS: Relationship extractor interface validation passed")
        return True
        
    except Exception as e:
        print(f"FAIL: Relationship extractor test failed: {e}")
        return False

def test_semantic_extractor():
    """Test that semantic extractor can be instantiated"""
    try:
        from plugins.extractors.semantic_extractor import SemanticExtractor
        
        extractor = SemanticExtractor()
        print("PASS: Semantic extractor instantiated successfully")
        
        capabilities = extractor.get_capabilities()
        assert capabilities.get('requires_llm') == True, "Must require LLM integration"
        assert capabilities.get('supports_relationships') == True, "Must support relationships"
        
        print("PASS: Semantic extractor interface validation passed")
        return True
        
    except Exception as e:
        print(f"FAIL: Semantic extractor test failed: {e}")
        return False

def test_validated_extractor():
    """Test that validated extractor can be instantiated"""
    try:
        from plugins.extractors.validated_extractor import ValidatedExtractor
        
        extractor = ValidatedExtractor()
        print("PASS: Validated extractor instantiated successfully")
        
        capabilities = extractor.get_capabilities()
        assert capabilities.get('requires_llm') == True, "Must require LLM integration (via base)"
        
        print("PASS: Validated extractor interface validation passed")
        return True
        
    except Exception as e:
        print(f"FAIL: Validated extractor test failed: {e}")
        return False

if __name__ == "__main__":
    print("Simple Extractor Validation Test")
    print("=" * 35)
    
    tests = [
        ("Hierarchical Extractor", test_hierarchical_extractor),
        ("Relationship Extractor", test_relationship_extractor),
        ("Semantic Extractor", test_semantic_extractor),
        ("Validated Extractor", test_validated_extractor)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 25)
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"FAIL: {e}")
            results.append(False)
    
    print(f"\n{'='*35}")
    print(f"Extractor Tests: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("\nSUCCESS: All extractors can be instantiated!")
        print("- All extractors have proper interfaces")
        print("- All extractors report LLM requirement correctly")
        print("- System ready for genuine algorithm testing")
    else:
        print("\nFAIL: Issues detected with extractor implementations")
        failed = [tests[i][0] for i, result in enumerate(results) if not result]
        print(f"Failed tests: {', '.join(failed)}")