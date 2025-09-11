#!/usr/bin/env python3
"""Check actual Neo4j database content"""

import asyncio
import sys
import os
sys.path.append('src')

from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager

async def check_neo4j_data():
    # Use same config as CLI
    mgr = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j", 
        password="devpassword"
    )
    await mgr.connect()
    
    # Check counts of different node types
    entities = await mgr.execute_cypher('MATCH (e:Entity) RETURN count(e) as count')
    codes = await mgr.execute_cypher('MATCH (c:Code) RETURN count(c) as count') 
    quotes = await mgr.execute_cypher('MATCH (q:Quote) RETURN count(q) as count')
    rels = await mgr.execute_cypher('MATCH ()-[r]->() RETURN count(r) as count')
    
    print(f"Neo4j Database Content:")
    print(f"  Entities: {entities[0]['count']}")
    print(f"  Codes: {codes[0]['count']}")
    print(f"  Quotes: {quotes[0]['count']}")
    print(f"  Relationships: {rels[0]['count']}")
    
    # Check if there are recent entities (from recent CLI runs)
    recent_entities = await mgr.execute_cypher('MATCH (e:Entity) RETURN e.name LIMIT 5')
    print(f"\nSample entities:")
    for entity in recent_entities:
        print(f"  - {entity['e.name']}")
    
    await mgr.close()

if __name__ == "__main__":
    asyncio.run(check_neo4j_data())