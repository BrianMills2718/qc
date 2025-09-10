"""Test Neo4j connection"""
import asyncio
import sys
sys.path.insert(0, 'src')

from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_connection():
    neo4j = EnhancedNeo4jManager(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="devpassword"
    )
    
    try:
        await neo4j.connect()
        print("SUCCESS: Connected to Neo4j!")
        
        # Test a simple query
        async with neo4j.driver.session() as session:
            result = await session.run("RETURN 'Hello Neo4j!' as message")
            record = await result.single()
            print(f"SUCCESS: Test query result: {record['message']}")
            
        await neo4j.close()
        return True
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")
        await neo4j.close()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)