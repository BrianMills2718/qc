#!/usr/bin/env python3
"""Fix Neo4j connection issues by testing different authentication methods"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def test_neo4j_connection():
    """Test various Neo4j connection methods to find working auth"""
    print("TESTING: Neo4j connection methods")
    
    # Try with environment password first
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    print(f"ENV PASSWORD: Using password from environment: {neo4j_password}")
    
    # Check docker container password
    try:
        import subprocess
        result = subprocess.run(['docker', 'inspect', '-f', '{{range .Config.Env}}{{println .}}{{end}}', 'qualitative-coding-neo4j'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("DOCKER ENV:")
            for line in result.stdout.strip().split('\n'):
                if 'NEO4J_AUTH' in line:
                    print(f"   {line}")
                    if '=' in line:
                        auth_value = line.split('=', 1)[1]
                        if '/' in auth_value:
                            username, password = auth_value.split('/', 1)
                            print(f"   Detected: username={username}, password={password}")
                            neo4j_password = password
        else:
            print("DOCKER INSPECT FAILED:", result.stderr)
    except Exception as e:
        print(f"DOCKER CHECK FAILED: {e}")
    
    # Now test connection
    try:
        from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager
        
        # Try with detected password
        print(f"CONNECTING: Testing with password: {neo4j_password}")
        neo4j = EnhancedNeo4jManager(password=neo4j_password)
        await neo4j.connect()
        print("SUCCESS: Neo4j connection established")
        
        # Test basic query
        nodes = await neo4j.execute_cypher("MATCH (n) RETURN n, labels(n) as labels")
        print(f"QUERY SUCCESS: Found {len(nodes)} existing nodes")
        
        # Show some node types
        node_types = {}
        for result in nodes:
            labels = result.get('labels', [])
            if labels:
                node_type = labels[0]  # Use first label
            else:
                node_type = 'Unknown'
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        print("NODE TYPES:")
        for node_type, count in node_types.items():
            print(f"   {node_type}: {count}")
        
        # Test relationship count
        async with neo4j.driver.session() as session:
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            record = await result.single()
            rel_count = record["rel_count"] if record else 0
            print(f"RELATIONSHIPS: {rel_count} relationships in database")
        
        await neo4j.close()
        return True
        
    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_neo4j_connection())
    if result:
        print("\nSUCCESS: Neo4j connection working")
    else:
        print("\nFAILED: Neo4j connection failed")