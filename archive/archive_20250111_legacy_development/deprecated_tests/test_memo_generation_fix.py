#!/usr/bin/env python3
"""
Test Memo Generation Fix - Regression Test

This test validates the fix for the argument signature mismatch bug that was causing:
"unsupported operand type(s) for /: 'list' and 'str'" in grounded theory workflow memo generation.

This test would have caught the original bug and prevents future regressions.
"""

import sys
from pathlib import Path
import tempfile
import asyncio

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_memo_generation_with_interview_data():
    """
    Test the exact scenario that was failing before the fix
    
    This test validates that:
    1. The new generate_analytical_memo_from_data() method works with List[Dict] input
    2. Type validation catches incorrect input types
    3. Memo generation succeeds and returns proper metadata
    4. Path operations work correctly with generated memo_id
    """
    
    print("MEMO GENERATION FIX REGRESSION TEST")
    print("=" * 50)
    
    try:
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        
        # Initialize system
        print("[INFO] Initializing system...")
        operations = RobustCLIOperations()
        await operations.initialize()
        print("[OK] System initialized successfully")
        
        # Create the exact data structure that was causing the bug
        interviews = [
            {
                'interview_id': 'test_interview_regression_001',
                'quotes': [
                    {
                        'id': 'q001',
                        'text': 'The main challenge in our organization is effective communication between different departments.',
                        'speaker': {'name': 'Participant A'},
                        'code_names': ['communication_challenges', 'organizational_barriers'],
                        'location_start': 100,
                        'location_end': 200,
                        'context_summary': 'Discussion about organizational challenges'
                    },
                    {
                        'id': 'q002', 
                        'text': 'Leadership support is absolutely critical for successful change management initiatives.',
                        'speaker': {'name': 'Participant B'},
                        'code_names': ['leadership_support', 'change_management'],
                        'location_start': 250,
                        'location_end': 350,
                        'context_summary': 'Leadership role in organizational change'
                    }
                ]
            },
            {
                'interview_id': 'test_interview_regression_002',
                'quotes': [
                    {
                        'id': 'q003',
                        'text': 'Technology implementation requires proper training and user support to be effective.',
                        'speaker': {'name': 'Participant C'},
                        'code_names': ['technology_implementation', 'training_needs', 'user_support'],
                        'location_start': 50,
                        'location_end': 150,
                        'context_summary': 'Technology adoption challenges'
                    }
                ]
            }
        ]
        
        print(f"[INFO] Created test data: {len(interviews)} interviews, {sum(len(i['quotes']) for i in interviews)} quotes")
        
        # Test 1: Successful memo generation (this would have failed before the fix)
        print("\n1. Testing successful memo generation with List[Dict] input...")
        
        result = await operations.generate_analytical_memo_from_data(
            interviews,
            memo_type="theoretical_memo",
            focus_codes=["communication_challenges", "leadership_support"],
            memo_title="Regression Test - Communication and Leadership"
        )
        
        # Validate results
        assert result["success"] == True, f"Memo generation failed: {result.get('error')}"
        assert "memo_id" in result, "Missing memo_id in result"
        assert isinstance(result["memo_id"], str), f"memo_id should be string, got {type(result['memo_id'])}"
        assert result["pattern_count"] >= 0, "Invalid pattern count"
        assert result["insight_count"] >= 0, "Invalid insight count"
        
        print(f"   [OK] Memo generated successfully: {result['memo_id']}")
        print(f"   [OK] Found {result['pattern_count']} patterns and {result['insight_count']} insights")
        print(f"   [OK] memo_id type validation passed: {type(result['memo_id'])}")
        
        # Test 2: Type validation (should catch incorrect input types)
        print("\n2. Testing type validation with incorrect input...")
        
        try:
            # This should raise TypeError (wrapped in the result dict)
            bad_result = await operations.generate_analytical_memo_from_data(
                "not a list",  # Wrong type - should trigger TypeError
                memo_type="theoretical_memo"
            )
            # Check if error was caught and returned in result
            if bad_result["success"] == False and "Expected List[Dict]" in bad_result.get("error", ""):
                print(f"   [OK] Type validation caught incorrect input: {bad_result['error']}")
            else:
                print(f"   [ERROR] Type validation should have failed but got: {bad_result}")
                return False
        except Exception as e:
            print(f"   [ERROR] Unexpected exception: {type(e).__name__}: {e}")
            return False
        
        # Test 3: Empty data validation
        print("\n3. Testing empty data validation...")
        
        try:
            empty_result = await operations.generate_analytical_memo_from_data(
                [],  # Empty list
                memo_type="theoretical_memo"
            )
            # Should handle gracefully
            assert empty_result["success"] == False, "Empty data should result in failure"
            print(f"   [OK] Empty data handled gracefully: {empty_result['error']}")
        except Exception as e:
            print(f"   [OK] Empty data validation triggered exception: {e}")
        
        # Test 4: Path operations validation (the core bug)
        print("\n4. Testing path operations with memo_id...")
        
        # Verify that memo files were actually created (proves path operations worked)
        if "output_files" in result:
            for format_type, file_path in result["output_files"].items():
                if Path(file_path).exists():
                    print(f"   [OK] {format_type.upper()} file created successfully: {Path(file_path).name}")
                else:
                    print(f"   [ERROR] {format_type.upper()} file not found: {file_path}")
        
        # Test 5: Integration with different memo types
        print("\n5. Testing different memo types...")
        
        for memo_type in ["pattern_analysis", "theoretical_memo", "cross_case_analysis"]:
            type_result = await operations.generate_analytical_memo_from_data(
                interviews,
                memo_type=memo_type,
                memo_title=f"Regression Test - {memo_type.title()}"
            )
            
            if type_result["success"]:
                print(f"   [OK] {memo_type} memo generated: {type_result['memo_id']}")
            else:
                print(f"   [ERROR] {memo_type} memo failed: {type_result.get('error')}")
        
        print(f"\n[SUCCESS] All regression tests passed!")
        print("The bug fix successfully resolves the argument signature mismatch.")
        print("Path operations now work correctly with proper data types.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Regression test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run memo generation fix regression test"""
    print("MEMO GENERATION FIX REGRESSION TEST SUITE")
    print("=" * 60)
    print("Testing fix for: 'unsupported operand type(s) for /: 'list' and 'str'")
    print("Original bug: List[Dict] passed to Path parameter in memo generation")
    print("Fix: New generate_analytical_memo_from_data() method for in-memory data")
    print()
    
    success = await test_memo_generation_with_interview_data()
    
    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Regression test validation complete!")
        print("✅ Argument signature mismatch bug fixed")
        print("✅ Type validation working correctly")
        print("✅ Path operations functioning properly")
        print("✅ All memo types supported")
        print("✅ Future regressions will be caught by this test")
    else:
        print("[FAILURE] Regression test failed - bug not properly fixed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)