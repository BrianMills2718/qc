#!/usr/bin/env python3
"""Test CLI Neo4j connection"""

import asyncio
import os
from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager

async def test_cli_connection():
    print("Testing CLI-style Neo4j connection...")
    
    # Clear environment variables like CLI does
    if 'NEO4J_USERNAME' in os.environ:
        del os.environ['NEO4J_USERNAME']
    if 'NEO4J_PASSWORD' in os.environ:
        del os.environ['NEO4J_PASSWORD']
    
    try:
        mgr = EnhancedNeo4jManager(username=None, password=None)
        print(f"Manager created: username={mgr.username}, password={mgr.password}")
        
        await mgr.connect()
        print("SUCCESS: Connected to Neo4j")
        
        # Test a simple query
        result = await mgr.execute_cypher("RETURN 1 as test")
        print(f"Query test: {result}")
        
        await mgr.close()
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cli_connection())