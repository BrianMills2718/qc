"""
Verify Neo4j data persistence after GT workflow
"""
import asyncio
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def verify_persistence():
    """Check if data persists in Neo4j"""
    
    # Initialize manager (same way as workflow does)
    manager = EnhancedNeo4jManager()
    
    # Check connection
    if not manager.driver:
        print("FAIL: Neo4j not connected")
        # Try to connect
        connected = await manager.connect()
        print(f"Connection attempt: {'SUCCESS' if connected else 'FAILED'}")
    
    # Query for codes
    codes_query = "MATCH (c:Code) RETURN count(c) as code_count"
    try:
        async with manager.driver.session() as session:
            result = await session.run(codes_query)
            codes_record = await result.single()
            print(f"Codes in database: {codes_record['code_count'] if codes_record else 0}")
    except Exception as e:
        print(f"Error querying codes: {e}")
    
    # Query for relationships
    rel_query = "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count"
    try:
        async with manager.driver.session() as session:
            result = await session.run(rel_query)
            relationships = await result.data()
            print(f"Relationships in database:")
            for rel in relationships:
                print(f"  - {rel['rel_type']}: {rel['count']}")
    except Exception as e:
        print(f"Error querying relationships: {e}")
    
    # Query for nodes by label
    node_query = "MATCH (n) WITH labels(n) as labels, count(n) as count RETURN labels, count"
    try:
        async with manager.driver.session() as session:
            result = await session.run(node_query)
            nodes = await result.data()
            print(f"Nodes in database:")
            for node in nodes:
                print(f"  - {node['labels']}: {node['count']}")
    except Exception as e:
        print(f"Error querying nodes: {e}")
    
    # Close connection
    await manager.close()

if __name__ == "__main__":
    asyncio.run(verify_persistence())