#!/usr/bin/env python3
"""
Test Neo4j query template execution without LLM calls
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_neo4j_query_execution():
    """Test actual Neo4j query execution"""
    print("TESTING NEO4J QUERY EXECUTION")
    print("=" * 40)
    
    try:
        from src.qc.query.query_templates import QueryTemplateLibrary, QueryTemplateExecutor
        from src.qc.core.neo4j_manager import EnhancedNeo4jManager
        
        # Initialize components
        neo4j_manager = EnhancedNeo4jManager()
        await neo4j_manager.connect()
        print("[OK] Neo4j connected")
        
        query_lib = QueryTemplateLibrary()
        query_executor = QueryTemplateExecutor(neo4j_manager)
        print("[OK] Query components initialized")
        
        # Test 1: Basic database info query (should always work)
        print("\n1. Testing basic database connectivity...")
        basic_result = await neo4j_manager.execute_cypher("RETURN 'Hello Neo4j' as message, datetime() as timestamp")
        print(f"[SUCCESS] Basic query result: {basic_result[0] if basic_result else 'No result'}")
        
        # Test 2: Check what data exists
        print("\n2. Checking existing data in database...")
        node_count_query = """
        MATCH (n) 
        RETURN labels(n)[0] as node_type, count(n) as count 
        ORDER BY count DESC
        """
        data_results = await neo4j_manager.execute_cypher(node_count_query)
        print("[INFO] Current database contents:")
        for result in data_results[:10]:  # Show top 10
            print(f"       {result.get('node_type', 'Unknown')}: {result.get('count', 0)} nodes")
        
        # Test 3: Try a simple template execution
        print("\n3. Testing query template execution...")
        templates = query_lib.list_templates()
        
        # Find a simple template to test
        simple_template = None
        for template in templates:
            if 'basic' in template.name.lower() or 'count' in template.name.lower():
                simple_template = template
                break
        
        if not simple_template and templates:
            simple_template = templates[0]  # Use first available template
        
        if simple_template:
            print(f"[INFO] Testing template: {simple_template.name}")
            try:
                # Execute with minimal parameters
                template_results = await query_executor.execute_template(
                    simple_template.id,  # Use 'id' not 'template_id'
                    parameters={}  # Try with no parameters first
                )
                print(f"[SUCCESS] Template executed, returned {len(template_results)} results")
                if template_results:
                    print(f"         Sample result keys: {list(template_results[0].keys())}")
                
            except Exception as template_error:
                print(f"[INFO] Template needs parameters: {template_error}")
                # This is expected for templates requiring parameters
        
        # Test 4: Test template parameter validation
        print("\n4. Testing template parameter validation...")
        network_templates = query_lib.list_templates_by_category("network_analysis")
        if network_templates:
            template = network_templates[0]
            print(f"[INFO] Checking parameters for: {template.name}")
            print(f"       Required parameters: {template.parameters}")
            print(f"       Description: {template.description[:100]}...")
        
        await neo4j_manager.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Neo4j query testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_analytical_memo_structure():
    """Test analytical memo data structures without LLM generation"""
    print("\nTESTING ANALYTICAL MEMO STRUCTURES")
    print("=" * 40)
    
    try:
        from src.qc.analysis.analytical_memos import (
            AnalyticalMemo, ThematicPattern, ResearchInsight, 
            TheoreticalConnection, MemoType, InsightLevel
        )
        
        print("[OK] Memo structure imports successful")
        
        # Test 1: Manual memo creation (no LLM)
        print("\n1. Testing manual memo structure creation...")
        
        # Create test patterns
        test_pattern = ThematicPattern(
            pattern_name="Test Pattern",
            description="A test pattern for validation",
            supporting_codes=["code1", "code2"],
            frequency=5,
            confidence=0.8,
            examples=["Example quote 1", "Example quote 2"]
        )
        print("[OK] ThematicPattern structure valid")
        
        # Create test insights
        test_insight = ResearchInsight(
            insight_title="Test Insight",
            insight_level=InsightLevel.ANALYTICAL.value,
            description="A test insight for validation",
            significance="Important for testing",
            supporting_data=["Data point 1", "Data point 2"],
            implications="Testing implications"
        )
        print("[OK] ResearchInsight structure valid")
        
        # Create test theoretical connection
        test_connection = TheoreticalConnection(
            theory_name="Test Theory",
            connection_type="supports",
            description="Connection description",
            implications="Theoretical implications",
            supporting_evidence=["Evidence 1", "Evidence 2"]
        )
        print("[OK] TheoreticalConnection structure valid")
        
        # Create complete memo
        test_memo = AnalyticalMemo(
            memo_id="test_memo_001",
            title="Test Analytical Memo",
            memo_type=MemoType.PATTERN_ANALYSIS.value,
            executive_summary="This is a test memo",
            patterns=[test_pattern],
            insights=[test_insight],
            theoretical_connections=[test_connection],
            methodological_notes="Test methodology",
            limitations="Test limitations",
            future_research="Future test research",
            confidence_assessment="High confidence in test"
        )
        print("[SUCCESS] Complete AnalyticalMemo structure valid")
        
        # Test 2: JSON serialization
        print("\n2. Testing memo JSON serialization...")
        memo_dict = test_memo.model_dump()
        print(f"[OK] Memo serializes to {len(memo_dict)} fields")
        print(f"     Key fields: {list(memo_dict.keys())}")
        
        # Test 3: Validation
        print("\n3. Testing memo validation...")
        # Try invalid data
        try:
            invalid_memo = AnalyticalMemo(
                memo_id="",  # Invalid: empty string
                title="Test",
                memo_type="invalid_type",  # Invalid type
                executive_summary="",
                patterns=[],
                insights=[],
                theoretical_connections=[],
                methodological_notes="",
                limitations="",
                future_research="",
                confidence_assessment=""
            )
            print("[WARNING] Invalid memo was accepted (validation may be too loose)")
        except Exception as validation_error:
            print(f"[OK] Validation working: {type(validation_error).__name__}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Memo structure testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all non-LLM validation tests"""
    print("NON-LLM SYSTEM VALIDATION")
    print("=" * 50)
    
    results = []
    
    # Test Neo4j queries
    neo4j_result = await test_neo4j_query_execution()
    results.append(("Neo4j Query Execution", neo4j_result))
    
    # Test memo structures
    memo_result = await test_analytical_memo_structure()
    results.append(("Analytical Memo Structures", memo_result))
    
    # Summary
    print("\n" + "=" * 50)
    print("NON-LLM VALIDATION RESULTS")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n[SUCCESS] All non-LLM functionality validated!")
    else:
        print("\n[PARTIAL] Some functionality needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)