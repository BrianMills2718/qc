from neo4j import GraphDatabase
import sys

def test_neo4j_connection():
    """Test direct Neo4j connection independent of application"""
    try:
        # Test connection with various credential combinations
        credentials = [
            (None, None),           # No auth
            ('neo4j', 'neo4j'),     # Default
            ('neo4j', 'password'),  # Common default
        ]
        
        for username, password in credentials:
            try:
                if username and password:
                    driver = GraphDatabase.driver(
                        "bolt://localhost:7687",
                        auth=(username, password)
                    )
                else:
                    driver = GraphDatabase.driver("bolt://localhost:7687")
                
                with driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    value = result.single()["test"]
                    
                    print(f"SUCCESS: Neo4j connected with auth: {username}/{password}")
                    
                    # Test data availability
                    entities_query = "MATCH (e:Entity) RETURN count(e) as entity_count"
                    result = session.run(entities_query)
                    count = result.single()["entity_count"]
                    print(f"SUCCESS: Found {count} entities in database")
                
                driver.close()
                return True
                
            except Exception as auth_error:
                print(f"Failed with {username}/{password}: {auth_error}")
                continue
    except Exception as e:
        print(f"Neo4j connection completely failed: {e}")
        return False

if __name__ == "__main__":
    success = test_neo4j_connection()
    if not success:
        print("FAILURE: Cannot connect to Neo4j database")
        sys.exit(1)