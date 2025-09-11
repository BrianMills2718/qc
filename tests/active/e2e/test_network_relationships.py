#!/usr/bin/env python3
"""
Direct Neo4j relationship testing script for network visualization debugging.
Tests database structure independently of web API to identify root causes.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.qc.core.neo4j_manager import EnhancedNeo4jManager


async def test_database_structure():
    """Test Neo4j database structure and relationship patterns"""
    print("PHASE 1: DATABASE STRUCTURE DIAGNOSTIC TESTING")
    print("=" * 60)
    
    try:
        neo4j = EnhancedNeo4jManager()
        await neo4j.connect()
        print("Neo4j connection established")
        
        # Test 1: Verify AI entity exists
        print("\nTEST 1: AI Entity Existence")
        entity_query = """
        MATCH (e:Entity {name: $entity_name})
        RETURN count(e) as entity_count, e.entity_type as entity_type
        """
        result = await neo4j.execute_cypher(entity_query, {"entity_name": "AI"})
        if result and result[0]['entity_count'] > 0:
            print(f"PASS: AI entity exists: {result[0]['entity_count']} instances")
            print(f"  Entity type: {result[0].get('entity_type', 'N/A')}")
        else:
            print("FAIL: AI entity does NOT exist in database")
            return False
        
        # Test 2: Check quote-entity relationships for AI
        print("\nTEST 2: Quote-Entity MENTIONS Relationships")
        quote_entity_query = """
        MATCH (q:Quote)-[:MENTIONS]->(e:Entity {name: $entity_name})
        RETURN count(DISTINCT q) as quote_count,
               count(DISTINCT e) as entity_count,
               collect(DISTINCT q.id)[..5] as sample_quote_ids
        """
        result = await neo4j.execute_cypher(quote_entity_query, {"entity_name": "AI"})
        if result and result[0]['quote_count'] > 0:
            print(f"PASS: Quotes mentioning AI: {result[0]['quote_count']}")
            print(f"  Sample quote IDs: {result[0]['sample_quote_ids']}")
        else:
            print("FAIL: NO quotes have MENTIONS relationships to AI entity")
            print("  This explains why relationship query fails!")
            return False
        
        # Test 3: Find other entities connected to AI through quotes
        print("\nTEST 3: Connected Entities Through Shared Quotes")
        connected_entities_query = """
        MATCH (ai:Entity {name: $entity_name})
        MATCH (q:Quote)-[:MENTIONS]->(ai)
        MATCH (q)-[:MENTIONS]->(other:Entity)
        WHERE other.name <> $entity_name
        RETURN other.name as connected_entity,
               count(DISTINCT q) as shared_quotes
        ORDER BY shared_quotes DESC
        LIMIT 20
        """
        result = await neo4j.execute_cypher(connected_entities_query, {"entity_name": "AI"})
        if result and len(result) > 0:
            print(f"✓ Connected entities found: {len(result)}")
            for row in result[:10]:  # Show top 10
                print(f"  {row['connected_entity']}: {row['shared_quotes']} shared quotes")
            connected_names = [row['connected_entity'] for row in result]
        else:
            print("❌ NO connected entities found through shared quotes")
            return False
        
        # Test 4: Test the exact relationship query from the API
        print("\n📊 TEST 4: Exact Relationship Query from API")
        test_entities = ["AI"] + connected_names[:10]  # Use AI + top 10 connected
        print(f"  Testing with entities: {test_entities[:5]}...")
        
        relationship_query = """
        UNWIND $entity_names as name1
        UNWIND $entity_names as name2
        WITH name1, name2 WHERE name1 < name2
        
        MATCH (e1:Entity {name: name1}), (e2:Entity {name: name2})
        OPTIONAL MATCH (q:Quote)-[:MENTIONS]->(e1), (q)-[:MENTIONS]->(e2)
        
        WITH name1, name2, count(DISTINCT q) as shared_quotes
        WHERE shared_quotes > 0
        
        RETURN collect({
            source: name1,
            target: name2,
            weight: shared_quotes  
        }) as relationships
        """
        
        result = await neo4j.execute_cypher(relationship_query, {"entity_names": test_entities})
        if result and result[0] and result[0]['relationships']:
            relationships = result[0]['relationships']
            print(f"✓ Relationship query successful: {len(relationships)} relationships found")
            for rel in relationships[:5]:  # Show first 5
                print(f"  {rel['source']} ↔ {rel['target']}: weight {rel['weight']}")
            return True
        else:
            print("❌ Relationship query returned NO relationships")
            print("  This is the ROOT CAUSE of the API failure!")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_api_query():
    """Test the basic query from get_entity_network_fixed"""
    print("\n🔍 PHASE 2: BASIC API QUERY TESTING")
    print("=" * 60)
    
    try:
        neo4j = EnhancedNeo4jManager()
        await neo4j.connect()
        
        # Test the exact basic query from the API
        basic_query = """
        MATCH (center:Entity {name: $entity_name})
        OPTIONAL MATCH (q:Quote)-[:MENTIONS]->(center)
        OPTIONAL MATCH (q)-[:MENTIONS]->(connected:Entity)
        WHERE connected.name <> $entity_name
        
        WITH $entity_name as center_name,
             count(DISTINCT center) as center_mentions,
             count(DISTINCT q) as quote_count,
             collect(DISTINCT {
                name: connected.name,
                type: connected.entity_type,
                mentions: 1
            }) as connected_entities,
             collect(DISTINCT center.interview_id) as interviews
        
        RETURN {
            center_entity: center_name,
            center_mentions: center_mentions,
            quote_count: quote_count,
            connected_entities: connected_entities,
            interviews: interviews
        } as basic_data
        """
        
        result = await neo4j.execute_cypher(basic_query, {"entity_name": "AI"})
        if result and result[0] and result[0]['basic_data']:
            basic_data = result[0]['basic_data']
            print(f"✓ Basic query successful")
            print(f"  Center entity: {basic_data['center_entity']}")
            print(f"  Center mentions: {basic_data['center_mentions']}")
            print(f"  Quote count: {basic_data['quote_count']}")
            print(f"  Connected entities: {len(basic_data['connected_entities'])}")
            
            connected_names = [e['name'] for e in basic_data['connected_entities'] if e['name']]
            print(f"  Connected entity names: {connected_names[:10]}")
            return basic_data, connected_names
        else:
            print("❌ Basic query failed or returned no data")
            return None, []
            
    except Exception as e:
        print(f"❌ Basic API query test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, []


async def diagnose_relationship_query_issue(connected_names):
    """Diagnose specific issues with the relationship query"""
    print("\n🔍 PHASE 3: RELATIONSHIP QUERY DIAGNOSIS")
    print("=" * 60)
    
    if len(connected_names) <= 1:
        print(f"❌ Insufficient connected entities: {len(connected_names)}")
        print("  Need at least 2 entities to create relationships")
        return False
    
    try:
        neo4j = EnhancedNeo4jManager()
        await neo4j.connect()
        
        # Test each step of the relationship query
        test_entities = connected_names[:5]  # Test with first 5
        print(f"Testing relationship query with: {test_entities}")
        
        # Step 1: Test entity pairs generation
        pairs_query = """
        UNWIND $entity_names as name1
        UNWIND $entity_names as name2
        WITH name1, name2 WHERE name1 < name2
        RETURN name1, name2
        LIMIT 10
        """
        result = await neo4j.execute_cypher(pairs_query, {"entity_names": test_entities})
        print(f"✓ Entity pairs generated: {len(result)}")
        for pair in result[:5]:
            print(f"  {pair['name1']} ↔ {pair['name2']}")
        
        # Step 2: Test entity matching
        entity_match_query = """
        UNWIND $entity_names as name1
        UNWIND $entity_names as name2
        WITH name1, name2 WHERE name1 < name2
        
        MATCH (e1:Entity {name: name1}), (e2:Entity {name: name2})
        RETURN name1, name2, e1.name as e1_found, e2.name as e2_found
        LIMIT 10
        """
        result = await neo4j.execute_cypher(entity_match_query, {"entity_names": test_entities})
        print(f"✓ Entity matches found: {len(result)}")
        
        # Step 3: Test quote relationships
        quote_match_query = """
        UNWIND $entity_names as name1
        UNWIND $entity_names as name2
        WITH name1, name2 WHERE name1 < name2
        
        MATCH (e1:Entity {name: name1}), (e2:Entity {name: name2})
        OPTIONAL MATCH (q:Quote)-[:MENTIONS]->(e1), (q)-[:MENTIONS]->(e2)
        
        RETURN name1, name2, count(DISTINCT q) as shared_quotes
        ORDER BY shared_quotes DESC
        LIMIT 20
        """
        result = await neo4j.execute_cypher(quote_match_query, {"entity_names": test_entities})
        print(f"✓ Quote relationship analysis complete")
        
        has_relationships = False
        for row in result:
            if row['shared_quotes'] > 0:
                print(f"  {row['name1']} ↔ {row['name2']}: {row['shared_quotes']} shared quotes")
                has_relationships = True
        
        if not has_relationships:
            print("❌ NO shared quotes found between any entity pairs")
            print("  This is why entity_relationships is empty!")
        
        return has_relationships
        
    except Exception as e:
        print(f"❌ Relationship query diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run comprehensive database diagnostic tests"""
    print("🚀 NETWORK RELATIONSHIP DATABASE DIAGNOSTIC")
    print("Testing database structure for entity network visualization")
    print("=" * 80)
    
    # Phase 1: Test database structure
    structure_ok = await test_database_structure()
    
    if not structure_ok:
        print("\n🚨 CRITICAL: Database structure issues found!")
        print("Fix database structure before proceeding with API fixes.")
        return False
    
    # Phase 2: Test basic API query
    basic_data, connected_names = await test_basic_api_query()
    
    if not basic_data:
        print("\n🚨 CRITICAL: Basic API query failed!")
        return False
    
    # Phase 3: Diagnose relationship query
    relationships_ok = await diagnose_relationship_query_issue(connected_names)
    
    print("\n" + "=" * 80)
    print("📋 DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    if structure_ok and basic_data and relationships_ok:
        print("✅ All database tests PASSED - API should work correctly")
        print("If API still fails, the issue is in the Python API code logic")
    else:
        print("❌ Database issues identified:")
        if not structure_ok:
            print("  - Database structure problems (entities/quotes/relationships)")
        if not basic_data:
            print("  - Basic query execution problems")
        if not relationships_ok:
            print("  - Relationship query execution problems")
    
    return structure_ok and basic_data and relationships_ok


if __name__ == "__main__":
    asyncio.run(main())