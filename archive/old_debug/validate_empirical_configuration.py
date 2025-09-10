#!/usr/bin/env python3
"""
Empirical Configuration Validation Script
Tests realistic configuration parameters against actual GT workflow execution
"""

import asyncio
import json
import traceback
from pathlib import Path
from datetime import datetime

async def test_realistic_configuration():
    """Test new empirically-validated configuration"""
    
    print("=== Empirical Configuration Validation ===")
    
    try:
        # Load realistic configuration
        from src.qc.config.methodology_config import MethodologyConfigManager
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(Path("config/methodology_configs/grounded_theory_realistic.yaml"))
        
        print(f"Testing configuration:")
        print(f"  minimum_code_frequency: {config.minimum_code_frequency}")
        print(f"  relationship_confidence_threshold: {config.relationship_confidence_threshold}")
        print(f"  temperature: {config.temperature}")
        print(f"  max_tokens: {config.max_tokens}")
        
        # Initialize system
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        
        if not init_success:
            print("FAIL-FAST: System initialization failed")
            return False
        
        # Load interview data
        interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
        print(f"Loaded {len(interviews)} interviews")
        
        # Test open coding phase with realistic parameters
        from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        start_time = datetime.now()
        try:
            print("\nTesting open coding phase...")
            open_codes = await workflow._open_coding_phase(interviews)
            duration = (datetime.now() - start_time).total_seconds()
            
            print(f"RESULT: Generated {len(open_codes) if open_codes else 0} codes in {duration:.1f}s")
            
            if open_codes and len(open_codes) > 0:
                print("SUCCESS: Open coding generated viable results")
                for i, code in enumerate(open_codes[:3]):  # Show first 3
                    print(f"  Code {i+1}: {code.code_name} (freq={code.frequency}, conf={code.confidence:.2f})")
                
                # Test axial coding with these results
                print("\nTesting axial coding phase...")
                axial_start = datetime.now()
                try:
                    relationships = await workflow._axial_coding_phase(open_codes, interviews)
                    axial_duration = (datetime.now() - axial_start).total_seconds()
                    
                    print(f"RESULT: Generated {len(relationships) if relationships else 0} relationships in {axial_duration:.1f}s")
                    
                    if relationships and len(relationships) > 0:
                        print("SUCCESS: Axial coding also works")
                        for i, rel in enumerate(relationships[:2]):  # Show first 2
                            print(f"  Rel {i+1}: {rel.central_category} → {rel.related_category} (strength={rel.strength:.2f})")
                    else:
                        print("INFO: Axial coding generated 0 relationships (may be normal for some data)")
                    
                except Exception as e:
                    print(f"WARNING: Axial coding failed: {e}")
                
                return True
            else:
                print("FAIL: Open coding still generates zero codes")
                return False
                
        except Exception as e:
            print(f"FAIL: Open coding phase failed: {e}")
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"FAIL: Configuration validation failed: {e}")
        traceback.print_exc()
        return False

async def comparison_test():
    """Compare old vs new configuration performance"""
    
    print("\n=== Configuration Comparison Test ===")
    
    configs_to_test = [
        ("Original (Failing)", "grounded_theory_focused.yaml"),
        ("Realistic (Fixed)", "grounded_theory_realistic.yaml")
    ]
    
    for config_name, config_file in configs_to_test:
        print(f"\n--- Testing {config_name} ---")
        
        try:
            from src.qc.config.methodology_config import MethodologyConfigManager
            config_manager = MethodologyConfigManager()
            config = config_manager.load_config_from_path(Path(f"config/methodology_configs/{config_file}"))
            
            print(f"Config: max_tokens={config.max_tokens}, min_freq={config.minimum_code_frequency}")
            
            from src.qc.core.robust_cli_operations import RobustCLIOperations
            operations = RobustCLIOperations(config=config)
            await operations.initialize_systems()
            
            interviews = operations.robust_load_interviews(Path("data/interviews/ai_interviews_3_for_test"))
            
            from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
            workflow = GroundedTheoryWorkflow(operations, config=config)
            
            # Test just the critical first step
            start_time = datetime.now()
            try:
                open_codes = await workflow._open_coding_phase(interviews)
                duration = (datetime.now() - start_time).total_seconds()
                
                result_summary = f"Generated {len(open_codes) if open_codes else 0} codes in {duration:.1f}s"
                if open_codes and len(open_codes) > 0:
                    print(f"  ✓ SUCCESS: {result_summary}")
                else:
                    print(f"  ✗ FAILED: {result_summary}")
                
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
        
        except Exception as e:
            print(f"  ✗ CONFIG ERROR: {e}")

async def run_validation():
    """Run the complete validation suite"""
    print("Starting Empirical Configuration Validation")
    print("=" * 50)
    
    success = await test_realistic_configuration()
    await comparison_test()
    
    print("\n" + "=" * 50)
    print(f"Validation Result: {'SUCCESS' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(run_validation())
    exit(0 if success else 1)