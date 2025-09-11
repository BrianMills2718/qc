#!/usr/bin/env python3
"""
Direct test of Neo4j hierarchy storage using custom queries
"""
import asyncio
import json
from datetime import datetime
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_neo4j_hierarchy_direct():
    """Test storing hierarchical codes directly in Neo4j"""
    print("=" * 60)
    print("DIRECT NEO4J HIERARCHY TEST")
    print("=" * 60)
    
    # 1. Connect to Neo4j
    print("\n1. CONNECTING TO NEO4J...")
    neo4j = EnhancedNeo4jManager()
    if not neo4j.driver:
        try:
            await neo4j.connect()
        except Exception as e:
            print(f"   [ERROR] Failed to connect: {e}")
            return False
    print("   [OK] Connected")
    
    # 2. Clear test data
    print("\n2. CLEARING TEST DATA...")
    clear_query = """
    MATCH (c:Code) 
    WHERE c.name STARTS WITH 'Test_' 
    DETACH DELETE c
    """
    async with neo4j.driver.session() as session:
        await session.run(clear_query)
    print("   [OK] Cleared")
    
    # 3. Create hierarchical codes with custom query
    print("\n3. CREATING HIERARCHICAL CODES...")
    
    # Create parent code
    parent_query = """
    CREATE (c:Code {
        id: $id,
        name: $name,
        description: $description,
        parent_id: $parent_id,
        level: $level,
        child_codes: $child_codes,
        created_at: $created_at
    })
    RETURN c
    """
    
    async with neo4j.driver.session() as session:
        # Create parent
        parent_result = await session.run(
            parent_query,
            id="test_parent",
            name="Test_AI_Tools",
            description="Parent code for AI tools",
            parent_id=None,
            level=0,
            child_codes=json.dumps(["test_child1", "test_child2"]),
            created_at=datetime.utcnow().isoformat()
        )
        parent = await parent_result.single()
        print(f"   Created parent: {parent['c']['name']}")
        
        # Create children
        for i, child_id in enumerate(["test_child1", "test_child2"], 1):
            child_result = await session.run(
                parent_query,
                id=child_id,
                name=f"Test_Child_{i}",
                description=f"Child code {i}",
                parent_id="test_parent",
                level=1,
                child_codes=json.dumps([]),
                created_at=datetime.utcnow().isoformat()
            )
            child = await child_result.single()
            print(f"   Created child: {child['c']['name']}")
    
    # 4. Create relationships
    print("\n4. CREATING RELATIONSHIPS...")
    rel_query = """
    MATCH (parent:Code {id: 'test_parent'})
    MATCH (child:Code)
    WHERE child.parent_id = 'test_parent'
    CREATE (parent)-[:HAS_CHILD]->(child)
    CREATE (child)-[:CHILD_OF]->(parent)
    RETURN count(*) as rel_count
    """
    
    async with neo4j.driver.session() as session:
        result = await session.run(rel_query)
        data = await result.single()
        print(f"   Created {data['rel_count']} relationships")
    
    # 5. Query hierarchy
    print("\n5. QUERYING HIERARCHY...")
    query = """
    MATCH (parent:Code {level: 0})
    WHERE parent.name STARTS WITH 'Test_'
    OPTIONAL MATCH (parent)-[:HAS_CHILD]->(child:Code)
    RETURN parent.name as parent_name,
           parent.level as level,
           parent.child_codes as child_codes,
           collect(child.name) as children
    """
    
    async with neo4j.driver.session() as session:
        result = await session.run(query)
        hierarchies = await result.data()
    
    print(f"   Found {len(hierarchies)} hierarchies:")
    for h in hierarchies:
        print(f"   - {h['parent_name']} (level {h['level']})")
        print(f"     Stored children: {h['child_codes']}")
        print(f"     Actual children: {h['children']}")
    
    # 6. Save evidence
    print("\n6. SAVING EVIDENCE...")
    evidence = {
        'timestamp': datetime.now().isoformat(),
        'hierarchies_found': len(hierarchies),
        'hierarchy_data': hierarchies,
        'success': len(hierarchies) > 0 and len(hierarchies[0]['children']) > 0
    }
    
    with open('evidence/current/Evidence_Neo4j_Direct_Hierarchy.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    print("   [OK] Evidence saved")
    
    await neo4j.close()
    
    # Result
    print("\n" + "=" * 60)
    if len(hierarchies) > 0 and hierarchies[0]['children']:
        print("SUCCESS: Hierarchical codes stored in Neo4j!")
        print(f"Parent has {len(hierarchies[0]['children'])} children")
        return True
    else:
        print("FAILURE: Hierarchy not properly stored")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_hierarchy_direct())
    exit(0 if success else 1)