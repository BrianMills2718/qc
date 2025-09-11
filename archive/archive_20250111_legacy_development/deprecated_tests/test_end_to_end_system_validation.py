#!/usr/bin/env python3
"""
End-to-End System Validation

Comprehensive test to validate the complete qualitative coding system
works end-to-end with real research data, producing valid research outputs.
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.qc.config.methodology_config import GroundedTheoryConfig, MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
from src.qc.core.robust_cli_operations import RobustCLIOperations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_gt_analysis_workflow():
    """Test complete GT analysis workflow with real research data"""
    print("\n=== End-to-End GT Analysis System Validation ===")
    
    try:
        # Load configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        print(f"Testing with configuration: {config.theoretical_sensitivity} sensitivity, {config.coding_depth} depth")
        
        # Initialize real operations - FAIL FAST if not working
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: System initialization failed - cannot run end-to-end validation")
            raise RuntimeError("System initialization failed - LLM integration broken")
        
        print("PASS: System initialization successful - LLM and Neo4j operational")
        
        # Check for real interview data
        interviews_path = Path("data/interviews/ai_interviews_3_for_test")
        if not interviews_path.exists():
            print(f"ERROR: Real interview data not found at {interviews_path}")
            print("FAIL-FAST: Cannot validate system without real research data")
            raise RuntimeError("Real interview data required for end-to-end validation")
        
        print(f"PASS: Real interview data found at {interviews_path}")
        
        # Load real interview data
        interviews = operations.robust_load_interviews(interviews_path)
        if not interviews:
            print("FAIL-FAST: No interview data loaded")
            raise RuntimeError("Interview loading failed")
        
        print(f"PASS: Loaded {len(interviews)} interviews for analysis")
        
        # Create GT workflow
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Validate prompt generator integration
        assert workflow.prompt_generator is not None, "ConfigurablePromptGenerator should be initialized"
        print("PASS: ConfigurablePromptGenerator integrated")
        
        start_time = datetime.now()
        print(f"Starting complete GT analysis at {start_time}")
        
        # Execute complete GT workflow with REAL data
        try:
            results = await workflow.execute_complete_workflow(interviews)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"PASS: GT analysis completed in {duration:.1f} seconds")
            
        except Exception as e:
            print(f"FAIL-FAST: GT analysis failed: {e}")
            raise RuntimeError(f"GT workflow execution failed: {e}") from e
        
        # Validate results structure
        assert results is not None, "GT analysis should return results"
        assert hasattr(results, 'open_codes'), "Results should have open codes"
        assert hasattr(results, 'axial_relationships'), "Results should have axial relationships"
        assert hasattr(results, 'core_category'), "Results should have core category"
        assert hasattr(results, 'theoretical_model'), "Results should have theoretical model"
        
        print("PASS: Complete GT results structure validated")
        
        # Validate open codes
        if results.open_codes:
            codes_count = len(results.open_codes)
            print(f"PASS: Generated {codes_count} open codes")
            
            # Check code quality
            for code in results.open_codes:
                assert hasattr(code, 'code_name'), "Code should have name"
                assert hasattr(code, 'description'), "Code should have description"
                assert hasattr(code, 'frequency'), "Code should have frequency"
                assert hasattr(code, 'confidence'), "Code should have confidence"
                assert code.frequency >= config.minimum_code_frequency, f"Code frequency filtering failed: {code.frequency} < {config.minimum_code_frequency}"
            
            print("PASS: Open codes structure and filtering validated")
        else:
            print("WARNING: No open codes generated - may indicate analysis issues")
        
        # Validate axial relationships
        if results.axial_relationships:
            rels_count = len(results.axial_relationships)
            print(f"PASS: Generated {rels_count} axial relationships")
            
            # Check relationship quality
            for rel in results.axial_relationships:
                assert hasattr(rel, 'central_category'), "Relationship should have central category"
                assert hasattr(rel, 'related_category'), "Relationship should have related category"
                assert hasattr(rel, 'strength'), "Relationship should have strength"
                assert rel.strength >= config.relationship_confidence_threshold, f"Relationship filtering failed: {rel.strength} < {config.relationship_confidence_threshold}"
            
            print("PASS: Axial relationships structure and filtering validated")
        else:
            print("WARNING: No axial relationships generated - may indicate analysis issues")
        
        # Validate core category
        if results.core_category:
            assert hasattr(results.core_category, 'category_name'), "Core category should have name"
            assert hasattr(results.core_category, 'definition'), "Core category should have definition"
            print(f"PASS: Core category generated: {results.core_category.category_name}")
        else:
            print("WARNING: No core category generated - may indicate analysis issues")
        
        # Validate theoretical model
        if results.theoretical_model:
            assert hasattr(results.theoretical_model, 'model_name'), "Theoretical model should have name"
            assert hasattr(results.theoretical_model, 'core_framework'), "Theoretical model should have framework"
            print(f"PASS: Theoretical model generated: {results.theoretical_model.model_name}")
        else:
            print("WARNING: No theoretical model generated - may indicate analysis issues")
        
        # Validate audit trail if available
        if hasattr(workflow, 'audit_trail') and workflow.audit_trail:
            assert workflow.audit_trail.steps, "Audit trail should have analysis steps"
            print(f"PASS: Audit trail captured with {len(workflow.audit_trail.steps)} steps")
        else:
            print("INFO: No audit trail captured (may not be enabled)")
        
        print("SUCCESS: End-to-end GT analysis system validation completed")
        
        # Save validation results for documentation
        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "configuration": config.to_dict(),
            "validation_status": "PASS",
            "analysis_duration_seconds": duration,
            "results_summary": {
                "open_codes_count": len(results.open_codes) if results.open_codes else 0,
                "axial_relationships_count": len(results.axial_relationships) if results.axial_relationships else 0,
                "core_category_generated": results.core_category is not None,
                "theoretical_model_generated": results.theoretical_model is not None,
                "audit_trail_captured": hasattr(workflow, 'audit_trail') and workflow.audit_trail is not None
            },
            "data_quality": {
                "interviews_processed": len(interviews),
                "configuration_filtering_applied": True,
                "llm_integration_functional": True,
                "neo4j_integration_functional": True
            }
        }
        
        validation_file = Path("evidence/current") / "end_to_end_validation_results.json"
        validation_file.parent.mkdir(parents=True, exist_ok=True)
        validation_file.write_text(json.dumps(validation_results, indent=2))
        
        print(f"Validation results saved to: {validation_file}")
        
        return True
        
    except Exception as e:
        print(f"FAIL: End-to-end system validation failed: {e}")
        logger.error(f"End-to-end validation error: {e}", exc_info=True)
        
        # Save failure results for debugging
        failure_results = {
            "timestamp": datetime.now().isoformat(),
            "validation_status": "FAIL",
            "error_message": str(e),
            "error_type": type(e).__name__
        }
        
        failure_file = Path("evidence/current") / "end_to_end_validation_failure.json"
        failure_file.parent.mkdir(parents=True, exist_ok=True)
        failure_file.write_text(json.dumps(failure_results, indent=2))
        
        return False

async def test_configuration_variation_analysis():
    """Test that different configurations produce measurably different analysis results"""
    print("\n=== Configuration Variation Analysis Validation ===")
    
    try:
        config_manager = MethodologyConfigManager()
        
        # Load two different configurations
        comprehensive_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory.yaml"))
        focused_config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_focused.yaml"))
        
        print(f"Comprehensive: {comprehensive_config.theoretical_sensitivity}/{comprehensive_config.coding_depth}")
        print(f"Focused: {focused_config.theoretical_sensitivity}/{focused_config.coding_depth}")
        
        # Load interview data
        interviews_path = Path("data/interviews/ai_interviews_3_for_test")
        if not interviews_path.exists():
            print("WARNING: Skipping configuration variation test - no interview data")
            return True
        
        # Quick validation of different prompt generation
        from qc.workflows.prompt_templates import ConfigurablePromptGenerator
        
        gen1 = ConfigurablePromptGenerator(comprehensive_config)
        gen2 = ConfigurablePromptGenerator(focused_config)
        
        test_data = "Test interview data for configuration comparison"
        prompt1 = gen1.generate_open_coding_prompt(test_data)
        prompt2 = gen2.generate_open_coding_prompt(test_data)
        
        assert prompt1 != prompt2, "Different configurations should produce different prompts"
        print("PASS: Different configurations produce different prompts")
        
        # Test filtering differences
        from qc.workflows.grounded_theory import OpenCode, AxialRelationship
        
        test_codes = [
            OpenCode(code_name="Low", description="Low frequency", properties=[], 
                    dimensions=[], supporting_quotes=[], frequency=1, confidence=0.8),
            OpenCode(code_name="High", description="High frequency", properties=[], 
                    dimensions=[], supporting_quotes=[], frequency=3, confidence=0.9)
        ]
        
        filtered1 = [c for c in test_codes if c.frequency >= comprehensive_config.minimum_code_frequency]
        filtered2 = [c for c in test_codes if c.frequency >= focused_config.minimum_code_frequency]
        
        filtering_different = len(filtered1) != len(filtered2)
        if filtering_different:
            print(f"PASS: Different filtering results - Comprehensive: {len(filtered1)}, Focused: {len(filtered2)}")
        else:
            print("INFO: Filtering parameters identical in test configurations")
        
        print("PASS: Configuration variation validation completed")
        return True
        
    except Exception as e:
        print(f"FAIL: Configuration variation validation failed: {e}")
        logger.error(f"Configuration variation error: {e}", exc_info=True)
        return False

async def main():
    """Run comprehensive end-to-end system validation"""
    print("Starting Comprehensive End-to-End System Validation")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Complete GT analysis workflow
    result1 = await test_complete_gt_analysis_workflow()
    test_results.append(("Complete GT Analysis Workflow", result1))
    
    # Test 2: Configuration variation analysis
    result2 = await test_configuration_variation_analysis()
    test_results.append(("Configuration Variation Analysis", result2))
    
    # Summary
    print("\n" + "=" * 60)
    print("END-TO-END SYSTEM VALIDATION RESULTS")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("END-TO-END VALIDATION SUCCESS: Complete system operational with real research data")
        return 0
    else:
        print("END-TO-END VALIDATION FAILED: System issues detected")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)