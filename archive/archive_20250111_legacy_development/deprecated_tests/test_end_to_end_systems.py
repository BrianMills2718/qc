#!/usr/bin/env python3
"""
End-to-end test for both debugged systems: Neo4j Query Templates and Analytical Memos
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_neo4j_query_templates():
    """Test Neo4j query template system"""
    print("\n1. TESTING NEO4J QUERY TEMPLATES")
    print("-" * 40)
    
    try:
        # Test importing query templates (this was failing before due to import issues)
        from src.qc.query.query_templates import QueryTemplateLibrary, QueryTemplate
        
        print("[OK] Query template imports successful")
        
        # Test creating query library
        query_lib = QueryTemplateLibrary()
        print("[OK] QueryTemplateLibrary initialized")
        
        # Test loading templates
        templates = query_lib.list_templates()
        print(f"[OK] Loaded {len(templates)} query templates")
        
        # Test getting categories
        categories = query_lib.get_template_categories()
        print(f"[OK] Available categories: {', '.join(categories)}")
        
        # Test getting a specific template
        if templates:
            template = templates[0]
            print(f"[OK] Sample template: {template.name} (ID: {template.template_id})")
            print(f"     Category: {template.category}")
            print(f"     Description: {template.description[:60]}...")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Neo4j query templates failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_analytical_memos():
    """Test analytical memo generation system"""
    print("\n2. TESTING ANALYTICAL MEMO GENERATION")
    print("-" * 40)
    
    try:
        from src.qc.analysis.analytical_memos import AnalyticalMemoGenerator, MemoType
        from src.qc.llm.llm_handler import LLMHandler
        
        print("[OK] Analytical memo imports successful")
        
        # Initialize components
        llm_handler = LLMHandler()
        memo_generator = AnalyticalMemoGenerator(llm_handler)
        print("[OK] Components initialized")
        
        # Test data
        sample_data = [
            {
                "interview_id": "test_interview_1",
                "quotes": [
                    {
                        "id": "test_quote_1", 
                        "text": "We faced significant challenges in project coordination",
                        "code_names": ["project_management", "challenges", "coordination"]
                    },
                    {
                        "id": "test_quote_2",
                        "text": "Team collaboration tools made a big difference",
                        "code_names": ["collaboration", "tools", "team_effectiveness"]
                    }
                ]
            }
        ]
        
        # Generate pattern analysis memo
        print("[INFO] Generating pattern analysis memo...")
        memo = await memo_generator.generate_pattern_analysis_memo(
            interview_data=sample_data,
            focus_codes=["project_management", "collaboration"],
            memo_title="End-to-End Test Memo"
        )
        
        print(f"[SUCCESS] Memo generated successfully!")
        print(f"          Type: {memo.memo_type}")
        print(f"          Title: {memo.title}")
        print(f"          Patterns: {len(memo.patterns)}")
        print(f"          Insights: {len(memo.insights)}")
        print(f"          Theoretical connections: {len(memo.theoretical_connections)}")
        
        # Test memo export
        memo_json = memo_generator.save_memo_json(memo, Path("test_memo_output.json"))
        print(f"[OK] Memo exported to JSON: {memo_json}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Analytical memo generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_robust_cli_integration():
    """Test integration with robust CLI operations"""
    print("\n3. TESTING ROBUST CLI INTEGRATION")
    print("-" * 40)
    
    try:
        from src.qc.core.robust_cli_operations import RobustCLIOperations
        from pathlib import Path as PathlibPath
        
        print("[OK] RobustCLIOperations import successful")
        
        # Initialize robust operations
        operations = RobustCLIOperations()
        await operations.initialize()
        
        print("[OK] RobustCLIOperations initialized")
        
        # Test query template listing
        query_types = operations.list_query_templates()
        print(f"[OK] Query templates accessible: {len(query_types.get('templates', []))} templates")
        
        # Test memo type listing  
        memo_types = operations.list_memo_types()
        print(f"[OK] Memo types accessible: {len(memo_types.get('memo_types', []))} types")
        
        # Test system status
        system_status = operations.get_system_status()
        print(f"[OK] System status: {system_status}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Robust CLI integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all end-to-end tests"""
    print("END-TO-END SYSTEM TESTING")
    print("=" * 50)
    
    results = []
    
    # Test 1: Neo4j Query Templates
    result1 = await test_neo4j_query_templates()
    results.append(("Neo4j Query Templates", result1))
    
    # Test 2: Analytical Memo Generation
    result2 = await test_analytical_memos()
    results.append(("Analytical Memo Generation", result2))
    
    # Test 3: Robust CLI Integration
    result3 = await test_robust_cli_integration()
    results.append(("Robust CLI Integration", result3))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("[SUCCESS] All systems operational!")
        print("Both debugged systems are working end-to-end.")
    else:
        print("[PARTIAL] Some systems need further debugging.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)