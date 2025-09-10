#!/usr/bin/env python3
"""Test Neo4j connectivity"""

import asyncio
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_connection():
    """Test Neo4j connection"""
    mgr = EnhancedNeo4jManager(username=None, password=None)  # No auth
    try:
        await mgr.connect()
        print("Neo4j connected successfully")
        await mgr.close()
        return True
    except Exception as e:
        print(f"Neo4j connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())