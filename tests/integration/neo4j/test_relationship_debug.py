#!/usr/bin/env python3
"""Debug relationship creation pipeline in isolation"""
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_relationship_pipeline():
    """Debug each step of relationship creation pipeline"""
    print("DEBUG: Debugging Relationship Creation Pipeline")
    
    try:
        # Step 1: Test Neo4j connection and existing entities
        from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager
        neo4j = EnhancedNeo4jManager()
        await neo4j.connect()
        
        # Get existing entities
        entities = await neo4j.get_all_nodes()
        print(f"SUCCESS: Found {len(entities)} entities in Neo4j")
        
        if len(entities) == 0:
            print("ERROR: No entities found - cannot test relationships")
            return False
        
        # Show some entities
        for i, entity in enumerate(entities[:5]):
            print(f"   Entity {i+1}: {entity.get('name', 'unnamed')} ({entity.get('label', 'no-label')})")
        
        # Step 2: Test relationship extraction using real entity data
        entity_names = [e.get('name', f'entity_{i}') for i, e in enumerate(entities[:5])]
        print(f"\nTEST: Testing relationship extraction with entities: {entity_names}")
        
        # Simple test text
        test_text = """
        John works at TechCorp and collaborates with Sarah on the AI project. 
        The development team uses agile methodologies for project management.
        Sarah oversees quality deliverables and manages the team.
        """
        
        # Step 3: Test LLM relationship extraction
        from qc_clean.core.llm.llm_handler import LLMHandler
        llm = LLMHandler()
        
        prompt = f"""
Analyze relationships between these entities from the interview text:
Entities: {entity_names}

Text: {test_text}

Identify relationships such as:
- WORKS_WITH, MANAGES, COLLABORATES_WITH (for people)
- BELONGS_TO, OPERATES_IN (for organizations/locations)
- INFLUENCES, CAUSES, RELATES_TO (for concepts)

Return JSON with relationships array containing: source, target, type, description
"""
        
        print("LLM: Calling LLM for relationship extraction...")
        llm_response = await llm.complete_raw(prompt, temperature=0.1)
        print(f"RESPONSE: LLM Response (first 500 chars): {llm_response[:500]}...")
        
        # Step 4: Test parsing
        def parse_relationship_response(response: str):
            """Parse LLM relationship extraction response"""
            try:
                import json
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                else:
                    json_str = response
                
                parsed = json.loads(json_str)
                return parsed.get('relationships', [])
            except Exception as e:
                logger.error(f"Relationship response parsing failed: {e}")
                return []
        
        relationships = parse_relationship_response(llm_response)
        print(f"PARSED: {len(relationships)} relationships:")
        for rel in relationships:
            print(f"   {rel.get('source')} --{rel.get('type')}--> {rel.get('target')}")
        
        if len(relationships) == 0:
            print("ERROR: No relationships parsed - this explains why 0 are stored!")
            print("DEBUG: Debug info:")
            print(f"   Raw response: {llm_response}")
            return False
        
        # Step 5: Test Neo4j relationship creation
        print(f"\nSTORE: Testing Neo4j relationship creation...")
        
        from qc_clean.core.data.neo4j_manager import RelationshipEdge
        
        for i, relationship in enumerate(relationships[:3]):  # Test first 3
            try:
                # Create RelationshipEdge
                edge = RelationshipEdge(
                    source_id=f"{relationship['source']}".replace(' ', '_'),
                    target_id=f"{relationship['target']}".replace(' ', '_'),
                    relationship_type=relationship['type'],
                    properties={
                        'description': relationship.get('description', ''),
                        'test_relationship': True
                    }
                )
                
                # Store in Neo4j
                success = await neo4j.create_relationship(edge)
                print(f"   Relationship {i+1}: {relationship['source']} --{relationship['type']}--> {relationship['target']} = {success}")
                
            except Exception as e:
                print(f"   Relationship {i+1} FAILED: {e}")
        
        # Step 6: Verify relationships were stored
        async with neo4j.driver.session() as session:
            result = await session.run("MATCH (a)-[r]->(b) RETURN count(r) as rel_count")
            record = await result.single()
            rel_count = record["rel_count"] if record else 0
            print(f"COUNT: Total relationships in database after test: {rel_count}")
            
            if rel_count > 0:
                # Show some relationships
                result = await session.run("""
                    MATCH (a)-[r]->(b) 
                    RETURN labels(a)[0] as from_type, a.name as from_name, 
                           type(r) as relationship, 
                           labels(b)[0] as to_type, b.name as to_name
                    LIMIT 5
                """)
                print("SAMPLE: Sample relationships:")
                async for record in result:
                    print(f"   {record['from_name']} ({record['from_type']}) --{record['relationship']}--> {record['to_name']} ({record['to_type']})")
        
        await neo4j.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Debug pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_relationship_pipeline())
    if result:
        print("\nSUCCESS: Relationship Pipeline Debug COMPLETED")
    else:
        print("\nFAILED: Relationship Pipeline Debug FAILED")