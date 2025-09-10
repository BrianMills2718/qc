#!/usr/bin/env python3
"""
Test that hierarchical codes can be stored and retrieved from Neo4j
"""
import asyncio
import json
from datetime import datetime
from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.workflows.grounded_theory import OpenCode

async def test_neo4j_hierarchy_storage():
    """Test storing and retrieving hierarchical codes in Neo4j"""
    print("=" * 60)
    print("TEST: NEO4J HIERARCHY STORAGE")
    print("=" * 60)
    
    # 1. Create test hierarchical codes
    print("\n1. CREATING TEST HIERARCHICAL CODES...")
    
    parent_code = OpenCode(
        code_name="AI Tool Usage",
        description="Overall usage patterns of AI tools",
        properties=["efficiency", "adoption"],
        dimensions=["frequency", "context"],
        supporting_quotes=["We use AI tools daily"],
        frequency=10,
        confidence=0.95,
        parent_id=None,
        level=0,
        child_codes=["ChatGPT_Usage", "Claude_Usage"]
    )
    
    child_code1 = OpenCode(
        code_name="ChatGPT Usage",
        description="Specific ChatGPT usage patterns",
        properties=["summarization"],
        dimensions=["research"],
        supporting_quotes=["I use ChatGPT for papers"],
        frequency=5,
        confidence=0.9,
        parent_id="AI_Tool_Usage",
        level=1,
        child_codes=[]
    )
    
    child_code2 = OpenCode(
        code_name="Claude Usage",
        description="Specific Claude usage patterns",
        properties=["coding"],
        dimensions=["development"],
        supporting_quotes=["Claude helps with debugging"],
        frequency=5,
        confidence=0.9,
        parent_id="AI_Tool_Usage",
        level=1,
        child_codes=[]
    )
    
    codes = [parent_code, child_code1, child_code2]
    print(f"   [OK] Created {len(codes)} hierarchical codes")
    
    # 2. Connect to Neo4j
    print("\n2. CONNECTING TO NEO4J...")
    neo4j = EnhancedNeo4jManager()
    
    # Check if already connected
    if not neo4j.driver:
        try:
            await neo4j.connect()
        except Exception as e:
            print(f"   [ERROR] Failed to connect to Neo4j: {e}")
            return False
    print("   [OK] Connected to Neo4j")
    
    # 3. Clear existing test codes
    print("\n3. CLEARING EXISTING TEST CODES...")
    clear_query = """
    MATCH (c:Code) 
    WHERE c.name STARTS WITH 'AI Tool Usage' 
       OR c.name STARTS WITH 'ChatGPT Usage' 
       OR c.name STARTS WITH 'Claude Usage'
    DETACH DELETE c
    """
    async with neo4j.driver.session() as session:
        await session.run(clear_query)
    print("   [OK] Cleared existing test codes")
    
    # 4. Store hierarchical codes
    print("\n4. STORING HIERARCHICAL CODES...")
    for code in codes:
        # Create code properties with hierarchy fields
        code_data = {
            'id': code.code_name.replace(' ', '_'),
            'name': code.code_name,
            'description': code.description,
            'confidence': code.confidence,
            'frequency': code.frequency,
            'parent_id': code.parent_id,
            'level': code.level,
            'child_codes': json.dumps(code.child_codes) if code.child_codes else '[]'
        }
        
        # Store in Neo4j
        await neo4j.create_code(code_data)
        print(f"   Stored: {code.code_name} (level={code.level}, parent={code.parent_id})")
    
    # 5. Create hierarchical relationships
    print("\n5. CREATING PARENT-CHILD RELATIONSHIPS...")
    relationship_query = """
    MATCH (parent:Code {name: 'AI Tool Usage'})
    MATCH (child:Code) 
    WHERE child.parent_id = 'AI_Tool_Usage'
    MERGE (parent)-[:HAS_CHILD]->(child)
    MERGE (child)-[:CHILD_OF]->(parent)
    RETURN count(*) as relationships_created
    """
    async with neo4j.driver.session() as session:
        result = await session.run(relationship_query)
        data = await result.single()
        print(f"   [OK] Created {data['relationships_created']} relationships")
    
    # 6. Query hierarchical structure
    print("\n6. QUERYING HIERARCHICAL STRUCTURE...")
    
    # Query parent with children
    query_hierarchy = """
    MATCH (parent:Code {level: 0})
    OPTIONAL MATCH (parent)-[:HAS_CHILD]->(child:Code)
    RETURN parent.name as parent_name, 
           parent.level as parent_level,
           parent.child_codes as child_list,
           collect(child.name) as actual_children
    """
    
    async with neo4j.driver.session() as session:
        result = await session.run(query_hierarchy)
        hierarchies = await result.data()
    
    print(f"   Found {len(hierarchies)} parent codes:")
    for h in hierarchies:
        print(f"   - {h['parent_name']} (level {h['parent_level']})")
        print(f"     Child codes field: {h['child_list']}")
        print(f"     Actual children: {h['actual_children']}")
    
    # 7. Verify hierarchy integrity
    print("\n7. VERIFYING HIERARCHY INTEGRITY...")
    
    # Check if children point back to parent
    verify_query = """
    MATCH (child:Code {level: 1})
    OPTIONAL MATCH (child)-[:CHILD_OF]->(parent:Code)
    RETURN child.name as child_name,
           child.parent_id as stored_parent_id,
           parent.name as actual_parent
    """
    
    async with neo4j.driver.session() as session:
        result = await session.run(verify_query)
        verifications = await result.data()
    
    all_valid = True
    for v in verifications:
        valid = v['actual_parent'] is not None
        status = "[OK]" if valid else "[ERROR]"
        print(f"   {status} {v['child_name']} -> {v['actual_parent']}")
        if not valid:
            all_valid = False
    
    # 8. Generate evidence
    print("\n8. GENERATING EVIDENCE...")
    
    evidence = {
        'timestamp': datetime.now().isoformat(),
        'codes_stored': len(codes),
        'hierarchies_found': len(hierarchies),
        'relationships_verified': len(verifications),
        'hierarchy_intact': all_valid,
        'sample_hierarchy': hierarchies[0] if hierarchies else None
    }
    
    evidence_file = 'evidence/current/Evidence_Neo4j_Hierarchy_Storage.json'
    with open(evidence_file, 'w') as f:
        json.dump(evidence, f, indent=2)
    print(f"   [OK] Evidence saved to {evidence_file}")
    
    # 9. Cleanup
    await neo4j.close()
    
    # Result
    print("\n" + "=" * 60)
    if all_valid and len(hierarchies) > 0:
        print("SUCCESS: Hierarchical codes stored and retrieved from Neo4j")
        return True
    else:
        print("FAILURE: Hierarchy not properly stored in Neo4j")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_hierarchy_storage())
    exit(0 if success else 1)