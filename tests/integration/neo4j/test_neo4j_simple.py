#!/usr/bin/env python3
"""Simple Neo4j connection test"""
import asyncio
from neo4j import AsyncGraphDatabase

async def test_connection():
    driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    
    try:
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            print(f"Connection successful: {record['test']}")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    finally:
        await driver.close()

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    print("SUCCESS" if success else "FAILED")