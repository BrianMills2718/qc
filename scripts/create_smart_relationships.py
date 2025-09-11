#!/usr/bin/env python3
"""Create intelligent relationships based on actual entity content and properties"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment  
load_dotenv()

async def create_smart_relationships():
    """Create relationships based on actual entity content rather than assumed types"""
    print("SMART RELATIONSHIPS: Creating relationships from actual entity content")
    
    try:
        from qc_clean.core.data.neo4j_manager import EnhancedNeo4jManager, RelationshipEdge
        
        neo4j = EnhancedNeo4jManager(password='password123')
        await neo4j.connect()
        print("SUCCESS: Connected to Neo4j")
        
        # 1. Get all entities with correct property names
        print("\n=== ENTITY ANALYSIS ===")
        entities = await neo4j.execute_cypher("""
            MATCH (n:Entity)
            RETURN n.name as name, 
                   n.entity_type as entity_type,
                   n.description as description,
                   n.id as entity_id
        """)
        
        print(f"FOUND: {len(entities)} entities")
        
        # Group by entity type
        entities_by_type = {}
        for entity in entities:
            etype = entity.get('entity_type', 'Unknown')
            if etype not in entities_by_type:
                entities_by_type[etype] = []
            entities_by_type[etype].append(entity)
        
        print("ENTITY TYPES:")
        for etype, elist in entities_by_type.items():
            print(f"   {etype}: {len(elist)} entities")
            for e in elist[:3]:  # Show first 3
                print(f"      - {e['name']}")
        
        # 2. Create content-based relationships
        print(f"\n=== CREATING RELATIONSHIPS ===")
        created_relationships = 0
        
        # Strategy 1: Find entities mentioned in each other's descriptions
        for i, entity1 in enumerate(entities):
            name1 = entity1['name'].lower()
            desc1 = entity1.get('description', '').lower()
            
            for j, entity2 in enumerate(entities):
                if i >= j:  # Avoid duplicates and self-references
                    continue
                    
                name2 = entity2['name'].lower()
                desc2 = entity2.get('description', '').lower()
                
                # Check if entity names appear in each other's descriptions
                relationship_found = False
                rel_type = "MENTIONS"
                
                if name1 in desc2:
                    print(f"FOUND: {entity2['name']} mentions {entity1['name']}")
                    relationship_found = True
                elif name2 in desc1:
                    print(f"FOUND: {entity1['name']} mentions {entity2['name']}")
                    relationship_found = True
                
                # Check for specific relationship patterns
                if not relationship_found:
                    # Look for work/affiliation patterns
                    if ('director' in desc1 or 'works' in desc1) and name2 in desc1:
                        rel_type = "WORKS_AT"
                        relationship_found = True
                        print(f"WORK: {entity1['name']} works at {entity2['name']}")
                    elif ('director' in desc2 or 'works' in desc2) and name1 in desc2:
                        rel_type = "WORKS_AT"  
                        relationship_found = True
                        print(f"WORK: {entity2['name']} works at {entity1['name']}")
                
                if relationship_found:
                    try:
                        # Create relationship using the real Neo4j manager
                        edge = RelationshipEdge(
                            source_id=entity1['entity_id'],
                            target_id=entity2['entity_id'],
                            relationship_type=rel_type,
                            properties={
                                'created_by': 'smart_relationship_creator',
                                'confidence': 0.8,
                                'method': 'content_analysis'
                            }
                        )
                        
                        success = await neo4j.create_relationship(edge)
                        if success:
                            created_relationships += 1
                            print(f"   CREATED: {entity1['name']} --{rel_type}--> {entity2['name']}")
                        else:
                            print(f"   FAILED: Could not create relationship")
                            
                    except Exception as e:
                        print(f"   ERROR: Relationship creation failed: {e}")
        
        # 3. Verify relationships were created
        print(f"\n=== VERIFICATION ===")
        relationships = await neo4j.execute_cypher("""
            MATCH (a)-[r]->(b)
            RETURN a.name as from_name, 
                   type(r) as rel_type,
                   b.name as to_name,
                   r.confidence as confidence
        """)
        
        print(f"TOTAL RELATIONSHIPS: {len(relationships)}")
        for rel in relationships:
            confidence = rel.get('confidence', 'unknown')
            print(f"   {rel['from_name']} --{rel['rel_type']}--> {rel['to_name']} (confidence: {confidence})")
        
        await neo4j.close()
        
        if created_relationships > 0:
            print(f"\nSUCCESS: Created {created_relationships} smart relationships")
            return True
        else:
            print(f"\nNO RELATIONSHIPS: Could not create relationships from content")
            return False
        
    except Exception as e:
        print(f"ERROR: Smart relationship creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(create_smart_relationships())
    if result:
        print("\nCOMPLETE: Smart relationship creation successful")
        print("\nNEXT STEPS:")
        print("1. Query the relationships to verify they work")
        print("2. Test graph analysis patterns on real data")  
        print("3. Build advanced queries based on actual relationship types")
    else:
        print("\nFAILED: Smart relationship creation unsuccessful")