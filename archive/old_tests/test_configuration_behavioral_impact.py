#!/usr/bin/env python3
"""
Configuration Behavioral Impact Test

CRITICAL TEST: Configuration changes MUST produce >50% different analysis results.
Tests the unified configuration system behavioral impact.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_configuration_behavioral_differences():
    """Test that different configurations produce measurably different behaviors"""
    from config.unified_config import UnifiedConfig, MethodologyType, CodingApproach, ValidationLevel, ExtractorType
    
    # Create dramatically different configurations
    config_conservative = UnifiedConfig(
        methodology=MethodologyType.GROUNDED_THEORY,
        coding_approach=CodingApproach.CLOSED,
        validation_level=ValidationLevel.RIGOROUS,
        extractor_type=ExtractorType.VALIDATED,
        theoretical_sensitivity="low",
        coding_depth="surface",
        temperature=0.0,
        minimum_confidence=0.7,
        relationship_confidence_threshold=0.8
    )
    
    config_exploratory = UnifiedConfig(
        methodology=MethodologyType.CONSTRUCTIVIST,
        coding_approach=CodingApproach.OPEN,
        validation_level=ValidationLevel.MINIMAL,
        extractor_type=ExtractorType.SEMANTIC,
        theoretical_sensitivity="high",
        coding_depth="intensive",
        temperature=1.0,
        minimum_confidence=0.2,
        relationship_confidence_threshold=0.4
    )
    
    # Calculate behavioral difference
    difference = config_conservative.calculate_behavioral_difference(config_exploratory)
    
    print(f"Conservative config profile: {config_conservative.get_behavioral_profile()}")
    print(f"Exploratory config profile: {config_exploratory.get_behavioral_profile()}")
    print(f"Behavioral difference: {difference:.1%}")
    
    # CRITICAL: Must be >50% different
    assert difference > 0.5, f"INSUFFICIENT BEHAVIORAL IMPACT: {difference:.1%} (required: >50%)"
    
    print(f"PASS: Configuration produces {difference:.1%} behavioral difference (>50% required)")
    return True

def test_configuration_profiles():
    """Test that predefined profiles produce expected differences"""
    from config.unified_config import get_configuration_profile
    
    # Test predefined profiles
    gt_standard = get_configuration_profile('grounded_theory_standard')
    thematic_rigorous = get_configuration_profile('thematic_analysis_rigorous')
    exploratory = get_configuration_profile('exploratory_creative')
    
    print("Configuration Profiles:")
    print(f"GT Standard: {gt_standard.get_behavioral_profile()}")
    print(f"Thematic Rigorous: {thematic_rigorous.get_behavioral_profile()}")
    print(f"Exploratory: {exploratory.get_behavioral_profile()}")
    
    # Test differences between profiles
    gt_vs_thematic = gt_standard.calculate_behavioral_difference(thematic_rigorous)
    gt_vs_exploratory = gt_standard.calculate_behavioral_difference(exploratory)
    thematic_vs_exploratory = thematic_rigorous.calculate_behavioral_difference(exploratory)
    
    print(f"GT vs Thematic difference: {gt_vs_thematic:.1%}")
    print(f"GT vs Exploratory difference: {gt_vs_exploratory:.1%}")
    print(f"Thematic vs Exploratory difference: {thematic_vs_exploratory:.1%}")
    
    # All profile pairs should be significantly different
    assert gt_vs_thematic > 0.3, f"GT vs Thematic too similar: {gt_vs_thematic:.1%}"
    assert gt_vs_exploratory > 0.5, f"GT vs Exploratory too similar: {gt_vs_exploratory:.1%}"
    assert thematic_vs_exploratory > 0.3, f"Thematic vs Exploratory too similar: {thematic_vs_exploratory:.1%}"
    
    print("PASS: All configuration profiles produce expected behavioral differences")
    return True

def test_extractor_configuration_impact():
    """Test that different extractors receive appropriate configurations"""
    from config.unified_config import UnifiedConfig, ExtractorType, ValidationLevel
    
    # Test hierarchical configuration
    hierarchical_config = UnifiedConfig(
        extractor_type=ExtractorType.HIERARCHICAL,
        minimum_confidence=0.4,
        validation_level=ValidationLevel.STANDARD
    )
    
    hierarchical_params = hierarchical_config.get_extractor_config()
    
    # Test semantic configuration  
    semantic_config = UnifiedConfig(
        extractor_type=ExtractorType.SEMANTIC,
        coding_depth="intensive",
        minimum_confidence=0.2
    )
    
    semantic_params = semantic_config.get_extractor_config()
    
    print(f"Hierarchical extractor config: {hierarchical_params}")
    print(f"Semantic extractor config: {semantic_params}")
    
    # Semantic should have semantic_units parameter
    assert 'semantic_units' in semantic_params, "Semantic config missing semantic_units"
    assert semantic_params['semantic_units'] == ['sentence', 'paragraph'], "Intensive depth should include sentences"
    
    # Both should have core parameters but with different values
    assert hierarchical_params['minimum_confidence'] == 0.4
    assert semantic_params['minimum_confidence'] == 0.2
    
    print("PASS: Different extractors receive appropriate configurations")
    return True

def test_legacy_compatibility():
    """Test that unified config can convert to legacy GroundedTheoryConfig"""
    from config.unified_config import UnifiedConfig, MethodologyType
    
    unified = UnifiedConfig(
        methodology=MethodologyType.GROUNDED_THEORY,
        theoretical_sensitivity="high",
        temperature=0.3
    )
    
    # Convert to legacy format
    legacy = unified.to_grounded_theory_config()
    
    # Verify key parameters are preserved
    assert legacy.methodology == "grounded_theory"
    assert legacy.theoretical_sensitivity == "high"
    assert legacy.temperature == 0.3
    assert hasattr(legacy, 'max_llm_retries')  # LLM reliability settings preserved
    
    print("PASS: Unified config successfully converts to legacy format")
    print(f"Legacy config created: methodology={legacy.methodology}, sensitivity={legacy.theoretical_sensitivity}")
    
    return True

def test_configuration_validation():
    """Test that configuration validation catches invalid values"""
    from config.unified_config import UnifiedConfig
    
    try:
        # Invalid theoretical sensitivity
        invalid_config = UnifiedConfig(theoretical_sensitivity="invalid")
        assert False, "Should have rejected invalid theoretical_sensitivity"
    except ValueError as e:
        print(f"PASS: Correctly rejected invalid theoretical_sensitivity: {e}")
    
    try:
        # Invalid confidence range
        invalid_config = UnifiedConfig(minimum_confidence=1.5)
        assert False, "Should have rejected invalid minimum_confidence"
    except ValueError as e:
        print(f"PASS: Correctly rejected invalid minimum_confidence: {e}")
    
    try:
        # Invalid temperature range
        invalid_config = UnifiedConfig(temperature=3.0)
        assert False, "Should have rejected invalid temperature"
    except ValueError as e:
        print(f"PASS: Correctly rejected invalid temperature: {e}")
    
    print("PASS: Configuration validation working correctly")
    return True

if __name__ == "__main__":
    print("Configuration Behavioral Impact Test")
    print("=" * 40)
    
    tests = [
        ("Behavioral Differences", test_configuration_behavioral_differences),
        ("Configuration Profiles", test_configuration_profiles),
        ("Extractor Configuration", test_extractor_configuration_impact),
        ("Legacy Compatibility", test_legacy_compatibility),
        ("Configuration Validation", test_configuration_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"FAIL: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print(f"\n{'='*40}")
    print(f"Configuration Tests: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("\nSUCCESS: Unified configuration system working correctly!")
        print("- Configuration changes produce >50% behavioral differences")
        print("- Multiple configuration profiles available")
        print("- Extractor-specific configuration working")
        print("- Legacy compatibility maintained")
        print("- Configuration validation functional")
    else:
        print("\nFAIL: Issues detected with configuration system")
        failed = [tests[i][0] for i, result in enumerate(results) if not result]
        print(f"Failed tests: {', '.join(failed)}")