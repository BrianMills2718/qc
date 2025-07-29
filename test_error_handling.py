"""
Test script to validate error handling improvements
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from qc.models.simplified_schemas import transform_to_full_schema, SimpleGlobalResult, SimpleTheme, SimpleCode, SimpleQuoteChain
from qc.core.error_recovery import DataFixer
import logging

logging.basicConfig(level=logging.INFO)

def test_chain_type_normalization():
    """Test various chain type inputs"""
    print("\n=== Testing Chain Type Normalization ===")
    
    test_cases = [
        "problem-solution",
        "problem solution", 
        "Problem_Solution",
        "PROBLEM-SOLUTION",
        "evolution",
        "contradiction",
        "consensus_building",
        "consensus-building",
        "invalid_type",
        "evolutionary",
        "contradictory"
    ]
    
    # Create minimal test data
    for test_type in test_cases:
        result = SimpleGlobalResult(
            themes=[],
            codes=[],
            quote_chains=[SimpleQuoteChain(
                chain_id="TEST_001",
                theme_id="THEME_001",
                chain_type=test_type,
                description="Test chain",
                quotes=["Test quote"]
            )],
            contradictions=[],
            stakeholder_positions=[],
            theoretical_insights=["Test insight"],
            emergent_theory="Test theory",
            methodological_notes="Test notes",
            saturation_point="INT_010",
            saturation_evidence="Test evidence",
            overall_confidence=0.8
        )
        
        try:
            metadata = {"study_id": "test", "research_question": "test"}
            transformed = transform_to_full_schema(result, metadata)
            actual_type = transformed['quote_chains'][0].chain_type
            print(f"'{test_type}' -> '{actual_type}'")
        except Exception as e:
            print(f"'{test_type}' -> ERROR: {str(e)}")

def test_prevalence_parsing():
    """Test prevalence string parsing"""
    print("\n=== Testing Prevalence String Parsing ===")
    
    fixer = DataFixer()
    
    test_prevalences = [
        "universal across all interviews",
        "highly prevalent in 80% of interviews",
        "mentioned in 15 of 18 interviews",
        "low prevalence",
        "rare",
        "moderate",
        "found in most interviews",
        "universal",
        "50%",
        "0.75",
        "invalid string"
    ]
    
    for prev_str in test_prevalences:
        theme = {'prevalence': prev_str}
        fixed = fixer.fix_response_data({'themes': [theme]})
        result = fixed['themes'][0]['prevalence']
        print(f"'{prev_str}' -> {result}")

def test_error_resilience():
    """Test that partial failures don't crash the whole analysis"""
    print("\n=== Testing Error Resilience ===")
    
    # Create data with some bad elements
    result = SimpleGlobalResult(
        themes=[
            SimpleTheme(
                theme_id="THEME_001",
                name="Good Theme",
                description="Valid theme",
                prevalence=0.8,
                interviews_count=15,
                key_quotes=["Good quote"],
                confidence_score=0.9
            ),
            SimpleTheme(
                theme_id="THEME_002",
                name="",  # Missing name
                description="",  # Missing description
                prevalence=0.5,
                interviews_count=10,
                key_quotes=[],  # No quotes
                confidence_score=0.5
            )
        ],
        codes=[],
        quote_chains=[
            SimpleQuoteChain(
                chain_id="CHAIN_001",
                theme_id="THEME_001",
                chain_type="invalid-chain-type",  # Bad chain type
                description="Test",
                quotes=["Quote 1"]
            )
        ],
        contradictions=[],
        stakeholder_positions=[],
        theoretical_insights=["Insight 1"],
        emergent_theory="Theory",
        methodological_notes="Notes",
        saturation_point="INT_010",
        saturation_evidence="Evidence",
        overall_confidence=0.8
    )
    
    try:
        metadata = {"study_id": "test", "research_question": "test"}
        transformed = transform_to_full_schema(result, metadata)
        print(f"Themes transformed: {len(transformed['themes'])}")
        print(f"Quote chains transformed: {len(transformed['quote_chains'])}")
        print("SUCCESS: Partial failures handled gracefully")
    except Exception as e:
        print(f"FAILED: {str(e)}")

if __name__ == "__main__":
    test_chain_type_normalization()
    test_prevalence_parsing()
    test_error_resilience()
    print("\n=== All Tests Complete ===")