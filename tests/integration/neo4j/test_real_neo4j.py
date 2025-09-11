#!/usr/bin/env python3
"""Test real Neo4j connection with different authentication approaches"""

import asyncio
from neo4j import AsyncGraphDatabase

async def test_neo4j_auth_methods():
    uri = "bolt://localhost:7687"
    
    print("Testing Neo4j authentication methods...")
    
    # Method 1: No authentication at all
    print("\n=== Test 1: No authentication ===")
    try:
        driver = AsyncGraphDatabase.driver(uri)
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            print(f"SUCCESS (no auth): {record['test']}")
        await driver.close()
    except Exception as e:
        print(f"FAILED (no auth): {e}")
    
    # Method 2: Default neo4j credentials
    print("\n=== Test 2: Default neo4j/neo4j ===")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=("neo4j", "neo4j"))
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            print(f"SUCCESS (neo4j/neo4j): {record['test']}")
        await driver.close()
    except Exception as e:
        print(f"FAILED (neo4j/neo4j): {e}")
    
    # Method 3: neo4j/devpassword
    print("\n=== Test 3: neo4j/devpassword ===")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=("neo4j", "devpassword"))
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            print(f"SUCCESS (neo4j/devpassword): {record['test']}")
        await driver.close()
    except Exception as e:
        print(f"FAILED (neo4j/devpassword): {e}")
    
    # Method 4: Empty string auth
    print("\n=== Test 4: Empty string auth ===")
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=("", ""))
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            print(f"SUCCESS (empty auth): {record['test']}")
        await driver.close()
    except Exception as e:
        print(f"FAILED (empty auth): {e}")

if __name__ == "__main__":
    asyncio.run(test_neo4j_auth_methods())