#!/usr/bin/env python3
"""
Simple Configuration Test

Test basic configuration functionality.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_enhanced_config_loading():
    """Test that enhanced configuration can be loaded"""
    try:
        from config.enhanced_config_manager import EnhancedConfigManager
        
        # Test creating a config manager
        manager = EnhancedConfigManager("config/qc_comprehensive.yaml")
        config = manager.load_config()
        
        print(f"Paradigm: {config.methodology.paradigm}")
        print(f"Coding approach: {config.extraction.coding_approach}")
        print(f"Extractor: {config.extraction.extractor}")
        print(f"Validation level: {config.validation.validation_level}")
        
        return True
        
    except Exception as e:
        print(f"Enhanced config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_behavior_change_detection():
    """Test behavior change detection"""
    try:
        from config.enhanced_config_manager import (
            EnhancedConfigManager, ComprehensiveConfig, 
            MethodologyConfig, ExtractionConfig, ValidationConfig,
            LLMConfig, OutputConfig, PerformanceConfig, DatabaseConfig,
            MethodologyType, CodingApproach, ValidationLevel
        )
        
        # Create two different configurations
        config1 = ComprehensiveConfig(
            methodology=MethodologyConfig(
                paradigm=MethodologyType.GROUNDED_THEORY,
                theoretical_sensitivity="low",
                coding_depth="surface"
            ),
            extraction=ExtractionConfig(
                coding_approach=CodingApproach.OPEN,
                extractor="hierarchical"
            ),
            validation=ValidationConfig(
                validation_level=ValidationLevel.MINIMAL
            ),
            llm=LLMConfig(temperature=0.9),
            output=OutputConfig(),
            performance=PerformanceConfig(parallel_processing=False),
            database=DatabaseConfig()
        )
        
        config2 = ComprehensiveConfig(
            methodology=MethodologyConfig(
                paradigm=MethodologyType.CRITICAL_THEORY,
                theoretical_sensitivity="high",
                coding_depth="intensive"
            ),
            extraction=ExtractionConfig(
                coding_approach=CodingApproach.CLOSED,
                extractor="validated"
            ),
            validation=ValidationConfig(
                validation_level=ValidationLevel.RIGOROUS
            ),
            llm=LLMConfig(temperature=0.1),
            output=OutputConfig(),
            performance=PerformanceConfig(parallel_processing=True),
            database=DatabaseConfig()
        )
        
        # Test behavior change detection
        manager = EnhancedConfigManager()
        changes = manager.get_behavior_changes(config1, config2)
        
        print(f"Behavior changes detected: {len(changes)}")
        for change in changes:
            print(f"  - {change}")
        
        return len(changes) >= 4  # At least 4 behavioral changes
        
    except Exception as e:
        print(f"Behavior change test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple Configuration Test")
    print("=" * 25)
    
    tests = [
        ("Config Loading", test_enhanced_config_loading),
        ("Behavior Changes", test_behavior_change_detection)
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
        print("Configuration system working!")
    else:
        print("Some tests failed")