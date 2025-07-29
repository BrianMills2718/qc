#!/usr/bin/env python3
"""
Quick test for Neo4j Docker connection
"""
import asyncio
import os
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

load_dotenv()

async def test_neo4j_docker():
    """Test Neo4j Docker connection and authentication"""
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password')
    
    print(f"Testing Neo4j connection...")
    print(f"URI: {uri}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    
    try:
        driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
        
        async with driver.session() as session:
            # Test basic query
            result = await session.run("RETURN 1 as num")
            record = await result.single()
            print(f"SUCCESS: Connection successful! Test query returned: {record['num']}")
            
            # Check version
            result = await session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            async for record in result:
                print(f"  - {record['name']}: {record['version']}")
        
        await driver.close()
        print("\nSUCCESS: Neo4j Docker is working correctly!")
        return True
        
    except Exception as e:
        print(f"\nConnection failed: {str(e)}")
        print("\nCommon Docker fixes:")
        print("1. Check if container is running: docker ps")
        print("2. Check container logs: docker logs <container-name>")
        print("3. Common Docker auth: NEO4J_AUTH=neo4j/your-password")
        print("4. If using default neo4j/neo4j, you may need to change password")
        return False

if __name__ == "__main__":
    asyncio.run(test_neo4j_docker())