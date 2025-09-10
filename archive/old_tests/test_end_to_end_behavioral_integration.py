#!/usr/bin/env python3
"""
End-to-End Behavioral Integration Validation

Tests to validate that the complete configuration-driven GT analysis system 
produces measurably different results when run with different configurations
on real interview data. NO MOCKS - uses real LLM calls only.
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.config.methodology_config import GroundedTheoryConfig, MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
from src.qc.core.robust_cli_operations import RobustCLIOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_end_to_end_configuration_behavior():
    """
    Run complete GT analysis with different configurations and compare results.
    This is the ultimate test of configuration-driven behavioral differences.
    Uses REAL LLM calls only - NO MOCKS.
    """
    print("\n=== End-to-End Configuration Behavior Validation ===")
    
    try:
        config_manager = MethodologyConfigManager()
        
        # Load two very different configurations
        comprehensive_config = config_manager.load_config_from_path(
            Path("config/methodology_configs/grounded_theory.yaml")
        )
        minimal_config = config_manager.load_config_from_path(
            Path("config/methodology_configs/grounded_theory_raw_data.yaml")
        )
        
        print(f"Comprehensive Config: {comprehensive_config.theoretical_sensitivity} sensitivity, {comprehensive_config.coding_depth} depth")
        print(f"                     freq>={comprehensive_config.minimum_code_frequency}, conf>={comprehensive_config.relationship_confidence_threshold}")
        print(f"                     temp={comprehensive_config.temperature}, tokens={comprehensive_config.max_tokens}")
        
        print(f"Minimal Config:      {minimal_config.theoretical_sensitivity} sensitivity, {minimal_config.coding_depth} depth")
        print(f"                     freq>={minimal_config.minimum_code_frequency}, conf>={minimal_config.relationship_confidence_threshold}")
        print(f"                     temp={minimal_config.temperature}, tokens={minimal_config.max_tokens}")
        
        # Check for real interview data (REQUIRED - no fallbacks to mocks)
        interviews_path = Path("data/interviews/ai_interviews_3_for_test")
        if not interviews_path.exists():
            print(f"ERROR: Test data not found at {interviews_path}")
            print("FAIL-FAST: Cannot proceed without real interview data")
            return False
        
        print(f"Using real interview data from {interviews_path}")
        
        # Create operations instances with different configurations
        comprehensive_operations = RobustCLIOperations(config=comprehensive_config)
        minimal_operations = RobustCLIOperations(config=minimal_config)
        
        # Initialize both systems (REQUIRED - fail fast if not working)
        comp_init_success = await comprehensive_operations.initialize_systems()
        min_init_success = await minimal_operations.initialize_systems()
        
        if not comp_init_success or not min_init_success:
            print("FAIL-FAST: System initialization failed - LLM integration broken")
            raise RuntimeError("System initialization failed - cannot proceed without working LLM")
        
        # Create workflows with different configurations
        comprehensive_workflow = GroundedTheoryWorkflow(comprehensive_operations, config=comprehensive_config)
        minimal_workflow = GroundedTheoryWorkflow(minimal_operations, config=minimal_config)
        
        print(f"\nRunning GT analysis with COMPREHENSIVE configuration...")
        
        # Load real interview data
        interviews = comprehensive_operations.robust_load_interviews(interviews_path)
        if not interviews:
            print("FAIL-FAST: No interview data loaded")
            return False
        
        # Run analysis with comprehensive configuration (REAL LLM CALLS ONLY)
        try:
            comprehensive_results = await comprehensive_workflow.execute_complete_workflow(interviews)
            print(f"Comprehensive analysis completed: {len(comprehensive_results.open_codes) if comprehensive_results.open_codes else 0} codes")
        except Exception as e:
            print(f"FAIL-FAST: Comprehensive analysis failed with real data: {e}")
            raise RuntimeError(f"GT analysis failed: {e}") from e
        
        print(f"Running GT analysis with MINIMAL configuration...")
        
        # Run analysis with minimal configuration (REAL LLM CALLS ONLY) 
        try:
            minimal_results = await minimal_workflow.execute_complete_workflow(interviews)
            print(f"Minimal analysis completed: {len(minimal_results.open_codes) if minimal_results.open_codes else 0} codes")
        except Exception as e:
            print(f"FAIL-FAST: Minimal analysis failed with real data: {e}")
            raise RuntimeError(f"GT analysis failed: {e}") from e
        
        # Compare results to prove behavioral differences
        evidence = collect_behavioral_evidence(comprehensive_results, minimal_results, 
                                               comprehensive_config, minimal_config)
        
        print("\n" + "=" * 60)
        print("BEHAVIORAL EVIDENCE COLLECTED")
        print("=" * 60)
        
        for key, value in evidence.items():
            print(f"{key}: {value}")
        
        # Validate that configurations caused measurably different behavior
        behavior_different = validate_behavioral_differences(evidence)
        
        if behavior_different:
            print("\nSUCCESS: Different configurations caused measurably different analysis behavior")
            
            # Save evidence to file for documentation
            evidence_file = Path("evidence") / "behavioral_integration_evidence.json"
            evidence_file.parent.mkdir(exist_ok=True)
            
            evidence_with_timestamp = {
                "timestamp": datetime.now().isoformat(),
                "configurations_tested": {
                    "comprehensive": comprehensive_config.to_dict(),
                    "minimal": minimal_config.to_dict()
                },
                "behavioral_evidence": evidence,
                "conclusion": "Different configurations cause measurably different GT analysis behavior"
            }
            
            evidence_file.write_text(json.dumps(evidence_with_timestamp, indent=2))
            print(f"Evidence saved to: {evidence_file}")
            
            return True
        else:
            print("\nFAILED: Configurations did not produce sufficiently different behavior")
            return False
            
    except Exception as e:
        print(f"FAIL: End-to-end behavioral integration test failed: {e}")
        logger.error(f"End-to-end behavioral integration error: {e}", exc_info=True)
        return False

def collect_behavioral_evidence(comp_results, min_results, comp_config, min_config):
    """Collect evidence of behavioral differences between configurations"""
    
    evidence = {}
    
    # Configuration differences
    evidence["config_theoretical_sensitivity_different"] = comp_config.theoretical_sensitivity != min_config.theoretical_sensitivity
    evidence["config_coding_depth_different"] = comp_config.coding_depth != min_config.coding_depth
    evidence["config_min_frequency_different"] = comp_config.minimum_code_frequency != min_config.minimum_code_frequency
    evidence["config_confidence_threshold_different"] = comp_config.relationship_confidence_threshold != min_config.relationship_confidence_threshold
    
    # Results differences (REAL results from REAL LLM calls)
    if hasattr(comp_results, 'open_codes') and hasattr(min_results, 'open_codes'):
        evidence["open_codes_count_comprehensive"] = len(comp_results.open_codes) if comp_results.open_codes else 0
        evidence["open_codes_count_minimal"] = len(min_results.open_codes) if min_results.open_codes else 0
        evidence["open_codes_count_different"] = evidence["open_codes_count_comprehensive"] != evidence["open_codes_count_minimal"]
    
    if hasattr(comp_results, 'axial_relationships') and hasattr(min_results, 'axial_relationships'):
        evidence["relationships_count_comprehensive"] = len(comp_results.axial_relationships) if comp_results.axial_relationships else 0
        evidence["relationships_count_minimal"] = len(min_results.axial_relationships) if min_results.axial_relationships else 0
        evidence["relationships_count_different"] = evidence["relationships_count_comprehensive"] != evidence["relationships_count_minimal"]
    
    if hasattr(comp_results, 'core_category') and hasattr(min_results, 'core_category'):
        evidence["core_category_comprehensive"] = comp_results.core_category.category_name if comp_results.core_category else "None"
        evidence["core_category_minimal"] = min_results.core_category.category_name if min_results.core_category else "None"
        evidence["core_category_different"] = evidence["core_category_comprehensive"] != evidence["core_category_minimal"]
    
    # Configuration parameter evidence
    evidence["comprehensive_config_summary"] = f"{comp_config.theoretical_sensitivity}/{comp_config.coding_depth}/freq>={comp_config.minimum_code_frequency}/conf>={comp_config.relationship_confidence_threshold}"
    evidence["minimal_config_summary"] = f"{min_config.theoretical_sensitivity}/{min_config.coding_depth}/freq>={min_config.minimum_code_frequency}/conf>={min_config.relationship_confidence_threshold}"
    
    return evidence

def validate_behavioral_differences(evidence):
    """Validate that the evidence shows meaningful behavioral differences"""
    
    # Check configuration differences
    config_differences = [
        evidence.get("config_theoretical_sensitivity_different", False),
        evidence.get("config_coding_depth_different", False), 
        evidence.get("config_min_frequency_different", False),
        evidence.get("config_confidence_threshold_different", False)
    ]
    
    # Check result differences
    result_differences = [
        evidence.get("open_codes_count_different", False),
        evidence.get("relationships_count_different", False),
        evidence.get("core_category_different", False)
    ]
    
    # Configurations must be different
    has_config_differences = any(config_differences)
    
    # Results should be different if configurations are different
    has_result_differences = any(result_differences)
    
    # Both configuration and results should show differences
    behavioral_causation_demonstrated = has_config_differences and has_result_differences
    
    # Additional validation: comprehensive should produce MORE than minimal
    comp_codes = evidence.get("open_codes_count_comprehensive", 0)
    min_codes = evidence.get("open_codes_count_minimal", 0)
    
    # Logic check: comprehensive configs should produce more codes
    logic_correct = comp_codes >= min_codes
    
    print(f"Configuration differences: {has_config_differences}")
    print(f"Result differences: {has_result_differences}")
    print(f"Logic check (comprehensive >= minimal): {logic_correct} ({comp_codes} >= {min_codes})")
    
    return behavioral_causation_demonstrated and logic_correct

async def test_configuration_behavior_without_llm():
    """Test configuration behavior when LLM is not available"""
    print("\nTesting configuration behavior without LLM (fallback validation)...")
    
    config_manager = MethodologyConfigManager()
    
    # Load different configurations
    config1 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
    config2 = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_raw_data.yaml"))
    
    # Test prompt generation differences (if prompt templates exist)
    try:
        from qc.workflows.prompt_templates import ConfigurablePromptGenerator
        
        gen1 = ConfigurablePromptGenerator(config1)
        gen2 = ConfigurablePromptGenerator(config2)
        
        test_data = "Test interview data"
        prompt1 = gen1.generate_open_coding_prompt(test_data)
        prompt2 = gen2.generate_open_coding_prompt(test_data)
        
        prompt_different = prompt1 != prompt2
        print(f"Prompt generation different: {prompt_different}")
    except ImportError:
        print("ConfigurablePromptGenerator not available")
        prompt_different = False
    
    # Test filtering differences
    from qc.workflows.grounded_theory import OpenCode
    test_codes = [
        OpenCode(code_name="Low", description="Low frequency code", properties=[], dimensions=[], 
                supporting_quotes=[], frequency=1, confidence=0.8),
        OpenCode(code_name="Med", description="Medium frequency code", properties=[], dimensions=[], 
                supporting_quotes=[], frequency=2, confidence=0.9)
    ]
    
    filtered1 = [c for c in test_codes if c.frequency >= config1.minimum_code_frequency]
    filtered2 = [c for c in test_codes if c.frequency >= config2.minimum_code_frequency]
    
    filtering_different = len(filtered1) != len(filtered2)
    
    print(f"Filtering behavior different: {filtering_different}")
    print(f"Config 1 would filter to: {len(filtered1)} codes")
    print(f"Config 2 would filter to: {len(filtered2)} codes")
    
    behavior_different = prompt_different or filtering_different
    
    if behavior_different:
        print("SUCCESS: Configuration behavior differences demonstrated without LLM")
        return True
    else:
        print("FAILED: Configuration behavior differences not demonstrated")
        return False

async def main():
    """Run end-to-end behavioral integration validation"""
    print("Starting End-to-End Behavioral Integration Validation")
    print("=" * 60)
    
    # Run the comprehensive end-to-end test
    success = await test_end_to_end_configuration_behavior()
    
    print("\n" + "=" * 60)
    if success:
        print("END-TO-END VALIDATION SUCCESS: Configuration-driven behavioral differences proven")
        return 0
    else:
        print("END-TO-END VALIDATION FAILED: Configuration behavioral integration incomplete")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)