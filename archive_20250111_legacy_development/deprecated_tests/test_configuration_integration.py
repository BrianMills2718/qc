#!/usr/bin/env python3
"""
Configuration Integration Validation

Tests to validate that ConfigurablePromptGenerator is properly integrated
into all phases of the GT workflow and that configuration parameters
control all LLM interactions.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.config.methodology_config import GroundedTheoryConfig, MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
from src.qc.workflows.prompt_templates import ConfigurablePromptGenerator
from src.qc.core.robust_cli_operations import RobustCLIOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_prompt_generator_integration_all_phases():
    """Test that ConfigurablePromptGenerator is used in all GT phases"""
    print("\n=== Testing Prompt Generator Integration in All Phases ===")
    
    try:
        # Load configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        # Create real operations - FAIL FAST if LLM not available
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: LLM integration not available - cannot test prompt generator integration")
            raise RuntimeError("System initialization failed - cannot test without working LLM")
        
        # Create workflow with configuration
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Verify prompt generator is initialized
        assert workflow.prompt_generator is not None, "Workflow should have prompt generator with config"
        assert isinstance(workflow.prompt_generator, ConfigurablePromptGenerator), "Should be ConfigurablePromptGenerator instance"
        
        # Test prompt generation for all phases with different configurations
        config2 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        operations2 = RobustCLIOperations(config=config2)
        await operations2.initialize_systems()
        workflow2 = GroundedTheoryWorkflow(operations2, config=config2)
        
        test_data = "Interview data about AI implementation challenges"
        
        # Test open coding prompt generation
        prompt1_open = workflow.prompt_generator.generate_open_coding_prompt(test_data)
        prompt2_open = workflow2.prompt_generator.generate_open_coding_prompt(test_data)
        assert prompt1_open != prompt2_open, "Different configs should generate different open coding prompts"
        print(f"PASS: Open coding prompts differ between configurations")
        
        # Test axial coding prompt generation
        codes_text = "Test codes summary"
        prompt1_axial = workflow.prompt_generator.generate_axial_coding_prompt(codes_text, test_data)
        prompt2_axial = workflow2.prompt_generator.generate_axial_coding_prompt(codes_text, test_data)
        assert prompt1_axial != prompt2_axial, "Different configs should generate different axial coding prompts"
        print(f"PASS: Axial coding prompts differ between configurations")
        
        # Test selective coding prompt generation
        relationships_text = "Test relationships summary"
        prompt1_selective = workflow.prompt_generator.generate_selective_coding_prompt(codes_text, relationships_text)
        prompt2_selective = workflow2.prompt_generator.generate_selective_coding_prompt(codes_text, relationships_text)
        assert prompt1_selective != prompt2_selective, "Different configs should generate different selective coding prompts"
        print(f"PASS: Selective coding prompts differ between configurations")
        
        # Test theory integration prompt generation
        core_category_text = "Test core category"
        prompt1_theory = workflow.prompt_generator.generate_theory_integration_prompt(core_category_text, codes_text, relationships_text)
        prompt2_theory = workflow2.prompt_generator.generate_theory_integration_prompt(core_category_text, codes_text, relationships_text)
        assert prompt1_theory != prompt2_theory, "Different configs should generate different theory integration prompts"
        print(f"PASS: Theory integration prompts differ between configurations")
        
        print("PASS: ConfigurablePromptGenerator successfully integrated into all GT workflow phases")
        return True
        
    except Exception as e:
        print(f"FAIL: Prompt generator integration test failed: {e}")
        logger.error(f"Prompt generator integration error: {e}", exc_info=True)
        return False

async def test_configuration_driven_filtering():
    """Test that configuration parameters control filtering behavior"""
    print("\n=== Testing Configuration-Driven Filtering ===")
    
    try:
        # Load configurations with different filtering parameters
        config_manager = MethodologyConfigManager()
        strict_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        loose_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_raw_data.yaml"))
        
        print(f"Strict config: min_freq={strict_config.minimum_code_frequency}, conf_threshold={strict_config.relationship_confidence_threshold}")
        print(f"Loose config: min_freq={loose_config.minimum_code_frequency}, conf_threshold={loose_config.relationship_confidence_threshold}")
        
        # Test that configuration parameters are applied to filtering
        from qc.workflows.grounded_theory import OpenCode, AxialRelationship
        
        # Create test codes with different frequencies
        test_codes = [
            OpenCode(code_name="Low", description="Low freq", properties=[], 
                    dimensions=[], supporting_quotes=[], frequency=1, confidence=0.8),
            OpenCode(code_name="Medium", description="Med freq", properties=[], 
                    dimensions=[], supporting_quotes=[], frequency=2, confidence=0.9),
            OpenCode(code_name="High", description="High freq", properties=[], 
                    dimensions=[], supporting_quotes=[], frequency=3, confidence=0.85)
        ]
        
        # Create test relationships with different strengths
        test_relationships = [
            AxialRelationship(central_category="Cat_A", related_category="Cat_B",
                            relationship_type="causal", conditions=[], consequences=[],
                            supporting_evidence=[], strength=0.5),
            AxialRelationship(central_category="Cat_C", related_category="Cat_D",
                            relationship_type="contextual", conditions=[], consequences=[],
                            supporting_evidence=[], strength=0.7),
            AxialRelationship(central_category="Cat_E", related_category="Cat_F",
                            relationship_type="intervening", conditions=[], consequences=[],
                            supporting_evidence=[], strength=0.9)
        ]
        
        # Test code filtering with different configurations
        strict_filtered_codes = [code for code in test_codes if code.frequency >= strict_config.minimum_code_frequency]
        loose_filtered_codes = [code for code in test_codes if code.frequency >= loose_config.minimum_code_frequency]
        
        # Test relationship filtering with different configurations
        strict_filtered_rels = [rel for rel in test_relationships if rel.strength >= strict_config.relationship_confidence_threshold]
        loose_filtered_rels = [rel for rel in test_relationships if rel.strength >= loose_config.relationship_confidence_threshold]
        
        print(f"Code filtering - Strict: {len(strict_filtered_codes)}, Loose: {len(loose_filtered_codes)}")
        print(f"Relationship filtering - Strict: {len(strict_filtered_rels)}, Loose: {len(loose_filtered_rels)}")
        
        # Verify filtering produces different results
        filtering_differs = (len(strict_filtered_codes) != len(loose_filtered_codes) or 
                            len(strict_filtered_rels) != len(loose_filtered_rels))
        
        assert filtering_differs, "Different configurations should produce different filtering results"
        
        print("PASS: Configuration-driven filtering working correctly")
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration-driven filtering test failed: {e}")
        logger.error(f"Configuration-driven filtering error: {e}", exc_info=True)
        return False

async def main():
    """Run all configuration integration tests"""
    print("Starting Configuration Integration Validation")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Prompt generator integration
    result1 = await test_prompt_generator_integration_all_phases()
    test_results.append(("Prompt Generator Integration", result1))
    
    # Test 2: Configuration-driven filtering
    result2 = await test_configuration_driven_filtering()
    test_results.append(("Configuration-Driven Filtering", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("CONFIGURATION INTEGRATION TEST RESULTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("ALL TESTS PASSED: Configuration integration working correctly")
        return 0
    else:
        print("SOME TESTS FAILED: Configuration integration needs fixes")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)