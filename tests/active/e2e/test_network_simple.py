#!/usr/bin/env python3
"""
Simple Neo4j relationship testing script - Windows compatible
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.qc.core.neo4j_manager import EnhancedNeo4jManager


async def main():
    """Run database diagnostic tests"""
    print("NETWORK RELATIONSHIP DATABASE DIAGNOSTIC")
    print("=" * 50)
    
    try:
        neo4j = EnhancedNeo4jManager()
        await neo4j.connect()
        print("Neo4j connection established")
        
        # Test 1: Check if AI entity exists
        print("\nTEST 1: AI Entity Check")
        entity_query = "MATCH (e:Entity {name: 'AI'}) RETURN count(e) as count"
        result = await neo4j.execute_cypher(entity_query)
        if result and result[0]['count'] > 0:
            print(f"PASS: AI entity found ({result[0]['count']} instances)")
        else:
            print("FAIL: AI entity not found")
            return
        
        # Test 2: Check quotes mentioning AI
        print("\nTEST 2: Quotes Mentioning AI")
        quote_query = "MATCH (q:Quote)-[:MENTIONS]->(e:Entity {name: 'AI'}) RETURN count(q) as quote_count"
        result = await neo4j.execute_cypher(quote_query)
        if result and result[0]['quote_count'] > 0:
            print(f"PASS: {result[0]['quote_count']} quotes mention AI")
        else:
            print("FAIL: No quotes mention AI - this is the root cause!")
            return
        
        # Test 3: Find connected entities
        print("\nTEST 3: Connected Entities")
        connected_query = """
        MATCH (ai:Entity {name: 'AI'})
        MATCH (q:Quote)-[:MENTIONS]->(ai)
        MATCH (q)-[:MENTIONS]->(other:Entity)
        WHERE other.name <> 'AI'
        RETURN other.name, count(q) as shared_quotes
        ORDER BY shared_quotes DESC
        LIMIT 10
        """
        result = await neo4j.execute_cypher(connected_query)
        if result and len(result) > 0:
            print(f"PASS: Found {len(result)} connected entities:")
            for row in result:
                print(f"  {row['other.name']}: {row['shared_quotes']} shared quotes")
        else:
            print("FAIL: No connected entities found")
            return
        
        # Test 4: Test relationship query
        print("\nTEST 4: Relationship Query Test")
        entity_names = ['AI'] + [row['other.name'] for row in result[:5]]
        print(f"Testing with entities: {entity_names}")
        
        rel_query = """
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
        
        result = await neo4j.execute_cypher(rel_query, {"entity_names": entity_names})
        if result and result[0]['relationships']:
            relationships = result[0]['relationships']
            print(f"PASS: Found {len(relationships)} relationships:")
            for rel in relationships[:5]:
                print(f"  {rel['source']} <-> {rel['target']}: weight {rel['weight']}")
        else:
            print("FAIL: No relationships found in final query")
        
        print("\n" + "=" * 50)
        print("DIAGNOSTIC COMPLETE")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())