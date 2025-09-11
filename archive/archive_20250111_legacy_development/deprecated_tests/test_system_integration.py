#!/usr/bin/env python3
"""
Test system integration points without LLM calls
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_robust_cli_integration():
    """Test robust CLI operations without LLM"""
    print("TESTING ROBUST CLI INTEGRATION")
    print("=" * 40)
    
    try:
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        
        # Initialize operations
        operations = RobustCLIOperations()
        print("[OK] RobustCLIOperations initialized")
        
        # Test 1: System status
        print("\n1. Testing system status methods...")
        status = operations.get_system_status()
        print(f"[OK] System status: {status}")
        
        # Test 2: List query templates
        print("\n2. Testing query template listing...")
        templates = operations.list_query_templates()
        print(f"[OK] Templates listed: {len(templates.get('templates', []))} templates")
        print(f"     Categories: {len(templates.get('categories', []))} categories")
        
        # Test 3: List memo types
        print("\n3. Testing memo type listing...")
        memo_types = operations.list_memo_types()
        print(f"[OK] Memo types: {len(memo_types.get('memo_types', []))} types")
        if 'memo_types' in memo_types:
            print(f"     Available types: {[mt['value'] for mt in memo_types['memo_types'][:3]]}...")
        
        # Test 4: Check capabilities
        print("\n4. Testing capability detection...")
        await operations.initialize()
        print("[OK] System initialization completed")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Robust CLI integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_export_functionality():
    """Test export functionality without LLM"""
    print("TESTING EXPORT FUNCTIONALITY")
    print("=" * 40)
    
    try:
        from src.qc.export.data_exporter import DataExporter
        from pathlib import Path as PathlibPath
        
        print("[OK] DataExporter imported")
        
        # Test 1: Check R integration methods exist
        exporter = DataExporter()
        print("[OK] DataExporter initialized")
        
        # Check if methods exist (without calling them with real data)
        methods_to_check = [
            'export_r_compatible_csv',
            'generate_r_import_script', 
            'export_r_package_integration',
            'generate_r_integration_readme'
        ]
        
        for method_name in methods_to_check:
            if hasattr(exporter, method_name):
                print(f"[OK] Method exists: {method_name}")
            else:
                print(f"[ERROR] Missing method: {method_name}")
        
        # Test 2: Test with minimal mock data
        print("\n2. Testing R export with mock data...")
        
        # Create correctly formatted mock data - list of interviews
        mock_interviews = [
            {
                'interview_id': 'interview_1',
                'quotes': [
                    {
                        'id': 'q1', 
                        'text': 'test quote', 
                        'code_names': ['code1'],
                        'speaker': {'name': 'Test Speaker 1'},
                        'location_start': 0,
                        'location_end': 10
                    },
                    {
                        'id': 'q2', 
                        'text': 'another quote', 
                        'code_names': ['code2'],
                        'speaker': {'name': 'Test Speaker 2'},
                        'location_start': 50,
                        'location_end': 65
                    }
                ]
            }
        ]
        
        # Test R-compatible CSV generation
        r_csv_result = exporter.export_r_compatible_csv(mock_interviews, "test_r_output.csv")
        print(f"[OK] R CSV export: {r_csv_result}")
        
        # Test R script generation
        r_script = exporter.generate_r_import_script("test_r_output.csv")
        print(f"[OK] R script generated: {len(r_script)} characters")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Export functionality failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run integration tests"""
    print("SYSTEM INTEGRATION TESTING")
    print("=" * 50)
    
    results = []
    
    # Test robust CLI
    cli_result = await test_robust_cli_integration()
    results.append(("Robust CLI Integration", cli_result))
    
    # Test export functionality
    export_result = await test_export_functionality()
    results.append(("Export Functionality", export_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)