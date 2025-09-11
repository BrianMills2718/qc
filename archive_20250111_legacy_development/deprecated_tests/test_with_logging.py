#!/usr/bin/env python3
"""
Run GT workflow with enhanced logging to capture failures
"""
import asyncio
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'gt_debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

async def run_with_debug():
    """Run GT workflow with full debug output"""
    try:
        print("=== STARTING GT WORKFLOW WITH DEBUG LOGGING ===")
        
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        from src.qc.config.methodology_config import MethodologyConfigManager
        from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
        
        # Load configuration
        config_manager = MethodologyConfigManager()
        config = config_manager.load_config_from_path(
            Path("config/methodology_configs/grounded_theory_reliable.yaml")
        )
        
        # Initialize operations
        operations = RobustCLIOperations(config=config)
        init_success = await operations.initialize_systems()
        print(f"System initialization: {'SUCCESS' if init_success else 'FAILED'}")
        
        if not init_success:
            print("CRITICAL: System initialization failed")
            return False
        
        # Load interviews
        interviews = operations.robust_load_interviews(
            Path("data/interviews/ai_interviews_3_for_test")
        )
        print(f"Loaded {len(interviews)} interviews")
        
        # Create workflow
        workflow = GroundedTheoryWorkflow(operations, config=config)
        
        # Run each phase with explicit error handling
        print("\n=== PHASE 1: OPEN CODING ===")
        try:
            open_codes = await workflow._open_coding_phase(interviews)
            print(f"Open coding result: {len(open_codes) if open_codes else 0} codes")
            if open_codes:
                for i, code in enumerate(open_codes[:3]):
                    print(f"  Sample code {i+1}: {code.code_name}")
        except Exception as e:
            print(f"OPEN CODING FAILED: {e}")
            traceback.print_exc()
            return False
        
        print("\n=== PHASE 2: AXIAL CODING ===")
        try:
            axial_relationships = await workflow._axial_coding_phase(open_codes, interviews)
            print(f"Axial coding result: {len(axial_relationships) if axial_relationships else 0} relationships")
            if axial_relationships:
                for i, rel in enumerate(axial_relationships[:3]):
                    print(f"  Sample relationship {i+1}: {rel.central_category} -> {rel.related_category}")
        except Exception as e:
            print(f"AXIAL CODING FAILED: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {str(e)}")
            traceback.print_exc()
            
            # Try to get more info about the error
            if hasattr(e, '__dict__'):
                print(f"Error attributes: {e.__dict__}")
            
            # Log the input that caused the failure
            print(f"Input open_codes type: {type(open_codes)}")
            print(f"Input open_codes length: {len(open_codes) if open_codes else 'None'}")
            if open_codes and len(open_codes) > 0:
                print(f"First code attributes: {open_codes[0].__dict__ if hasattr(open_codes[0], '__dict__') else 'No __dict__'}")
            
            return False
        
        print("\n=== PHASE 3: SELECTIVE CODING ===")
        try:
            core_category = await workflow._selective_coding_phase(
                open_codes, axial_relationships, interviews
            )
            print(f"Selective coding result: {core_category.category_name if core_category else 'No core category'}")
        except Exception as e:
            print(f"SELECTIVE CODING FAILED: {e}")
            traceback.print_exc()
            return False
        
        print("\n=== PHASE 4: THEORETICAL MODEL ===")
        try:
            theoretical_model = await workflow._theory_integration_phase(
                open_codes, axial_relationships, core_category, interviews
            )
            print(f"Theoretical model result: {theoretical_model.model_name if theoretical_model else 'No model'}")
        except Exception as e:
            print(f"THEORETICAL MODEL FAILED: {e}")
            traceback.print_exc()
            return False
        
        print("\n=== WORKFLOW COMPLETED SUCCESSFULLY ===")
        return True
        
    except Exception as e:
        print(f"\n=== UNEXPECTED ERROR ===")
        print(f"Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_with_debug())
    print(f"\nFinal result: {'SUCCESS' if success else 'FAILURE'}")
    sys.exit(0 if success else 1)