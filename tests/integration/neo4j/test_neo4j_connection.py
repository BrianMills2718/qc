#!/usr/bin/env python3
"""
Test Neo4j Connection for Dashboard
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_neo4j_connection():
    try:
        from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager
        
        # Test current system connection
        print("Testing Neo4j connection with current system credentials...")
        neo4j_mgr = EnhancedNeo4jManager()
        
        # Test basic query
        result = await neo4j_mgr.execute_cypher('MATCH (n) RETURN count(n) as total')
        print(f'SUCCESS: Current system Neo4j connection - {result[0]["total"]} total nodes')
        
        await neo4j_mgr.close()
        return True
        
    except Exception as e:
        print(f'ERROR: Neo4j connection failed - {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_neo4j_connection())
    sys.exit(0 if success else 1)