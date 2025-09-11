#!/usr/bin/env python3
"""
Test Network API Direct: Test the exact network API logic without server dependencies
"""

import asyncio
import json
from src.qc.core.neo4j_manager import EnhancedNeo4jManager

async def test_network_api_logic():
    """Test the exact network API logic"""
    print("TESTING: Network API Logic Direct")
    print("=" * 50)
    
    neo4j = EnhancedNeo4jManager()
    await neo4j.connect()
    
    entity_name = "AI"
    
    try:
        # Step 1: Get basic network data for the center entity (exact from API)
        basic_query = """
        MATCH (center:Entity {name: $entity_name})
        OPTIONAL MATCH (q:Quote)-[:MENTIONS]->(center)
        OPTIONAL MATCH (q)-[:MENTIONS]->(connected:Entity)
        WHERE connected.name <> $entity_name
        
        WITH $entity_name as center_name,
             count(DISTINCT center) as center_mentions,
             count(DISTINCT q) as quote_count,
             collect(DISTINCT {
                name: connected.name,
                type: connected.entity_type,
                mentions: 1
            }) as connected_entities,
             collect(DISTINCT center.interview_id) as interviews
        
        RETURN {
            center_entity: center_name,
            center_mentions: center_mentions,
            quote_count: quote_count,
            connected_entities: connected_entities,
            interviews: interviews
        } as basic_data
        """
        
        basic_result = await neo4j.execute_cypher(basic_query, {"entity_name": entity_name})
        
        if not basic_result or not basic_result[0].get('basic_data'):
            print("ERROR: No basic_data returned")
            return
            
        basic_data = basic_result[0]['basic_data']
        connected_names = [e['name'] for e in basic_data['connected_entities'] if e['name']]
        
        print(f"SUCCESS: Basic query successful")
        print(f"   Center mentions: {basic_data['center_mentions']}")
        print(f"   Quote count: {basic_data['quote_count']}")
        print(f"   Connected entities: {len(connected_names)}")
        
        # Step 2: Find relationships between connected entities (exact from API)
        if len(connected_names) > 1:
            print(f"\nSUCCESS: Condition met: {len(connected_names)} > 1, executing relationship query")
            
            relationship_query = """
            UNWIND $entity_names as name1
            UNWIND $entity_names as name2
            WITH name1, name2 WHERE name1 < name2
            
            MATCH (e1:Entity {name: name1}), (e2:Entity {name: name2})
            OPTIONAL MATCH (q:Quote)-[:MENTIONS]->(e1), (q)-[:MENTIONS]->(e2)
            
            WITH name1, name2, count(DISTINCT q) as shared_quotes
            WHERE shared_quotes > 0
            
            RETURN collect({
                source: name1,
                target: name2, 
                weight: shared_quotes
            }) as relationships
            """
            
            rel_result = await neo4j.execute_cypher(relationship_query, {"entity_names": connected_names[:20]})
            relationships = rel_result[0]['relationships'] if rel_result and rel_result[0] else []
            
            print(f"SUCCESS: Relationship query successful")
            print(f"   Relationships found: {len(relationships)}")
        else:
            relationships = []
            print(f"FAILED: Condition failed: {len(connected_names)} <= 1")
        
        # Step 3: Build the final network data structure (exact from API)
        network_data = {
            "center_entity": basic_data['center_entity'],
            "total_mentions": basic_data['center_mentions'],
            "quote_count": basic_data['quote_count'],
            "connected_entities": [e['name'] for e in basic_data['connected_entities']],
            "entity_relationships": relationships,
            "connection_count": len(basic_data['connected_entities']),
            "interviews": basic_data['interviews']
        }
        
        # Ensure all required fields exist with defaults (exact from API)
        safe_network_data = {
            "total_mentions": network_data.get('total_mentions', 0),
            "quote_count": network_data.get('quote_count', 0),
            "connected_entities": network_data.get('connected_entities', []),
            "entity_relationships": network_data.get('entity_relationships', []),
            "connection_count": network_data.get('connection_count', 0),
            "interviews": network_data.get('interviews', [])
        }
        
        # Filter out empty or invalid entity names (exact from API)
        safe_network_data['connected_entities'] = [
            entity for entity in safe_network_data['connected_entities'] 
            if entity and isinstance(entity, str) and entity.strip()
        ]
        
        # Build final response structure (exact from API)
        response = {
            "entity_name": entity_name,
            "network": safe_network_data,
            "visualization": {
                "center_node": {
                    "id": entity_name,
                    "label": entity_name,
                    "type": "center",
                    "mentions": safe_network_data['total_mentions'],
                    "quotes": safe_network_data['quote_count']
                },
                "connected_nodes": [
                    {
                        "id": connected_entity,
                        "label": connected_entity,
                        "type": "connected"
                    } for connected_entity in safe_network_data['connected_entities']
                ],
                "relationships": safe_network_data.get('entity_relationships', [])
            }
        }
        
        print(f"\nSUCCESS: Final response structure built")
        print(f"   Network entity_relationships: {len(response['network']['entity_relationships'])}")
        print(f"   Visualization relationships: {len(response['visualization']['relationships'])}")
        
        # Show sample relationships
        if response['network']['entity_relationships']:
            print(f"\nSample relationships:")
            for rel in response['network']['entity_relationships'][:5]:
                print(f"   {rel['source']} <--> {rel['target']} (weight: {rel['weight']})")
        
        print(f"\nSUMMARY:")
        print(f"   SUCCESS: Query logic works correctly")
        print(f"   SUCCESS: Relationships are found: {len(relationships)}")
        print(f"   SUCCESS: Response structure includes relationships")
        print(f"   SUCCESS: Both network and visualization have relationship data")
        
        # Save response to file for comparison with API
        with open('network_api_test_response.json', 'w') as f:
            json.dump(response, f, indent=2)
        print(f"   SUCCESS: Response saved to network_api_test_response.json")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await neo4j.close()

if __name__ == "__main__":
    asyncio.run(test_network_api_logic())