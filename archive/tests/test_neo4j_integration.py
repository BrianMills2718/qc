"""
Test Neo4j Integration
Tests that Neo4j operations work correctly in isolation
"""
import asyncio
import logging
import os
from datetime import datetime
import sys
sys.path.insert(0, 'src')

from src.qc.core.neo4j_manager import EnhancedNeo4jManager
from src.qc.extraction.code_first_schemas import (
    HierarchicalCode,
    CodeTaxonomy,
    DiscoveredSpeakerProperty,
    SpeakerPropertySchema,
    DiscoveredEntityType,
    DiscoveredRelationshipType,
    EntityRelationshipSchema
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_neo4j_connection():
    """Test basic Neo4j connection"""
    logger.info("=" * 60)
    logger.info("TEST 1: Neo4j Connection")
    logger.info("=" * 60)
    
    neo4j = EnhancedNeo4jManager()
    
    try:
        # Test connection
        await neo4j.connect()
        logger.info("✅ Successfully connected to Neo4j")
        
        # Run a simple query to verify connection
        query = "RETURN 'Connection test successful' as message"
        result = await neo4j.execute_cypher(query)
        
        if result and len(result) > 0:
            logger.info(f"   Query result: {result[0]['message']}")
            success = True
        else:
            logger.error("❌ Query returned no results")
            success = False
            
        await neo4j.close()
        logger.info("✅ Successfully closed connection")
        return success
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

async def test_create_nodes():
    """Test creating nodes in Neo4j"""
    logger.info("=" * 60)
    logger.info("TEST 2: Create Nodes")
    logger.info("=" * 60)
    
    neo4j = EnhancedNeo4jManager()
    
    try:
        await neo4j.connect()
        
        # Clear any existing test data
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        
        # Create test nodes
        test_nodes = [
            {"name": "TestCode1", "type": "Code", "level": 1},
            {"name": "TestCode2", "type": "Code", "level": 2},
            {"name": "TestSpeaker1", "type": "Speaker", "role": "Researcher"}
        ]
        
        for node_data in test_nodes:
            query = """
            CREATE (n:TestNode {name: $name, type: $type})
            SET n += $props
            RETURN n.name as name
            """
            props = {k: v for k, v in node_data.items() if k not in ["name", "type"]}
            result = await neo4j.execute_cypher(
                query,
                {"name": node_data["name"], "type": node_data["type"], "props": props}
            )
            logger.info(f"   Created node: {result[0]['name']}")
        
        # Verify nodes were created
        count_query = "MATCH (n:TestNode) RETURN count(n) as count"
        result = await neo4j.execute_cypher(count_query)
        count = result[0]['count']
        
        if count == len(test_nodes):
            logger.info(f"✅ Successfully created {count} nodes")
            success = True
        else:
            logger.error(f"❌ Expected {len(test_nodes)} nodes, found {count}")
            success = False
        
        # Cleanup
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        await neo4j.close()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to create nodes: {e}")
        return False

async def test_create_relationships():
    """Test creating relationships in Neo4j"""
    logger.info("=" * 60)
    logger.info("TEST 3: Create Relationships")
    logger.info("=" * 60)
    
    neo4j = EnhancedNeo4jManager()
    
    try:
        await neo4j.connect()
        
        # Clear any existing test data
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        
        # Create nodes first
        await neo4j.execute_cypher("""
            CREATE (c1:TestNode {name: 'ParentCode', type: 'Code'})
            CREATE (c2:TestNode {name: 'ChildCode', type: 'Code'})
            CREATE (s:TestNode {name: 'Speaker1', type: 'Speaker'})
            CREATE (q:TestNode {name: 'Quote1', type: 'Quote'})
        """)
        
        # Create relationships
        relationships = [
            ("ParentCode", "ChildCode", "HAS_CHILD"),
            ("Quote1", "ChildCode", "CODED_WITH"),
            ("Speaker1", "Quote1", "SAID")
        ]
        
        for source, target, rel_type in relationships:
            query = f"""
            MATCH (a:TestNode {{name: $source}})
            MATCH (b:TestNode {{name: $target}})
            CREATE (a)-[r:{rel_type}]->(b)
            RETURN type(r) as rel_type
            """
            result = await neo4j.execute_cypher(
                query,
                {"source": source, "target": target}
            )
            logger.info(f"   Created relationship: {source} -[{result[0]['rel_type']}]-> {target}")
        
        # Verify relationships
        count_query = """
        MATCH (:TestNode)-[r]->(:TestNode)
        RETURN count(r) as count
        """
        result = await neo4j.execute_cypher(count_query)
        count = result[0]['count']
        
        if count == len(relationships):
            logger.info(f"✅ Successfully created {count} relationships")
            success = True
        else:
            logger.error(f"❌ Expected {len(relationships)} relationships, found {count}")
            success = False
        
        # Cleanup
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        await neo4j.close()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to create relationships: {e}")
        return False

async def test_complex_query():
    """Test a complex query pattern"""
    logger.info("=" * 60)
    logger.info("TEST 4: Complex Query Pattern")
    logger.info("=" * 60)
    
    neo4j = EnhancedNeo4jManager()
    
    try:
        await neo4j.connect()
        
        # Clear and create test data
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        
        # Create a small knowledge graph
        await neo4j.execute_cypher("""
            // Create codes
            CREATE (c1:TestNode:Code {name: 'AI Impact', level: 1})
            CREATE (c2:TestNode:Code {name: 'Benefits', level: 2})
            CREATE (c3:TestNode:Code {name: 'Challenges', level: 2})
            
            // Create hierarchy
            CREATE (c1)-[:HAS_CHILD]->(c2)
            CREATE (c1)-[:HAS_CHILD]->(c3)
            
            // Create speakers
            CREATE (s1:TestNode:Speaker {name: 'Dr. Smith', role: 'Professor'})
            CREATE (s2:TestNode:Speaker {name: 'Jane Doe', role: 'Student'})
            
            // Create quotes
            CREATE (q1:TestNode:Quote {text: 'AI helps with analysis'})
            CREATE (q2:TestNode:Quote {text: 'Training is a challenge'})
            
            // Link quotes to speakers
            CREATE (s1)-[:SAID]->(q1)
            CREATE (s2)-[:SAID]->(q2)
            
            // Link quotes to codes
            CREATE (q1)-[:CODED_WITH]->(c2)
            CREATE (q2)-[:CODED_WITH]->(c3)
        """)
        
        # Run complex query - find all quotes linked to child codes of 'AI Impact'
        complex_query = """
        MATCH (parent:TestNode:Code {name: 'AI Impact'})
        MATCH (parent)-[:HAS_CHILD]->(child:Code)
        MATCH (quote:Quote)-[:CODED_WITH]->(child)
        MATCH (speaker:Speaker)-[:SAID]->(quote)
        RETURN 
            parent.name as parent_code,
            child.name as child_code,
            speaker.name as speaker,
            quote.text as quote_text
        ORDER BY child.name
        """
        
        results = await neo4j.execute_cypher(complex_query)
        
        if len(results) == 2:
            logger.info(f"✅ Complex query returned {len(results)} results:")
            for r in results:
                logger.info(f"   {r['speaker']} said '{r['quote_text']}' (coded as {r['child_code']})")
            success = True
        else:
            logger.error(f"❌ Expected 2 results, got {len(results)}")
            success = False
        
        # Cleanup
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        await neo4j.close()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Complex query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_batch_operations():
    """Test batch insert operations"""
    logger.info("=" * 60)
    logger.info("TEST 5: Batch Operations")
    logger.info("=" * 60)
    
    neo4j = EnhancedNeo4jManager()
    
    try:
        await neo4j.connect()
        
        # Clear test data
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        
        # Create batch data
        batch_size = 10
        codes = [{"name": f"Code_{i}", "level": i % 3 + 1} for i in range(batch_size)]
        
        # Batch insert
        batch_query = """
        UNWIND $batch as item
        CREATE (n:TestNode:Code {name: item.name, level: item.level})
        RETURN count(n) as created
        """
        
        result = await neo4j.execute_cypher(batch_query, {"batch": codes})
        created = sum(r['created'] for r in result)
        
        # Verify
        count_query = "MATCH (n:TestNode:Code) RETURN count(n) as count"
        result = await neo4j.execute_cypher(count_query)
        count = result[0]['count']
        
        if count == batch_size:
            logger.info(f"✅ Successfully batch inserted {count} nodes")
            success = True
        else:
            logger.error(f"❌ Expected {batch_size} nodes, found {count}")
            success = False
        
        # Cleanup
        await neo4j.execute_cypher("MATCH (n:TestNode) DETACH DELETE n")
        await neo4j.close()
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Batch operations failed: {e}")
        return False

async def main():
    """Run all Neo4j integration tests"""
    logger.info("Starting Neo4j Integration Tests")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    # Check if Neo4j is running
    logger.info("\nChecking Neo4j availability...")
    logger.info("Expected: Neo4j running on bolt://localhost:7687")
    logger.info("Username: neo4j, Password: password123")
    
    tests = [
        ("Neo4j Connection", test_neo4j_connection),
        ("Create Nodes", test_create_nodes),
        ("Create Relationships", test_create_relationships),
        ("Complex Query", test_complex_query),
        ("Batch Operations", test_batch_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL NEO4J TESTS PASSED!")
        return 0
    else:
        logger.error(f"⚠️ {total - passed} tests failed")
        logger.info("\nTroubleshooting:")
        logger.info("1. Ensure Neo4j is running: docker-compose up -d")
        logger.info("2. Check connection at: http://localhost:7474")
        logger.info("3. Verify credentials: neo4j/password123")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)