#!/usr/bin/env python3
"""
Test Entity Types: Direct database query vs API response
"""

import asyncio
import json
import requests
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_direct_db():
    """Test direct database query for entity types"""
    print("DIRECT DATABASE QUERY RESULTS")
    print("=" * 50)
    
    neo4j = EnhancedNeo4jManager()
    await neo4j.connect()
    
    # Simple query to get entities with their types
    query = """
    MATCH (e:Entity)
    RETURN e.name as name, e.entity_type as entity_type
    ORDER BY e.name
    LIMIT 20
    """
    
    result = await neo4j.execute_cypher(query)
    entities = [dict(record) for record in result]
    
    print(f"Found {len(entities)} entities (first 20):")
    entity_types = {}
    for entity in entities:
        name = entity['name']
        entity_type = entity['entity_type']
        print(f"  {name}: {entity_type}")
        
        if entity_type in entity_types:
            entity_types[entity_type] += 1
        else:
            entity_types[entity_type] = 1
    
    print()
    print("Entity type distribution from database:")
    for entity_type, count in sorted(entity_types.items()):
        print(f"  {entity_type}: {count}")
    
    await neo4j.close()

def test_api():
    """Test API response for entity types"""
    print("\nAPI RESPONSE RESULTS")
    print("=" * 50)
    
    try:
        response = requests.get('http://127.0.0.1:8000/api/entities')
        if response.status_code != 200:
            print(f"API request failed: {response.status_code}")
            return
        
        data = response.json()
        entities = data['entities'][:20]  # First 20
        
        print(f"Found {len(entities)} entities from API (first 20):")
        entity_types = {}
        for entity in entities:
            name = entity.get('name', 'MISSING')
            entity_type = entity.get('entity_type', 'MISSING')
            print(f"  {name}: {entity_type}")
            
            if entity_type in entity_types:
                entity_types[entity_type] += 1
            else:
                entity_types[entity_type] = 1
        
        print()
        print("Entity type distribution from API:")
        for entity_type, count in sorted(entity_types.items()):
            print(f"  {entity_type}: {count}")
            
    except Exception as e:
        print(f"API request failed: {e}")

async def main():
    await test_direct_db()
    test_api()

if __name__ == "__main__":
    asyncio.run(main())