#!/usr/bin/env python3
"""
Direct Extractor Test

Test extractors directly without going through plugin system.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_hierarchical_extractor():
    """Test hierarchical extractor directly"""
    try:
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        
        extractor = HierarchicalExtractor()
        print(f"Name: {extractor.get_name()}")
        print(f"Version: {extractor.get_version()}")
        print(f"Description: {extractor.get_description()}")
        print(f"Capabilities: {extractor.get_capabilities()}")
        
        # Test extraction
        interview_data = {
            'id': 'test_001',
            'content': 'AI is transforming qualitative research methods. Traditional approaches remain important but technology offers new possibilities.'
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open'
        }
        
        codes = extractor.extract_codes(interview_data, config)
        print(f"Generated {len(codes)} codes")
        
        for i, code in enumerate(codes[:3]):  # Show first 3
            print(f"  {i+1}. {code.get('code_name', 'unknown')} - {code.get('description', 'No description')}")
        
        return len(codes) > 0
        
    except Exception as e:
        print(f"Hierarchical extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_relationship_extractor():
    """Test relationship extractor directly"""
    try:
        from plugins.extractors.relationship_extractor import RelationshipExtractor
        
        extractor = RelationshipExtractor()
        print(f"Name: {extractor.get_name()}")
        print(f"Description: {extractor.get_description()}")
        
        # Test extraction
        interview_data = {
            'id': 'test_002', 
            'content': 'Technology influences research methods. Methods encounter challenges. Technology provides benefits.'
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'relationship_threshold': 0.5
        }
        
        codes = extractor.extract_codes(interview_data, config)
        print(f"Generated {len(codes)} codes")
        
        # Show codes with relationships
        for code in codes[:3]:
            relationships = code.get('relationships', [])
            print(f"  - {code.get('code_name', 'unknown')} ({len(relationships)} relationships)")
        
        return len(codes) > 0
        
    except Exception as e:
        print(f"Relationship extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extractors_produce_different_results():
    """Test that different extractors produce different results"""
    try:
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        from plugins.extractors.relationship_extractor import RelationshipExtractor
        
        # Same input data
        interview_data = {
            'id': 'comparison_test',
            'content': 'AI technology is revolutionizing qualitative research. Traditional methods face new challenges but also gain powerful capabilities.'
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'relationship_threshold': 0.5
        }
        
        # Test both extractors
        h_extractor = HierarchicalExtractor()
        r_extractor = RelationshipExtractor()
        
        h_codes = h_extractor.extract_codes(interview_data, config)
        r_codes = r_extractor.extract_codes(interview_data, config)
        
        print(f"Hierarchical: {len(h_codes)} codes")
        print(f"Relationship: {len(r_codes)} codes")
        
        # Compare code names
        h_names = set(code.get('code_name', '') for code in h_codes)
        r_names = set(code.get('code_name', '') for code in r_codes)
        
        intersection = h_names.intersection(r_names)
        union = h_names.union(r_names)
        difference = 1.0 - (len(intersection) / len(union)) if union else 0.0
        
        print(f"Code name difference: {difference:.2f}")
        print(f"Intersection: {intersection}")
        print(f"H-only: {h_names - r_names}")  
        print(f"R-only: {r_names - h_names}")
        
        return difference > 0.3  # Should be >30% different
        
    except Exception as e:
        print(f"Difference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Direct Extractor Test")
    print("=" * 20)
    
    tests = [
        ("Hierarchical Extractor", test_hierarchical_extractor),
        ("Relationship Extractor", test_relationship_extractor),
        ("Different Results", test_extractors_produce_different_results)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 15)
        result = test_func()
        results.append(result)
        status = "PASS" if result else "FAIL" 
        print(f"Result: {status}")
    
    print(f"\n{'='*20}")
    print(f"Overall: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("SUCCESS: Extractor plugins working!")
    else:
        print("Some tests failed")