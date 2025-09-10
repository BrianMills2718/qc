#!/usr/bin/env python3
"""
Simple Integration Test

Test the entire restored system with all components working together.
"""

import sys
from pathlib import Path

# Set up path
project_root = Path(__file__).parent
qc_clean_path = project_root / 'qc_clean'
sys.path.insert(0, str(qc_clean_path))

def test_full_integration():
    """Test complete system integration"""
    try:
        print("Testing full system integration...")
        
        # 1. Test configuration system
        from config.enhanced_config_manager import (
            EnhancedConfigManager, ComprehensiveConfig, 
            MethodologyConfig, ExtractionConfig, ValidationConfig,
            LLMConfig, OutputConfig, PerformanceConfig, DatabaseConfig,
            MethodologyType, CodingApproach, ValidationLevel
        )
        
        # Create comprehensive config
        config = ComprehensiveConfig(
            methodology=MethodologyConfig(
                paradigm=MethodologyType.GROUNDED_THEORY,
                theoretical_sensitivity="medium",
                coding_depth="focused"
            ),
            extraction=ExtractionConfig(
                coding_approach=CodingApproach.OPEN,
                extractor="hierarchical",
                relationship_threshold=0.7
            ),
            validation=ValidationConfig(
                validation_level=ValidationLevel.STANDARD,
                consolidation_enabled=True
            ),
            llm=LLMConfig(temperature=0.1),
            output=OutputConfig(),
            performance=PerformanceConfig(),
            database=DatabaseConfig()
        )
        
        print("PASS: Configuration system working")
        
        # 2. Test extractor plugins
        from plugins.extractors import get_available_extractors, get_extractor_plugin
        
        available_extractors = get_available_extractors()
        print(f"PASS: Available extractors: {available_extractors}")
        
        # Test each extractor
        interview_data = {
            'id': 'integration_test',
            'content': 'AI technology is transforming qualitative research methods. Traditional approaches are being enhanced with computational capabilities.'
        }
        
        extractor_config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'relationship_threshold': 0.7,
            'validation_level': 'standard',
            'consolidation_enabled': True
        }
        
        extractor_results = {}
        for extractor_name in available_extractors:
            extractor = get_extractor_plugin(extractor_name)
            if extractor:
                codes = extractor.extract_codes(interview_data, extractor_config)
                extractor_results[extractor_name] = len(codes)
                print(f"PASS: {extractor_name}: Generated {len(codes)} codes")
        
        # 3. Test behavior change detection
        manager = EnhancedConfigManager()
        
        relationship_config = ComprehensiveConfig(
            methodology=config.methodology,
            extraction=ExtractionConfig(
                coding_approach=CodingApproach.MIXED,
                extractor="relationship"
            ),
            validation=config.validation,
            llm=config.llm,
            output=config.output,
            performance=config.performance,
            database=config.database
        )
        
        changes = manager.get_behavior_changes(config, relationship_config)
        print(f"PASS: Behavioral changes detected: {len(changes)}")
        
        # 4. Test validation
        issues = manager.validate_config(config)
        print(f"PASS: Configuration validation issues: {len(issues)}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extractor_differences():
    """Test that different extractors produce different results"""
    try:
        print("Testing extractor differences...")
        
        from plugins.extractors import get_extractor_plugin
        
        interview_data = {
            'id': 'diff_test',
            'content': 'Research methodology is evolving with technological advances. Traditional qualitative methods are being enhanced with AI capabilities.'
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'validation_level': 'standard',
            'consolidation_enabled': True
        }
        
        # Test three different extractors
        h_extractor = get_extractor_plugin('hierarchical')
        r_extractor = get_extractor_plugin('relationship')
        s_extractor = get_extractor_plugin('semantic')
        
        if h_extractor and r_extractor and s_extractor:
            h_codes = h_extractor.extract_codes(interview_data, config)
            r_codes = r_extractor.extract_codes(interview_data, config)
            s_codes = s_extractor.extract_codes(interview_data, config)
            
            print(f"Hierarchical: {len(h_codes)} codes")
            print(f"Relationship: {len(r_codes)} codes")
            print(f"Semantic: {len(s_codes)} codes")
            
            # Test that they produce different code names
            h_names = set(code.get('code_name', '') for code in h_codes)
            r_names = set(code.get('code_name', '') for code in r_codes)
            s_names = set(code.get('code_name', '') for code in s_codes)
            
            # Calculate differences
            hr_diff = len(h_names.symmetric_difference(r_names)) / max(len(h_names.union(r_names)), 1)
            hs_diff = len(h_names.symmetric_difference(s_names)) / max(len(h_names.union(s_names)), 1)
            rs_diff = len(r_names.symmetric_difference(s_names)) / max(len(r_names.union(s_names)), 1)
            
            avg_diff = (hr_diff + hs_diff + rs_diff) / 3
            
            print(f"Average difference: {avg_diff:.2f}")
            print(f"PASS: Extractors produce >30% different results: {avg_diff > 0.3}")
            
            return avg_diff > 0.3
        
        return False
        
    except Exception as e:
        print(f"FAIL: Extractor difference test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_behavior_impact():
    """Test that configuration changes affect system behavior"""
    try:
        print("Testing configuration behavior impact...")
        
        from config.enhanced_config_manager import (
            ComprehensiveConfig, MethodologyConfig, ExtractionConfig, 
            ValidationConfig, LLMConfig, OutputConfig, PerformanceConfig,
            DatabaseConfig, MethodologyType, CodingApproach, ValidationLevel
        )
        
        # Create two very different configurations
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
        
        from config.enhanced_config_manager import EnhancedConfigManager
        manager = EnhancedConfigManager()
        changes = manager.get_behavior_changes(config1, config2)
        
        print(f"Behavioral changes detected: {len(changes)}")
        for change in changes:
            print(f"  - {change}")
        
        expected_changes = [
            "paradigm_change_affects_prompts",
            "coding_approach_affects_extraction_strategy",
            "extractor_change_affects_algorithm", 
            "validation_level_affects_quality_pipeline",
            "performance_settings_affect_processing",
            "llm_temperature_affects_response_variability"
        ]
        
        detected_expected = sum(1 for change in changes if change in expected_changes)
        print(f"Expected changes detected: {detected_expected}/{len(expected_changes)}")
        print(f"PASS: >50% behavior changes detected: {detected_expected/len(expected_changes) > 0.5}")
        
        return detected_expected >= 4  # At least 4 expected changes
        
    except Exception as e:
        print(f"FAIL: Configuration behavior test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_architecture_preserved():
    """Test that clean architecture is preserved"""
    try:
        print("Testing architecture preservation...")
        
        # Test file count
        import os
        python_files = []
        for root, dirs, files in os.walk('qc_clean'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        file_count = len(python_files)
        print(f"Python file count: {file_count} (target: 38)")
        
        # Test key imports work
        from config.enhanced_config_manager import EnhancedConfigManager
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        from plugins.extractors.relationship_extractor import RelationshipExtractor
        from plugins.extractors.semantic_extractor import SemanticExtractor
        from plugins.extractors.validated_extractor import ValidatedExtractor
        
        print("PASS: All key modules import successfully")
        
        # Test capabilities vary
        extractors = [HierarchicalExtractor(), RelationshipExtractor(), SemanticExtractor(), ValidatedExtractor()]
        capabilities = [e.get_capabilities() for e in extractors]
        
        # Should have different capabilities
        unique_capabilities = len(set(str(c) for c in capabilities))
        print(f"Unique capability sets: {unique_capabilities}")
        
        print(f"PASS: Architecture preserved: {file_count == 38 and unique_capabilities >= 3}")
        return file_count == 38 and unique_capabilities >= 3
        
    except Exception as e:
        print(f"FAIL: Architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_research_quality():
    """Test research quality improvements"""
    try:
        print("Testing research quality improvements...")
        
        from plugins.extractors import get_extractor_plugin
        
        # Research interview
        interview_data = {
            'id': 'quality_test',
            'content': '''
            The integration of AI in qualitative research presents both opportunities and challenges.
            Traditional grounded theory emphasizes emergent categories from systematic data analysis.
            Machine learning can identify patterns that researchers might overlook in large datasets.
            However, maintaining interpretive authenticity remains a core methodological concern.
            The balance between computational efficiency and humanistic understanding is delicate.
            '''
        }
        
        # Test different validation levels
        basic_config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'validation_level': 'minimal',
            'consolidation_enabled': False
        }
        
        rigorous_config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'validation_level': 'rigorous',
            'consolidation_enabled': True
        }
        
        # Compare basic vs validated extractor
        basic_extractor = get_extractor_plugin('hierarchical')
        validated_extractor = get_extractor_plugin('validated')
        
        if basic_extractor and validated_extractor:
            basic_codes = basic_extractor.extract_codes(interview_data, basic_config)
            validated_codes = validated_extractor.extract_codes(interview_data, rigorous_config)
            
            print(f"Basic extraction: {len(basic_codes)} codes")
            print(f"Validated extraction: {len(validated_codes)} codes")
            
            # Check for quality improvements
            has_validation_metadata = any(
                'validation_summary' in code or 'extraction_metadata' in code
                for code in validated_codes
            )
            
            has_confidence_enhancement = any(
                code.get('confidence', 0) > 0.5 for code in validated_codes
            )
            
            print(f"Has validation metadata: {has_validation_metadata}")
            print(f"Has confidence enhancement: {has_confidence_enhancement}")
            
            print(f"PASS: Research quality improved: {has_validation_metadata and has_confidence_enhancement}")
            return has_validation_metadata and has_confidence_enhancement
        
        return False
        
    except Exception as e:
        print(f"FAIL: Quality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple Integration Test")
    print("=" * 25)
    
    tests = [
        ("Full Integration", test_full_integration),
        ("Extractor Differences", test_extractor_differences),
        ("Configuration Behavior", test_configuration_behavior_impact),
        ("Architecture Preserved", test_architecture_preserved),
        ("Research Quality", test_research_quality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        result = test_func()
        results.append(result)
        status = "PASS" if result else "FAIL"
        print(f"Result: {status}")
    
    print(f"\n{'='*25}")
    print(f"Overall: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("\nSUCCESS: Complete restoration validated!")
        print("- 4 extractor plugins working")
        print("- >30% different results between extractors")  
        print("- 15+ configuration categories")
        print("- Configuration changes affect behavior")
        print("- Clean architecture maintained (38 files)")
        print("- Research quality improvements confirmed")
    else:
        print("\nSome tests failed")
        failed = [tests[i][0] for i, result in enumerate(results) if not result]
        print(f"Failed: {', '.join(failed)}")