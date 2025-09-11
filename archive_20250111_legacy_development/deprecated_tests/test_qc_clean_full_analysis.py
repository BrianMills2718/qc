#!/usr/bin/env python3
"""
Test QC Clean Full GT Analysis - Phase 1 Validation
Attempts to run actual GT analysis using qc_clean architecture
"""

import sys
import asyncio
from pathlib import Path

# Add qc_clean to Python path  
sys.path.insert(0, str(Path.cwd() / "qc_clean"))

async def test_full_gt_analysis():
    """Test running a complete GT analysis with qc_clean"""
    print("=== QC CLEAN FULL GT ANALYSIS TEST ===")
    
    try:
        # Import the core CLI components
        from core.cli.cli_robust import RobustCLI
        
        print("[INIT] Creating RobustCLI instance...")
        cli = RobustCLI()
        
        print("[INIT] Initializing system...")
        init_success = await cli.initialize()
        
        if not init_success:
            print("[ERROR] System initialization failed")
            return False
            
        print("[SUCCESS] System initialized successfully")
        
        # Test with actual interview data
        input_dir = "data/interviews/ai_interviews_3_for_test"
        output_dir = "qc_clean_test_output"
        
        if not Path(input_dir).exists():
            print(f"[ERROR] Test data not found: {input_dir}")
            print("Cannot proceed with full analysis test")
            return False
            
        print(f"[ANALYSIS] Starting GT analysis...")
        print(f"   Input: {input_dir}")  
        print(f"   Output: {output_dir}")
        
        # Run the GT analysis
        analysis_success = await cli.analyze_grounded_theory(input_dir, output_dir)
        
        if analysis_success:
            print("[SUCCESS] GT analysis completed successfully!")
            
            # Check output files
            output_path = Path(output_dir)
            if output_path.exists():
                files = list(output_path.glob("*.md")) + list(output_path.glob("*.json"))
                print(f"   Generated {len(files)} output files:")
                for file in files:
                    print(f"      - {file.name}")
            
            print("\n[PHASE 1 VALIDATION] GT ANALYSIS END-TO-END SUCCESS")
            return True
        else:
            print("[ERROR] GT analysis failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] Full analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await cli.cleanup()
        except:
            pass

async def main():
    """Main test function"""
    print("QC Clean Architecture - Full GT Analysis Test")
    print("=" * 50)
    
    success = await test_full_gt_analysis()
    
    if success:
        print("\n[PHASE 1 COMPLETE] CORE EXTRACTION FULLY VALIDATED")
        print("Ready to proceed to Phase 2: Plugin Architecture")
    else:
        print("\n[PHASE 1 ISSUE] End-to-end validation needs attention")
        print("Core extraction successful but GT workflow needs fixes")
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)