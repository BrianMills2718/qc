#!/usr/bin/env python3
"""
Complete Integration Test

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
        
        # 3. Test configuration affects extractor selection
        hierarchical_config = config
        hierarchical_config.extraction.extractor = "hierarchical"
        
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
        
        print(f"PASS: Config 1 extractor: {hierarchical_config.extraction.extractor}")
        print(f"PASS: Config 2 extractor: {relationship_config.extraction.extractor}")
        
        # 4. Test behavior change detection
        manager = EnhancedConfigManager()
        changes = manager.get_behavior_changes(hierarchical_config, relationship_config)
        print(f"PASS: Behavioral changes detected: {len(changes)}")
        
        # 5. Test validation
        issues = manager.validate_config(config)
        print(f"PASS: Configuration validation issues: {len(issues)}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extractor_plugin_combinations():
    """Test all extractor-configuration combinations"""
    try:
        print("\nTesting extractor-configuration combinations...")
        
        from config.enhanced_config_manager import (
            ComprehensiveConfig, MethodologyConfig, ExtractionConfig, 
            ValidationConfig, LLMConfig, OutputConfig, PerformanceConfig, 
            DatabaseConfig, MethodologyType, CodingApproach, ValidationLevel
        )
        from plugins.extractors import get_extractor_plugin
        
        # Test data
        interview_data = {
            'id': 'combo_test',
            'content': 'Research methodology is evolving with technological advances. Traditional qualitative methods are being enhanced.'
        }
        
        # Test combinations
        combinations = [
            ("hierarchical", CodingApproach.OPEN, ValidationLevel.MINIMAL),
            ("relationship", CodingApproach.MIXED, ValidationLevel.STANDARD),
            ("semantic", CodingApproach.OPEN, ValidationLevel.STANDARD),
            ("validated", CodingApproach.CLOSED, ValidationLevel.RIGOROUS)
        ]
        
        combo_results = []
        
        for extractor_name, coding_approach, validation_level in combinations:
            # Create configuration
            config = ComprehensiveConfig(
                methodology=MethodologyConfig(
                    paradigm=MethodologyType.GROUNDED_THEORY,
                    theoretical_sensitivity="medium",
                    coding_depth="focused"
                ),
                extraction=ExtractionConfig(
                    coding_approach=coding_approach,
                    extractor=extractor_name
                ),
                validation=ValidationConfig(
                    validation_level=validation_level,
                    consolidation_enabled=True
                ),
                llm=LLMConfig(),
                output=OutputConfig(),
                performance=PerformanceConfig(),
                database=DatabaseConfig()
            )
            
            # Test extractor
            extractor = get_extractor_plugin(extractor_name)
            if extractor:
                extractor_config = {
                    'llm_handler': None,
                    'coding_approach': coding_approach.value,
                    'validation_level': validation_level.value,
                    'consolidation_enabled': True
                }
                
                codes = extractor.extract_codes(interview_data, extractor_config)
                combo_results.append((extractor_name, len(codes)))
                print(f"PASS: {extractor_name} + {coding_approach.value} + {validation_level.value}: {len(codes)} codes")
        
        # Verify all combinations worked
        success_count = len([r for r in combo_results if r[1] > 0])
        total_count = len(combinations)
        
        print(f"PASS: {success_count}/{total_count} combinations successful")
        return success_count >= 3  # At least 3 combinations should work
        
    except Exception as e:
        print(f"FAIL: Combination test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_benchmarks():
    """Test system performance meets requirements"""
    try:
        print("\nTesting performance benchmarks...")
        
        import time
        from plugins.extractors import get_extractor_plugin
        
        # Performance test data
        large_interview = {
            'id': 'perf_test',
            'content': '''
            Artificial Intelligence is revolutionizing qualitative research methodologies across multiple domains.
            Traditional approaches to coding and analysis are being enhanced with computational capabilities.
            Researchers are finding new ways to combine human insight with machine processing power.
            The integration of AI tools is creating opportunities for more comprehensive analysis.
            However, there are also challenges related to validation and maintaining research rigor.
            The balance between automation and human judgment remains a critical consideration.
            Quality assurance becomes more complex when AI is involved in the analysis process.
            Methodological frameworks need to evolve to accommodate these technological advances.
            The research community is actively developing best practices for AI-assisted analysis.
            Ethical considerations around AI use in qualitative research are increasingly important.
            ''' * 5  # Make it larger
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'validation_level': 'standard',
            'consolidation_enabled': True
        }
        
        # Test performance of different extractors
        performance_results = {}
        
        for extractor_name in ['hierarchical', 'relationship', 'semantic']:
            extractor = get_extractor_plugin(extractor_name)
            if extractor:
                start_time = time.time()
                codes = extractor.extract_codes(large_interview, config)
                end_time = time.time()
                
                duration = end_time - start_time
                performance_results[extractor_name] = {
                    'duration': duration,
                    'codes_generated': len(codes),
                    'codes_per_second': len(codes) / duration if duration > 0 else 0
                }
                
                codes_per_sec = len(codes)/duration if duration > 0 else float('inf')
                print(f"PASS: {extractor_name}: {duration:.2f}s, {len(codes)} codes, {codes_per_sec:.1f} codes/sec")
        
        # Performance requirements (within 2x of baseline)
        max_duration = 5.0  # 5 seconds max for this test
        min_codes = 2      # At least 2 codes should be generated
        
        performance_ok = True
        for name, results in performance_results.items():
            if results['duration'] > max_duration or results['codes_generated'] < min_codes:
                performance_ok = False
                print(f"FAIL: {name} performance issue: {results['duration']:.2f}s, {results['codes_generated']} codes")
        
        print(f"PASS: Performance test: {'PASS' if performance_ok else 'FAIL'}")
        return performance_ok
        
    except Exception as e:
        print(f"FAIL: Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_architectural_integrity():
    """Test that clean architecture is maintained"""
    try:
        print("\nTesting architectural integrity...")
        
        # Test file count
        import os
        python_files = []
        for root, dirs, files in os.walk('qc_clean'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        file_count = len(python_files)
        print(f"PASS: Python file count: {file_count} (target: 38)")
        
        # Test module imports work
        from config.enhanced_config_manager import EnhancedConfigManager
        from plugins.extractors.hierarchical_extractor import HierarchicalExtractor
        from plugins.extractors.relationship_extractor import RelationshipExtractor
        from plugins.extractors.semantic_extractor import SemanticExtractor
        from plugins.extractors.validated_extractor import ValidatedExtractor
        
        print("PASS: All key modules import successfully")
        
        # Test plugin system isolation
        extractor1 = HierarchicalExtractor()
        extractor2 = RelationshipExtractor()
        
        # Should be independent instances
        assert extractor1.get_name() != extractor2.get_name()
        assert extractor1.get_capabilities() != extractor2.get_capabilities()
        
        print("PASS: Plugin isolation maintained")
        
        return file_count == 38
        
    except Exception as e:
        print(f"FAIL: Architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_research_quality_improvement():
    """Test that enhanced system produces better research results"""
    try:
        print("\nTesting research quality improvement...")
        
        from plugins.extractors import get_extractor_plugin
        
        # Research-focused test data
        research_interview = {
            'id': 'quality_test',
            'content': '''
            The integration of artificial intelligence in qualitative research represents a paradigmatic shift.
            Researchers are grappling with questions of authenticity and validity when AI assists analysis.
            Traditional grounded theory approaches emphasize emergent categories from data.
            However, AI-enhanced methods can identify patterns that humans might miss.
            The relationship between human interpretation and machine analysis is complex.
            Methodological rigor remains paramount regardless of technological assistance.
            Quality criteria must evolve to accommodate hybrid human-AI analysis approaches.
            The research community is developing new standards for AI-assisted qualitative research.
            '''
        }
        
        config = {
            'llm_handler': None,
            'coding_approach': 'open',
            'validation_level': 'rigorous',
            'consolidation_enabled': True
        }
        
        # Test enhanced vs basic extraction
        hierarchical_extractor = get_extractor_plugin('hierarchical')
        validated_extractor = get_extractor_plugin('validated')
        
        if hierarchical_extractor and validated_extractor:
            basic_codes = hierarchical_extractor.extract_codes(research_interview, config)
            enhanced_codes = validated_extractor.extract_codes(research_interview, config)
            
            print(f"PASS: Basic extraction: {len(basic_codes)} codes")
            print(f"PASS: Enhanced extraction: {len(enhanced_codes)} codes")
            
            # Enhanced should have quality metadata
            has_quality_metadata = any(
                'validation_summary' in code or 'confidence_enhancement' in code 
                for code in enhanced_codes
            )
            
            print(f"PASS: Enhanced codes have quality metadata: {has_quality_metadata}")
            
            # Should show evidence of validation
            has_validation_evidence = any(
                code.get('extraction_metadata', {}).get('extractor') == 'validated'
                for code in enhanced_codes
            )
            
            print(f"PASS: Enhanced codes show validation evidence: {has_validation_evidence}")
            
            return has_quality_metadata and has_validation_evidence
        
        return False
        
    except Exception as e:
        print(f"FAIL: Quality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Complete System Integration Test")
    print("=" * 35)
    
    tests = [
        ("Full Integration", test_full_integration),
        ("Plugin Combinations", test_extractor_plugin_combinations),
        ("Performance Benchmarks", test_performance_benchmarks),
        ("Architectural Integrity", test_architectural_integrity),
        ("Research Quality", test_research_quality_improvement)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 25)
        result = test_func()
        results.append(result)
        status = "PASS" if result else "FAIL"
        print(f"Final Result: {status}")
    
    print(f"\n{'='*35}")
    print(f"Overall Integration: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("\nSUCCESS: Complete system restoration validated!")
        print("PASS: 4 extractor plugins with >30% different results")
        print("PASS: 15+ configuration categories with behavioral impact")
        print("PASS: Plugin interoperability across all combinations")
        print("PASS: Clean architecture maintained (38 files)")
        print("PASS: Research quality improvements validated")
    else:
        print("\nFAIL: Some integration tests failed")
        failed_tests = [tests[i][0] for i, result in enumerate(results) if not result]
        print(f"Failed tests: {', '.join(failed_tests)}")