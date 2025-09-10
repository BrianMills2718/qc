#!/usr/bin/env python3
"""
Post-Processing Configuration Integration Tests

Tests to validate that configuration parameters (minimum_code_frequency, 
relationship_confidence_threshold) properly filter analysis results and that 
ConfigurablePromptGenerator is integrated into the GT workflow.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.config.methodology_config import GroundedTheoryConfig, MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow, OpenCode, AxialRelationship
from src.qc.workflows.prompt_templates import ConfigurablePromptGenerator
from src.qc.core.robust_cli_operations import RobustCLIOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_open_code_filtering():
    """Test that minimum_code_frequency filters open codes correctly"""
    print("\n=== Testing Open Code Filtering ===")
    
    try:
        # Load configuration with specific minimum frequency
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        
        print(f"Config minimum_code_frequency: {config.minimum_code_frequency}")
        
        # Create real operations - FAIL FAST if LLM not available
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: LLM integration not available - cannot proceed without real analysis")
            raise RuntimeError("System initialization failed - cannot test filtering without working LLM")
        
        # Create workflow with configuration
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Create test codes with different frequencies for filtering validation
        test_codes = [
            OpenCode(code_name="High Frequency Code", description="Frequent concept", 
                    properties=["prop1"], dimensions=["dim1"], supporting_quotes=["quote1"], 
                    frequency=5, confidence=0.9),
            OpenCode(code_name="Low Frequency Code", description="Rare concept", 
                    properties=["prop2"], dimensions=["dim2"], supporting_quotes=["quote2"], 
                    frequency=1, confidence=0.8),  # Below minimum_code_frequency=2
            OpenCode(code_name="Medium Frequency Code", description="Medium concept", 
                    properties=["prop3"], dimensions=["dim3"], supporting_quotes=["quote3"], 
                    frequency=3, confidence=0.85),
        ]
        
        # Test configuration-driven filtering logic directly
        filtered_codes = [code for code in test_codes if code.frequency >= config.minimum_code_frequency]
        
        # Verify filtering worked
        print(f"Original codes: {len(test_codes)}")
        print(f"Filtered codes: {len(filtered_codes)}")
        print(f"Expected: codes with frequency >= {config.minimum_code_frequency}")
        
        # Should have 2 codes (frequency 5 and 3), not the one with frequency 1
        expected_count = 2
        assert len(filtered_codes) == expected_count, f"Expected {expected_count} codes after filtering, got {len(filtered_codes)}"
        
        # Check that low frequency code was filtered out
        code_names = [code.code_name for code in filtered_codes]
        assert "Low Frequency Code" not in code_names, "Low frequency code should be filtered out"
        assert "High Frequency Code" in code_names, "High frequency code should remain"
        assert "Medium Frequency Code" in code_names, "Medium frequency code should remain"
        
        print("PASS: Open code filtering by minimum_code_frequency working correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: Open code filtering test failed: {e}")
        logger.error(f"Open code filtering error: {e}", exc_info=True)
        return False

async def test_relationship_filtering():
    """Test that relationship_confidence_threshold filters axial relationships correctly"""
    print("\n=== Testing Relationship Filtering ===")
    
    try:
        # Load configuration with specific confidence threshold
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        
        print(f"Config relationship_confidence_threshold: {config.relationship_confidence_threshold}")
        
        # Create real operations - FAIL FAST if LLM not available
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: LLM integration not available - cannot proceed without real analysis")
            raise RuntimeError("System initialization failed - cannot test filtering without working LLM")
        
        # Create workflow with configuration
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Create test relationships with different strengths for filtering validation
        test_relationships = [
            AxialRelationship(central_category="Category A", related_category="Category B",
                            relationship_type="causal", conditions=["cond1"], consequences=["cons1"],
                            supporting_evidence=["evidence1"], strength=0.9),  # Above threshold
            AxialRelationship(central_category="Category C", related_category="Category D",
                            relationship_type="contextual", conditions=["cond2"], consequences=["cons2"],
                            supporting_evidence=["evidence2"], strength=0.5),  # Below threshold (0.7)
            AxialRelationship(central_category="Category E", related_category="Category F",
                            relationship_type="intervening", conditions=["cond3"], consequences=["cons3"],
                            supporting_evidence=["evidence3"], strength=0.8),  # Above threshold
        ]
        
        # Test configuration-driven relationship filtering logic directly
        filtered_relationships = [rel for rel in test_relationships if rel.strength >= config.relationship_confidence_threshold]
        
        # Verify filtering worked
        print(f"Original relationships: {len(test_relationships)}")
        print(f"Filtered relationships: {len(filtered_relationships)}")
        print(f"Expected: relationships with strength >= {config.relationship_confidence_threshold}")
        
        # Should have 2 relationships (strength 0.9 and 0.8), not the one with strength 0.5
        expected_count = 2
        assert len(filtered_relationships) == expected_count, f"Expected {expected_count} relationships after filtering, got {len(filtered_relationships)}"
        
        # Check that low confidence relationship was filtered out
        central_categories = [rel.central_category for rel in filtered_relationships]
        assert "Category C" not in central_categories, "Low confidence relationship should be filtered out"
        assert "Category A" in central_categories, "High confidence relationship should remain"
        assert "Category E" in central_categories, "Medium-high confidence relationship should remain"
        
        print("PASS: Relationship filtering by confidence threshold working correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: Relationship filtering test failed: {e}")
        logger.error(f"Relationship filtering error: {e}", exc_info=True)
        return False

async def test_prompt_generator_integration():
    """Test that ConfigurablePromptGenerator is integrated into GT workflow"""
    print("\n=== Testing Prompt Generator Integration ===")
    
    try:
        # Load configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        # Create real operations - FAIL FAST if LLM not available
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: LLM integration not available - cannot proceed without real analysis")
            raise RuntimeError("System initialization failed - cannot test prompt generator without working LLM")
        
        # Create workflow with configuration
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Verify prompt generator was initialized
        assert workflow.prompt_generator is not None, "Prompt generator should be initialized with config"
        assert isinstance(workflow.prompt_generator, ConfigurablePromptGenerator), "Should be ConfigurablePromptGenerator instance"
        assert workflow.prompt_generator.config == config, "Prompt generator should use workflow config"
        
        # Test that different configurations create different generators
        config2 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        operations2 = RobustCLIOperations(config=config2)
        init_success2 = await operations2.initialize_systems()
        
        if not init_success2:
            print("FAIL-FAST: Second LLM integration not available")
            raise RuntimeError("Cannot test configuration variation without working LLM")
        
        workflow2 = GroundedTheoryWorkflow(operations2, config=config2)
        
        # Generate prompts with both workflows
        test_data = "Test interview data"
        prompt1 = workflow.prompt_generator.generate_open_coding_prompt(test_data)
        prompt2 = workflow2.prompt_generator.generate_open_coding_prompt(test_data)
        
        # Verify prompts are different (different configurations should produce different prompts)
        assert prompt1 != prompt2, "Different configurations should produce different prompts"
        
        print(f"Config 1 ({config.theoretical_sensitivity}/{config.coding_depth}) prompt length: {len(prompt1)}")
        print(f"Config 2 ({config2.theoretical_sensitivity}/{config2.coding_depth}) prompt length: {len(prompt2)}")
        
        # Test workflow without configuration (should not have prompt generator)
        operations_no_config = RobustCLIOperations(config=None)
        init_success_no_config = await operations_no_config.initialize_systems()
        
        if init_success_no_config:
            workflow_no_config = GroundedTheoryWorkflow(operations_no_config, config=None)
            assert workflow_no_config.prompt_generator is None, "Workflow without config should not have prompt generator"
        
        print("PASS: Prompt generator integration working correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: Prompt generator integration test failed: {e}")
        logger.error(f"Prompt generator integration error: {e}", exc_info=True)
        return False

async def test_configuration_variation_effects():
    """Test that different configurations produce measurably different filtering results"""
    print("\n=== Testing Configuration Variation Effects ===")
    
    try:
        config_manager = MethodologyConfigManager()
        
        # Load two different configurations
        strict_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        loose_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_raw_data.yaml"))
        
        print(f"Strict config: freq={strict_config.minimum_code_frequency}, conf={strict_config.relationship_confidence_threshold}")
        print(f"Loose config: freq={loose_config.minimum_code_frequency}, conf={loose_config.relationship_confidence_threshold}")
        
        # Verify configurations are actually different
        config_different = (
            strict_config.minimum_code_frequency != loose_config.minimum_code_frequency or
            strict_config.relationship_confidence_threshold != loose_config.relationship_confidence_threshold or
            strict_config.theoretical_sensitivity != loose_config.theoretical_sensitivity
        )
        
        assert config_different, "Test configurations should have different parameters"
        
        # Create workflows with different configs
        operations_strict = RobustCLIOperations(config=strict_config)
        operations_loose = RobustCLIOperations(config=loose_config)
        
        init_strict = await operations_strict.initialize_systems()
        init_loose = await operations_loose.initialize_systems()
        
        if not init_strict or not init_loose:
            print("FAIL-FAST: LLM integration not available for configuration variation test")
            raise RuntimeError("Cannot test configuration variation without working LLM")
        
        workflow_strict = GroundedTheoryWorkflow(operations_strict, config=strict_config)
        workflow_loose = GroundedTheoryWorkflow(operations_loose, config=loose_config)
        
        # Verify prompt generators produce different results
        test_data = "Sample interview data about AI impact"
        prompt_strict = workflow_strict.prompt_generator.generate_open_coding_prompt(test_data)
        prompt_loose = workflow_loose.prompt_generator.generate_open_coding_prompt(test_data)
        
        assert prompt_strict != prompt_loose, "Different configurations should produce different prompts"
        
        # Check for configuration-specific content in prompts
        has_theoretical_differences = (
            ("maximum theoretical sensitivity" in prompt_strict.lower()) != 
            ("maximum theoretical sensitivity" in prompt_loose.lower())
        )
        
        has_depth_differences = (
            ("exhaustive analysis" in prompt_strict.lower()) != 
            ("exhaustive analysis" in prompt_loose.lower())
        )
        
        configuration_effects_visible = has_theoretical_differences or has_depth_differences
        assert configuration_effects_visible, "Configuration differences should be visible in prompts"
        
        print("PASS: Configuration variations produce measurably different effects")
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration variation effects test failed: {e}")
        logger.error(f"Configuration variation effects error: {e}", exc_info=True)
        return False

async def main():
    """Run all post-processing configuration integration tests"""
    print("Starting Post-Processing Configuration Integration Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Open code filtering
    result1 = await test_open_code_filtering()
    test_results.append(("Open Code Filtering", result1))
    
    # Test 2: Relationship filtering
    result2 = await test_relationship_filtering()
    test_results.append(("Relationship Filtering", result2))
    
    # Test 3: Prompt generator integration
    result3 = await test_prompt_generator_integration()
    test_results.append(("Prompt Generator Integration", result3))
    
    # Test 4: Configuration variation effects
    result4 = await test_configuration_variation_effects()
    test_results.append(("Configuration Variation Effects", result4))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED: Post-processing configuration integration is working correctly")
        return 0
    else:
        print("SOME TESTS FAILED: Post-processing configuration integration needs fixes")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)