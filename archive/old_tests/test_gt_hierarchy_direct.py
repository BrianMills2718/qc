#!/usr/bin/env python3
"""
Direct test of GT hierarchy implementation
Tests the actual LLM behavior and Neo4j persistence
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from src.qc.core.robust_cli_operations import RobustCLIOperations
from src.qc.config.methodology_config import MethodologyConfigManager
from src.qc.workflows.grounded_theory import GroundedTheoryWorkflow
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_hierarchy_direct():
    """Test hierarchical GT implementation with real LLM and Neo4j"""
    print("=" * 60)
    print("TESTING GT HIERARCHY IMPLEMENTATION")
    print("=" * 60)
    
    # 1. Load config and initialize
    print("\n1. INITIALIZATION")
    config_manager = MethodologyConfigManager()
    config = config_manager.load_config_from_path(
        Path('config/methodology_configs/grounded_theory_reliable.yaml')
    )
    print(f"   Config loaded: {config.methodology}")
    
    operations = RobustCLIOperations(config=config)
    await operations.initialize_systems()
    print("   Systems initialized")
    
    # 2. Load interviews
    print("\n2. LOADING DATA")
    interviews = operations.robust_load_interviews(
        Path('data/interviews/ai_interviews_3_for_test')
    )
    print(f"   Loaded {len(interviews)} interviews")
    
    # 3. Create and run workflow
    print("\n3. RUNNING GT WORKFLOW")
    workflow = GroundedTheoryWorkflow(operations, config=config)
    print("   Starting workflow...")
    
    result = await workflow.execute_complete_workflow(interviews)
    
    # 4. CHECK RESULTS
    print("\n4. CHECKING HIERARCHY IN RESULTS")
    print(f"   Total open codes: {len(result.open_codes)}")
    print(f"   Total core categories: {len(result.core_categories)}")
    
    # Check for hierarchy
    hierarchy_found = False
    for i, code in enumerate(result.open_codes[:10]):  # Check first 10
        if code.parent_id or code.child_codes or code.level > 0:
            hierarchy_found = True
            print(f"\n   HIERARCHY DETECTED in code {i+1}:")
            print(f"     Name: {code.code_name}")
            print(f"     Parent ID: {code.parent_id}")
            print(f"     Level: {code.level}")
            print(f"     Child codes: {code.child_codes}")
    
    if not hierarchy_found:
        print("\n   ⚠️ WARNING: No hierarchy detected in codes!")
        print("   Sample codes:")
        for code in result.open_codes[:3]:
            print(f"     - {code.code_name} (level={code.level}, parent={code.parent_id})")
    
    # Check multiple core categories
    if len(result.core_categories) > 1:
        print(f"\n   ✅ MULTIPLE CORE CATEGORIES: {len(result.core_categories)}")
        for cat in result.core_categories:
            print(f"     - {cat.category_name}")
    else:
        print(f"\n   ⚠️ SINGLE CORE CATEGORY: {result.core_categories[0].category_name if result.core_categories else 'None'}")
    
    # 5. TEST NEO4J PERSISTENCE
    print("\n5. TESTING NEO4J PERSISTENCE")
    
    # Create Neo4j manager
    neo4j = EnhancedNeo4jManager()
    await neo4j.connect()
    
    # Store codes with hierarchy
    for code in result.open_codes[:5]:  # Store first 5 codes
        properties = {
            'name': code.code_name,
            'description': code.description,
            'confidence': code.confidence,
            'parent_id': code.parent_id,
            'level': code.level,
            'child_codes': json.dumps(code.child_codes)  # Store as JSON string
        }
        
        await neo4j.create_code(
            code_id=code.code_name.replace(' ', '_'),
            **properties
        )
        print(f"   Stored code: {code.code_name} (level={code.level})")
    
    # Query to verify
    query = "MATCH (c:Code) RETURN c.name as name, c.level as level, c.parent_id as parent_id LIMIT 10"
    async with neo4j.driver.session() as session:
        result_neo4j = await session.run(query)
        codes_in_db = await result_neo4j.data()
    
    print(f"\n   Codes in Neo4j: {len(codes_in_db)}")
    for code in codes_in_db[:3]:
        print(f"     - {code['name']} (level={code['level']}, parent={code['parent_id']})")
    
    await neo4j.close()
    
    # 6. CHECK REPORT GENERATION
    print("\n6. CHECKING REPORT GENERATION")
    
    # Generate report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = Path(f"reports/test_hierarchy_{timestamp}")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Write executive summary
    summary_file = report_dir / "hierarchy_test_summary.md"
    with open(summary_file, 'w') as f:
        f.write("# GT Hierarchy Test Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## Results\n\n")
        f.write(f"- Open Codes: {len(result.open_codes)}\n")
        f.write(f"- Core Categories: {len(result.core_categories)}\n")
        f.write(f"- Hierarchy Found: {'Yes' if hierarchy_found else 'No'}\n\n")
        
        if hierarchy_found:
            f.write("### Hierarchical Codes\n\n")
            for code in result.open_codes:
                if code.parent_id or code.child_codes:
                    f.write(f"- **{code.code_name}**\n")
                    f.write(f"  - Parent: {code.parent_id or 'None'}\n")
                    f.write(f"  - Level: {code.level}\n")
                    f.write(f"  - Children: {', '.join(code.child_codes) if code.child_codes else 'None'}\n\n")
    
    print(f"   Report saved to: {summary_file}")
    
    # FINAL SUMMARY
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Workflow completed successfully")
    print(f"{'✅' if hierarchy_found else '❌'} Hierarchy in codes")
    print(f"{'✅' if len(result.core_categories) > 1 else '⚠️'} Multiple core categories")
    print(f"✅ Neo4j persistence tested")
    print(f"✅ Report generated")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_hierarchy_direct())
    print("\nTest complete!")