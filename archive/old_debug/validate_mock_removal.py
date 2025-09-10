import subprocess
import sys

def validate_no_mock_systems():
    """Validate that all mock systems have been removed from test files"""
    
    print("=== Mock System Removal Validation ===")
    
    mock_patterns = [
        "MockOpenCode",
        "MockAxialRelationship", 
        "MockCoreCategory", 
        "MockGroundedTheoryResults",
        "create_mock_",
        "fallback_mock",
        "predetermined_result",
        "mock_interview_data",
        "run_mock_analysis",
        "mock_open_coding",
        "mock_axial_coding", 
        "mock_selective_coding",
        "mock_theory_integration",
        "MagicMock",
        "AsyncMock",
        "falling back to mock",
        "fall back to mock"
    ]
    
    test_files = [
        "test_configuration_behavior.py",
        "test_llm_configuration_integration.py", 
        "test_end_to_end_behavioral_integration.py",
        "test_post_processing_configuration.py",
        "test_deterministic_configuration_causation.py"
    ]
    
    violations_found = []
    
    for file_name in test_files:
        try:
            with open(file_name, 'r') as f:
                content = f.read()
                
            for pattern in mock_patterns:
                if pattern in content:
                    violations_found.append(f"{file_name}: Contains '{pattern}'")
                    
        except FileNotFoundError:
            print(f"Warning: {file_name} not found")
    
    if violations_found:
        print("FAIL: Mock system violations found:")
        for violation in violations_found:
            print(f"  - {violation}")
        return False
    else:
        print("PASS: No mock system violations detected")
        return True

if __name__ == "__main__":
    success = validate_no_mock_systems()
    exit(0 if success else 1)